from dataclasses import dataclass
from typing import List, AnyStr
import logging
import time
import multiprocessing
from functools import partial

from arg_mine.api.auth import load_auth_tokens
from arg_mine.api import session, errors
from arg_mine import utils

_logger = utils.get_logger(__name__, logging.DEBUG)


class TopicRelevance:
    """enum for the topic relevance matching options, via "topicRelevance" in API"""

    MATCH_STRING = "match_string"
    N_GRAM_OVERLAP = "n_gram_overlap"
    WORD2VEC = "word2vec"


class ArgumentLabel:
    """enum for possible argument labels"""

    ARGUMENT = "argument"
    NO_ARGUMENT = "no argument"


class StanceLabel:
    """enum for possible stance labels"""

    PRO = "pro"
    CON = "contra"
    NA = ""


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
        url = metadata_dict[
            "userMetadata"
        ]  # should be enforcing upstream that the metadata will be the URL
        return ClassifyMetadata(
            # make the document ID based on the url
            doc_id=cls.make_doc_id(url),
            url=url,
            topic=metadata_dict["topic"],
            model_version=metadata_dict["modelVersion"],
            language=metadata_dict["language"],
            time_argument_prediction=metadata_dict["timeArgumentPrediction"],
            time_attention_computation=metadata_dict["timeAttentionComputation"],
            time_preprocessing=metadata_dict["timePreprocessing"],
            time_stance_prediction=metadata_dict["timeStancePrediction"],
            time_logging=metadata_dict["timeLogging"],
            time_total=metadata_dict["timeTotal"],
            total_arguments=metadata_dict["totalArguments"],
            total_contra_arguments=metadata_dict["totalContraArguments"],
            total_pro_arguments=metadata_dict["totalProArguments"],
            total_non_arguments=metadata_dict["totalNonArguments"],
            total_classified_sentences=metadata_dict["totalClassifiedSentences"],
        )

    @staticmethod
    def make_doc_id(input_str):
        """Return a unique hash for the given input string; used as the document id"""
        return utils.unique_hash(input_str)


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
    stance_label: str = StanceLabel.NA

    @classmethod
    def from_dict(cls, url, topic, sentence_dict):
        """Load data object from dict"""
        return ClassifiedSentence(
            url=url,
            doc_id=ClassifyMetadata.make_doc_id(url),
            topic=topic,
            sentence_id=cls.make_sentence_id(sentence_dict["sentencePreprocessed"]),
            argument_confidence=sentence_dict["argumentConfidence"],
            argument_label=sentence_dict["argumentLabel"],
            sentence_original=sentence_dict["sentenceOriginal"],
            sentence_preprocessed=sentence_dict["sentencePreprocessed"],
            sort_confidence=sentence_dict["sortConfidence"],
            stance_confidence=sentence_dict.get("stanceConfidence", 0.0),
            stance_label=sentence_dict.get("stanceLabel", StanceLabel.NA),
        )

    @property
    def is_argument(self):
        return self.argument_label == ArgumentLabel.ARGUMENT

    @staticmethod
    def make_sentence_id(input_str):
        """Return a unique hash for the given input string; used as the sentence id"""
        _id = utils.unique_hash(input_str)
        return _id


# ==============================================================================
# methods


def classify_url_sentences(
    topic: str,
    url: str,
    user_id: str,
    api_key: str,
    only_arguments: bool = True,
    topic_relevance: str = TopicRelevance.WORD2VEC,
    timeout: float = session.DEFAULT_TIMEOUT,
    request_session=None,
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
        use options from TopicRelevance enum
    timeout : float
    request_session : requests.Session
        session to pass in, for large iterations

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
    request_session = request_session or session.get_session()
    json_response = session.fetch(
        session.ApiUrl.CLASSIFY_BASE_URL,
        payload,
        timeout,
        request_session=request_session,
    )
    return json_response


def collect_sentences_by_topic(
    topic: str, url_list: List[AnyStr],
):
    """
    Iterate over a list of URLs for a given topic, return whether or not the token/sentence is an argument or not

    Parameters
    ----------
    topic : str
    url_list : List[AnyStr]

    Returns
    -------
    Tuple[List[ClassifyMetadata],  List[ClassifiedSentence], List[str]]
    """
    user_id, api_key = load_auth_tokens()

    doc_list = []
    refused_doc_list = []
    sentence_list = []
    for url_index, url in enumerate(url_list):
        out_dict = None
        try:
            _logger.debug(
                "Attempting url {} of {}".format(url_index + 1, len(url_list))
            )
            out_dict = classify_url_sentences(topic, url, user_id, api_key)
        except errors.Refused as e:
            _logger.warning("Refused: {}, url={}".format(e, url))
            refused_doc_list.append(url)
        except (errors.Unavailable, errors.ArgumenTextGatewayError) as e:
            _logger.error(e)

        if out_dict:
            doc_list.append(ClassifyMetadata.from_dict(out_dict["metadata"]))
            for sentence in out_dict["sentences"]:
                sentence_list.append(ClassifiedSentence.from_dict(url, topic, sentence))

    return doc_list, sentence_list, refused_doc_list


def collect_sentences_for_url(topic, url, user_id, api_key):
    doc_list = []
    refused_doc_list = []
    sentence_list = []
    out_dict = None
    try:
        out_dict = classify_url_sentences(topic, url, user_id, api_key)
    except errors.Refused as e:
        _logger.warning("Refused: {}, url={}".format(e, url))
        refused_doc_list.append(url)
    except (errors.Unavailable, errors.ArgumenTextGatewayError) as e:
        _logger.error(e)

    if out_dict:
        doc_list.append(ClassifyMetadata.from_dict(out_dict["metadata"]))
        for sentence in out_dict["sentences"]:
            sentence_list.append(ClassifiedSentence.from_dict(url, topic, sentence))
    return doc_list, sentence_list, refused_doc_list


def collect_sentences_by_topic_parallel(
    topic: str, url_list: List[AnyStr], proc_count: int = 4,
):
    """
    Iterate over a list of URLs for a given topic, return whether or not the token/sentence is an argument or not

    Parameters
    ----------
    topic : str
    url_list : List[AnyStr]
    proc_count : int
        number of processes that we want to use for this extraction

    Returns
    -------
    Tuple[List[ClassifyMetadata],  List[ClassifiedSentence], List[str]]
    """

    # TODO: look into using `grequests` for requests parallelization
    user_id, api_key = load_auth_tokens()

    wrapper = partial(collect_sentences_for_url, topic, user_id, api_key)

    with multiprocessing.Pool(processes=proc_count) as pool:
        results = pool.map(wrapper, url_list)

    return results
