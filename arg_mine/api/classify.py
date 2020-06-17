from dataclasses import dataclass
from typing import List, Tuple, Any
import logging
import requests
import math
import time

from arg_mine.api import DEFAULT_TIMEOUT, CLASSIFY_BASE_URL, load_auth_tokens
from arg_mine.api import errors
from arg_mine.utils import enum, unique_hash

logger = logging.getLogger(__name__)

# TODO(MJP): this enum pattern is horrible. Find a better one.

# enum for the topic relevance matching options, via "topicRelevance" in API
TOPIC_RELEVANCE = enum(
    MATCH_STRING='match_string',
    N_GRAM_OVERLAP='n_gram_overlap',
    WORD2VEC='word2vec'
)

# enum for possible argument labels
ARGUMENT_LABEL = enum(
    ARGUMENT='argument',
    NO_ARGUMENT='no argument'
)

# enum for possible stance labels
STANCE_LABEL = enum(
    PRO='pro',
    CON='contra',
    NA=''
)


@dataclass
class ClassifyMetadata:
    """
    data class to hold the return values from a classify API call
    """
    doc_id: str  # unique hash associated with the source document / content
    url: str
    topic: str
    model_version: str
    language: str
    time_argument_prediction: float
    time_attention_computation: float
    time_preprocessing: float
    time_stance_prediction: float
    time_logging: float
    time_total: float
    total_arguments: int
    total_contra_arguments: int
    total_pro_arguments: int
    total_non_arguments: int
    total_classified_sentences: int
    # params: dict   # to add later, holding the classify parameters used in the query

    @classmethod
    def from_dict(cls, metadata_dict):
        """Load data object from a dict"""
        url = metadata_dict["userMetadata"]  # should be enforcing upstream that the metadata will be the URL
        return ClassifyMetadata(
            # make the document ID based on the url
            doc_id=cls.make_doc_id(url),
            url=url,
            topic=metadata_dict['topic'],
            model_version=metadata_dict['modelVersion'],
            language=metadata_dict['language'],
            time_argument_prediction=metadata_dict['timeArgumentPrediction'],
            time_attention_computation=metadata_dict['timeAttentionComputation'],
            time_preprocessing=metadata_dict['timePreprocessing'],
            time_stance_prediction=metadata_dict['timeStancePrediction'],
            time_logging=metadata_dict['timeLogging'],
            time_total=metadata_dict['timeTotal'],
            total_arguments=metadata_dict['totalArguments'],
            total_contra_arguments=metadata_dict['totalContraArguments'],
            total_pro_arguments=metadata_dict['totalProArguments'],
            total_non_arguments=metadata_dict['totalNonArguments'],
            total_classified_sentences=metadata_dict['totalClassifiedSentences'],
        )

    @staticmethod
    def make_doc_id(input_str):
        """Return a unique hash for the given input string; used as the document id"""
        return unique_hash(input_str)


@dataclass
class ClassifiedSentence:
    """
    data class to hold the return values from a classify API call
    The kwargs in this class are optional, and are not required when parsing from a dict
    """
    url: str
    doc_id: str
    topic: str
    sentence_id: str
    argument_confidence: float
    argument_label: str
    sentence_original: str
    sentence_preprocessed: str
    sort_confidence: float
    stance_confidence: float = 0.0
    stance_label: str = STANCE_LABEL.NA

    @classmethod
    def from_dict(cls, url, topic, sentence_dict):
        """Load data object from dict"""
        return ClassifiedSentence(
            url=url,
            doc_id=ClassifyMetadata.make_doc_id(url),
            topic=topic,
            sentence_id=cls.make_sentence_id(sentence_dict['sentencePreprocessed']),
            argument_confidence=sentence_dict['argumentConfidence'],
            argument_label=sentence_dict['argumentLabel'],
            sentence_original=sentence_dict['sentenceOriginal'],
            sentence_preprocessed=sentence_dict['sentencePreprocessed'],
            sort_confidence=sentence_dict['sortConfidence'],
            stance_confidence=sentence_dict.get('stanceConfidence', 0.0),
            stance_label=sentence_dict.get('stanceLabel', STANCE_LABEL.NA),
        )

    @property
    def is_argument(self):
        return self.argument_label == ARGUMENT_LABEL.ARGUMENT

    @staticmethod
    def make_sentence_id(input_str):
        """Return a unique hash for the given input string; used as the sentence id"""
        _id = unique_hash(input_str)
        return _id

