import os
import logging

import requests
from dotenv import find_dotenv, load_dotenv
import http.cookiejar


logger = logging.getLogger(__name__)

GATEWAY_BASE_URL = "https://api.argumentsearch.com/en"
CLASSIFY_BASE_URL = GATEWAY_BASE_URL + "/classify"
CLUSTER_BASE_URL = GATEWAY_BASE_URL + "/cluster_arguments"
SEARCH_BASE_URL = GATEWAY_BASE_URL + "/search"

DEFAULT_TIMEOUT = 5  # sec


# A shared requests session for payment requests.
class _BlockAll(http.cookiejar.CookiePolicy):
    def set_ok(self, cookie, request):
        return False


query_session = requests.Session()
query_session.cookies.policy = _BlockAll()


def load_auth_tokens():
    """
    Read the ArgumentText auth tokens from the .env file

    # TODO: make this into a context manager

    Returns
    -------
    user_id, api_key
    """
    load_dotenv(find_dotenv())
    am_user_id = os.getenv("ARGUMENTEXT_USERID")
    am_user_key = os.getenv("ARGUMENTEXT_KEY")
    return am_user_id, am_user_key
