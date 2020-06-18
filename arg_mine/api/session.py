import http.cookiejar
import logging
import requests

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


def get_session():
    """Return a session object"""
    # todo: add authentication here
    query_session = requests.Session()
    query_session.cookies.policy = _BlockAll()
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
        _logger.error("{} : {}".format(e.response.status_code, e.response.json()['error']))
        raise errors.NotResponding(
            "Server not responding, ConnectionError or Timeout"
        ) from e
    except requests.HTTPError as e:
        print("****** inside HTTPError catch")
        print(e.response.status_code)
        print(e.response.json())
        _logger.error("{} : {}".format(e.response.status_code, e.response.json()))
        if e.response.status_code == 400:
            error = e.response.json()
            message = error["error"]
            print("** inside 400")
            print(message)
            if errors.Refused.TARGET_MSG in message:
                raise errors.Refused(message)
            raise errors.ArgumenTextGatewayError(message) from e

        msg = "ArgumentText service had internal error."
        _logger.exception(msg)
        raise errors.Unavailable(msg) from e
    json_response = response.json()
    return json_response
