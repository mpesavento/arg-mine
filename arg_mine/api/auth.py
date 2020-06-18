import os

from dotenv import load_dotenv, find_dotenv


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
