import requests

from arg_mine.api import errors

GATEWAY_BASE_URL = "https://api.argumentsearch.com/en/"

CLASSIFY_BASE_URL = GATEWAY_BASE_URL + "/classify"


def main():
    timeout = 5
    payload = {}
    headers = {}
    try:
        response = requests.post(
            CLASSIFY_BASE_URL,
            json=payload,
            headers=headers,
            timeout=timeout,
        )
        response.raise_for_status()

    except (requests.ConnectionError, requests.Timeout) as e:
        raise errors.Unavailable() from e
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            error = e.response.json()
            code = error['code']
            message = error['message']
        if code == 1:
            raise errors.Refused(code, message) from e
        elif code == 2:
            raise errors.Stolen(code, message) from e
        else:
            raise errors.PaymentGatewayError(code, message) from e

        logger.exception("Payment service had internal error.")
        raise errors.Unavailable() from e