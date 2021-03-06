from dataclasses import dataclass
from typing import List, AnyStr, Iterable  # noqa: F401
import logging
import time

import requests
import grequests  # really should have used requests-futures :/=
import pandas as pd
import json

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
class DocumentMetadata:
    """
    data class for the document metadata from a given URL, via a classify API call
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
        return DocumentMetadata(
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

    doc_id: str
    url: str
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
            doc_id=DocumentMetadata.make_doc_id(url),
            url=url,
            topic=topic,
            sentence_id=cls.make_sentence_id(sentence_dict["sentencePreprocessed"]),
            argument_confidence=sentence_dict["argumentConfidence"],
            argument_label=sentence_dict["argumentLabel"],
            sentence_original=sentence_dict["sentenceOriginal"],
            sentence_preprocessed=sentence_dict["sentencePreprocessed"],
            sort_confidence=sentence_dict.get("sortConfidence", None),
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


def bundle_payload(
    topic,
    url,
    only_arguments: bool = False,
    topic_relevance: str = TopicRelevance.WORD2VEC,
):
    """
    Bundle the target json payload with API parameters

    Note that this call collects the authentication tokens for each time
    this method is called.

    Parameters
    ----------
    topic: str
        keywords used in topic_relevance search
    url : str
        full URL to a target web document
    only_arguments : bool
        If True, only return sentences that contain arguments. This option
        can be enabled to save storage space
    topic_relevance : TopicRelevance
        enum/str for which topic relevance model to use. See TopicRelevance.

    Returns
    -------
    dict
        json-able dict to be used in the http request
    """
    user_id, api_key = load_auth_tokens()
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
        "sortBy": "none",
        "userMetadata": url,
    }
    return payload


def classify_url_sentences(
    topic: str,
    url: str,
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
    payload = bundle_payload(
        topic, url, only_arguments=only_arguments, topic_relevance=topic_relevance
    )
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
    Serially iterate over a list of URLs for a given topic
    return whether or not the token/sentence is an argument or not

    Parameters
    ----------
    topic : str
        keywords to use for topic identification in ArgText
    url_list : List[AnyStr]
        list of URLs containing documents to argument mine

    Returns
    -------
    Tuple[List[DocumentMetadata],  List[ClassifiedSentence], List[str]]
    """
    user_id, api_key = load_auth_tokens()

    doc_list = []
    refused_doc_list = []
    sentence_list = []
    with session.get_session() as req_session:
        for url_index, url in enumerate(url_list):
            out_dict = None
            try:
                _logger.debug(
                    "Attempting url {} of {}".format(url_index + 1, len(url_list))
                )
                out_dict = classify_url_sentences(
                    topic, url, user_id, api_key, request_session=req_session
                )
            except errors.Refused as e:
                _logger.warning("Refused: {}, url={}".format(e, url))
                refused_doc_list.append(url)
            except (errors.Unavailable, errors.ArgumenTextGatewayError) as e:
                _logger.error(e)

            if out_dict:
                doc_list.append(DocumentMetadata.from_dict(out_dict["metadata"]))
                for sentence in out_dict["sentences"]:
                    sentence_list.append(
                        ClassifiedSentence.from_dict(url, topic, sentence)
                    )

    return doc_list, sentence_list, refused_doc_list


def collect_sentences_for_url(topic, url, user_id, api_key):
    """
    Thin wrapper function for getting the DocumentMetadata and ClassifiedSentence objects for a url

    Parameters
    ----------
    topic : str
    url : str
    user_id : str
    api_key : str

    Returns
    -------
    Tuple[List[DocumentMetadata],  List[ClassifiedSentence], List[str]]
    """
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
        doc_list.append(DocumentMetadata.from_dict(out_dict["metadata"]))
        for sentence in out_dict["sentences"]:
            sentence_list.append(ClassifiedSentence.from_dict(url, topic, sentence))
    return doc_list, sentence_list, refused_doc_list


def _response_error_check(response):
    """
    Trigger any Exceptions that happened during a document URL request
    Convert raised exceptions to internal exception types for consistency

    Parameters
    ----------
    response : requests.Response

    Returns
    -------
    none

    Raises
    ------
    errors.Unavailable
        when requests returns an unknown HTTPError
    errors.Refused
        when server returns a 400 and "Website could not be crawled"
    errors.ArgumenTextGatewayError
        when server returns a 400 and unspecified message
    errors.NotResponding
        when connection fails or times out

    """
    try:
        response.raise_for_status()
    except (requests.ConnectionError, requests.Timeout) as e:
        raise errors.NotResponding(
            "Server not responding, ConnectionError or Timeout"
        ) from e
    except requests.HTTPError as e:
        status_code = e.response.status_code
        if e.response.status_code == 400:
            error = e.response.json()
            message = error["error"]
            if errors.Refused.TARGET_MSG in message:
                # for now, dont want to display every time we get a missing article
                # _logger.debug("{} : {}".format(status_code, error))
                raise errors.Refused(status_code, message)
            _logger.error("{} : {}".format(status_code, error))
            raise errors.ArgumenTextGatewayError(status_code, message) from e
        elif status_code == 500:
            msg = (
                "Server Error: INTERNAL SERVER ERROR for url: {}".format(
                    session.ApiUrl.CLASSIFY_BASE_URL
                )
                + ", check payload contents?"
            )
            _logger.error("{} : {}".format(status_code, msg))
            raise errors.InternalGatewayError(status_code, msg)

        msg = "ArgumentText service had internal error."
        _logger.exception(msg)
        raise errors.ArgumenTextGatewayError(e.response.status_code, msg) from e