# ==============================================================================
# methods


def classify_url_sentences(
        topic: str,
        url: str,
        user_id: str,
        api_key: str,
        only_arguments: bool = True,
        topic_relevance: str = TOPIC_RELEVANCE.WORD2VEC,
        timeout: float = DEFAULT_TIMEOUT,
):
    """
    For a given URL and topic phrase, identify which sentences contain arguments
    vs non-arguments

    It encodes the url and topic used for the query in the returned metadata object

    Parameters
    ----------
    topic : str
        string of keywords used to query if sentence states argument on topic
    url : str
        source of the content, webpage URL works well
    user_id : str
    api_key : str
    only_arguments : bool
        only return the sentences of the estimated arguments
        TODO: check to see if setting this true decreases the computation time on the server
    topic_relevance : str
        use options from TOPIC_RELEVANCE enum
    timeout : float

    Returns
    -------
    dict
    """
    payload = {
        "topic": topic,
        "userID": user_id,
        "apiKey": api_key,
        "targetUrl": url,
        "model": "default",
        "topicRelevance": topic_relevance,
        "predictStance": True,  # we don't want to predict stance without context
        "computeAttention": False,  # doesnt work for BERT-based models (the default model)
        "showOnlyArguments": only_arguments,  # only return sentences classified as arguments
        "userMetadata": url,
    }

    try:
        # do the requests call
        # TODO: add sessions to this:
        # inject a session or the requests object, confirm that injected object has a `post` method
        response = requests.post(
            CLASSIFY_BASE_URL,
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()

    except (requests.ConnectionError, requests.Timeout) as e:
        raise errors.Unavailable("Server not responding") from e
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            error = e.response.json()
            message = error['error']
            if errors.Refused.TARGET_MSG in message:
                raise errors.Refused(message)
            raise errors.ArgumenTextGatewayError(message) from e

        msg = "ArgumentText service had internal error."
        logger.exception(msg)
        raise errors.Unavailable(msg) from e
    return response.json()


def collect_sentences_by_topic(topic, url_list, pause_every=None, sleep_dur=5, max_attempts=3):
    """
    Iterate over a list of URLs for a given topic, return whether or not the token/sentence is an argument or not

    Parameters
    ----------
    topic : str
    url_list : List[AnyStr]
    pause_every : int
        pause this many iterations
        throttling to not DDOS the API server
    sleep_dur : float
        number of second to pause when pause_every is hit
    max_attempts : int
        maximum number of retries per url


    Returns
    -------
    Tuple[List[ClassifyMetadata]], List[ClassifiedSentence], List[Any]]
    """
    pause_every = pause_every or len(url_list)
    user_id, api_key = load_auth_tokens()
    doc_list = []
    refused_doc_list = []
    sentence_list = []
    for url_index, url in enumerate(url_list):
        attempts = 0
        if url_index and url_index % pause_every == 0:
            logger.debug("sleeping for {} sec".format(sleep_dur))
            time.sleep(sleep_dur)

        out_dict = None
        while attempts < max_attempts:
            try:
                attempts += 1
                logger.debug("Attempting url {}, try #{}".format(url_index, attempts))
                out_dict = classify_url_sentences(topic, url, user_id, api_key)
                break  # exit out if we didnt error on anything
            except errors.Refused as e:
                logger.warning("Refused: {}, url={}".format(e, url))
                refused_doc_list.append(url)
                break
            except (errors.Unavailable, errors.ArgumenTextGatewayError) as e:
                logger.error(e)
            if attempts == max_attempts:
                logger.error("Failing attempts")
        if not out_dict:
            logger.info("Skipping {}: {}".format(url_index, url))
            continue
        doc_list.append(ClassifyMetadata.from_dict(out_dict['metadata']))
        for sentence in out_dict['sentences']:
            sentence_list.append(ClassifiedSentence.from_dict(url, topic, sentence))

    return doc_list, sentence_list, refused_doc_list