import http.cookiejar
import logging
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from arg_mine.api import errors

_logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 5  # sec


class ApiUrl:
    """
    Enum-like class for holding the target URLs
    """

    GATEWAY_BASE_URL = "https://api.argumentsearch.com/en"
    CLASSIFY_BASE_URL = GATEWAY_BASE_URL + "/classify"
    CLUSTER_BASE_URL = GATEWAY_BASE_URL + "/cluster_arguments"
    SEARCH_BASE_URL = GATEWAY_BASE_URL + "/search"


# A shared requests session for payment requests.
class _BlockAll(http.cookiejar.CookiePolicy):
    def set_ok(self, cookie, request):
        return False


class TimeoutHTTPAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        self.timeout = DEFAULT_TIMEOUT
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
            del kwargs["timeout"]
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        timeout = kwargs.get("timeout")
        if timeout is None:
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)


def get_session():
    """Return a session object"""
    # todo: add authentication here
    query_session = requests.Session()
    # block all collection of cookies
    query_session.cookies.policy = _BlockAll()

    # create retry strategy
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS", "POST"],  # generally avoid having POST in here, it inserts
        backoff_factor=1,  # {backoff factor} * (2 ** ({number of total retries} - 1))
    )

    # Mount timeout adapter for both http and https usage
    adapter = TimeoutHTTPAdapter(timeout=DEFAULT_TIMEOUT, max_retries=retry_strategy)
    query_session.mount("https://", adapter)

    return query_session


def fetch(
    base_url: str, payload: dict, timeout: float = DEFAULT_TIMEOUT, request_session=None
):
    """
    Make request from base API service, with error handling

    Parameters
    ----------
    base_url : str
        The target URL for the API POST call, eg ApiUrl.CLASSIFY_BASE_URL
    payload : dict
        Contains all of the associated parameters
    timeout : float
        API call timeout, in seconds
    request_session : requests.Session
        Optional, uses this session to speed up repeated API calls

    Returns
    -------
    dict with the API response

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
    # select which version of post() we want to use, if we have a session injected or not
    if request_session and hasattr(request_session, "post"):
        post_fn = request_session.post
    else:
        post_fn = requests.post

    try:
        # do the requests call
        # inject a session or the requests object, confirm that injected object has a `post` method
        response = post_fn(base_url, json=payload, timeout=timeout)
        response.raise_for_status()

    except (requests.ConnectionError, requests.Timeout) as e:
        raise errors.NotResponding(
            "Server not responding, ConnectionError or Timeout ({} s)".format(timeout)
        ) from e
    except requests.HTTPError as e:
        if e.response.status_code == 400:
            error = e.response.json()
            _logger.error("{} : {}".format(e.response.status_code, e.response.json()))
            message = error["error"]
            if errors.Refused.TARGET_MSG in message:
                raise errors.Refused(e.response.status_code, message)
            raise errors.ArgumenTextGatewayError(e.response.status_code, message) from e
        elif e.response.status_code == 500:
            msg = (
                "Server Error: INTERNAL SERVER ERROR for url: https://api.argumentsearch.com/en/classify" +
                ", check payload contents?"
            )
            _logger.error("{} : {}".format(500, msg))
            raise errors.InternalGatewayError(e.response.status_code, msg)

        msg = "ArgumentText service had internal error."
        _logger.exception(msg)
        raise errors.ArgumenTextGatewayError(e.response.status_code, msg) from e
    json_response = response.json()
    return json_response