def _exception_handler(request, exception):
    """
    catch raised exceptions and log them
    Returns any missing urls

    Parameters
    ----------
    request : request.Request
        the request made via HTTP
    exception : Optional[Exception]
        the exception that was raised from the given request
    Returns
    -------
    Optional[AnyStr]
        if there was a 404 error, this method returns the URL that caused the 404
    """
    url_404 = None
    if isinstance(exception, errors.Refused):
        url = json.loads(request.body.decode("utf-8"))["targetUrl"]
        # _logger.warning("{}, url={}".format(exception, url))
        url_404 = url
    elif isinstance(exception, (errors.Unavailable, errors.ArgumenTextGatewayError)):
        _logger.error(exception)
    elif exception is not None:
        _logger.exception(
            "Request failed request:{} \n exception:{} ".format(request, exception)
        )
    return url_404


def fetch_concurrent(
    topic,
    url_list,
    only_arguments: bool = False,
    topic_relevance: str = TopicRelevance.WORD2VEC,
    pool_size: int = 5,
    chunk_size: int = 1000,
):
    """
    Given a list of article URLs, iterate through them in chunks and return a list of responses


    Parameters
    ----------
    topic : str
        keywords to use for topic identification in ArgText
    url_list : List[AnyStr]
        list of URLs containing documents to argument mine
    only_arguments : bool
        only return the sentences of the estimated arguments
        TODO: check to see if setting this true decreases the computation time on the server
    topic_relevance : str
        use options from TopicRelevance enum
    pool_size : int
        How many threads to use for concurrency. Suggested=around 5
    chunk_size : int
        How many requests to read before downloading them and avoiding out of memory errors
        (which is a known issue with grequests)

    Returns
    -------
    List[requests.Response]
    """
    start_time = time.time()
    s = session.get_session(pool_size=pool_size)
    response_list = []

    chunk_ix = 0
    _logger.debug(">>>> starting doc extraction")
    for i in range(0, len(url_list), chunk_size):
        iter_time = time.time()
        chunk_urls = url_list[i : i + chunk_size]  # noqa: E203
        unsent_requests = (
            grequests.post(
                session.ApiUrl.CLASSIFY_BASE_URL,
                json=bundle_payload(
                    topic,
                    u,
                    only_arguments=only_arguments,
                    topic_relevance=topic_relevance,
                ),
                session=s,
                allow_redirects=False,
            )
            for u in chunk_urls
        )
        # output is a list of response objects
        output = grequests.map(
            unsent_requests, size=100, exception_handler=_exception_handler
        )
        response_list.extend(output)
        _logger.debug(
            "iteration {} took {:0.3f} s ({} docs)".format(
                chunk_ix, time.time() - iter_time, chunk_size
            )
        )
        chunk_ix += 1

    _logger.debug(
        "{} URLs took {:0.3f} s".format(len(url_list), time.time() - start_time)
    )
    return response_list


def process_responses(response_list):
    """
    Take a list of classify responses, convert them to docs and sentences,
    and create associate dataframes

    Parameters
    ----------
    response_list : Iterable[requests.Response]

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame, List]
        docs_df, sentences_df, missing_url_list
    """
    doc_list = []
    sentence_list = []
    missing_url_list = []
    for response in response_list:
        if response is None:
            # we weren't able to get a result from the server
            continue

        try:
            # trigger any exceptions that happened for this doc url
            _response_error_check(response)
        except Exception as e:
            if hasattr(response, "request"):
                # list the docs that the API couldnt access
                url_404 = _exception_handler(response.request, e)
                if url_404:
                    missing_url_list.append(url_404)
            else:
                _logger.exception(errors.Unavailable(e))
            continue

        # parse the response output
        json_response = response.json()
        if json_response:
            doc_list.append(DocumentMetadata.from_dict(json_response["metadata"]))
            topic = json_response["metadata"]["topic"]
            url = json_response["metadata"]["userMetadata"]
            for sentence in json_response["sentences"]:
                sentence_list.append(ClassifiedSentence.from_dict(url, topic, sentence))

    docs_df = pd.DataFrame(utils.dataclasses_to_dicts(doc_list))
    sentence_df = pd.DataFrame(utils.dataclasses_to_dicts(sentence_list))
    return docs_df, sentence_df, missing_url_list
