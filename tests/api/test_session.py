import unittest
from unittest import mock
import requests
import json

from arg_mine.api import session, errors
from tests.fixtures import load_json_fixture


class TestApiUrl(unittest.TestCase):
    def test_class_exists(self):
        # just a basic coverage test to make sure it exists
        self.assertEqual(
            session.ApiUrl.CLASSIFY_BASE_URL,
            session.ApiUrl.GATEWAY_BASE_URL + "/classify",
        )


# This method will be used by the mock to replace requests.post
def mocked_requests_post(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    # case statements for different test URLs.
    # NOTE that these URLs are not real, only mocked!
    if args[0] == session.ApiUrl.CLASSIFY_BASE_URL + "/test_only_args":
        blob = load_json_fixture("response_classify_only_args.json")
        return MockResponse(blob["response"], 200)
    elif args[0] == "http://someotherurl.com/anothertest.json":
        blob = load_json_fixture("response_classify_only_args.json")

        return MockResponse({"key2": "value2"}, 200)

    return MockResponse(None, 404)


# Our test case class
class TestFetch(unittest.TestCase):
    @staticmethod
    def _mock_response(status=200, content=None, json_data=None, raise_for_status=None):
        """
        Helper function that builds different mocked responses
        """
        mock_resp = mock.Mock()
        # set status code and content
        mock_resp.status_code = status

        # add json data if provided
        if json_data:
            mock_resp.json = mock.Mock(return_value=json_data)
            if not content:
                mock_resp.content = json.dumps(json_data)

        # mock raise_for_status call w/optional error
        mock_resp.raise_for_status = mock.Mock()
        if raise_for_status:
            if isinstance(raise_for_status, requests.HTTPError):
                raise_for_status.response = mock.PropertyMock(mock_resp)
                # we need to load the response object inside the error, since we use this content for error handling
                raise_for_status.response.status_code = status
                raise_for_status.response.json = mock.Mock(return_value=json_data)
            mock_resp.raise_for_status.side_effect = raise_for_status

        return mock_resp

    # We patch 'requests.post' with our own method. The mock object is passed in to our test case method.
    @mock.patch("arg_mine.api.session.requests.post")
    def test_fetch_only_args(self, mock_post):
        expected = load_json_fixture("response_classify_only_args.json")
        payload = expected["payload"]
        mock_resp = self._mock_response(
            status=expected["status_code"], json_data=expected["response"]
        )
        mock_post.return_value = mock_resp

        # Assert requests.post calls
        response = session.fetch(
            session.ApiUrl.CLASSIFY_BASE_URL + "/test_only_args", payload
        )
        self.assertEqual(response, expected["response"])

        # Assert that our mocked method was called with the right parameters
        print(mock_post.call_args_list)
        self.assertIn(
            mock.call(
                session.ApiUrl.CLASSIFY_BASE_URL + "/test_only_args",
                json=payload,
                timeout=session.DEFAULT_TIMEOUT),
            mock_post.call_args_list
        )

    @mock.patch("arg_mine.api.session.requests.post")
    def test_fetch_refused(self, mock_post):
        expected = load_json_fixture("response_classify_refused_remote_404.json")
        payload = expected["payload"]
        print("response json")
        print(expected["response"])

        mock_resp = self._mock_response(
            status=expected["status_code"],
            json_data=expected["response"],
            raise_for_status=requests.HTTPError(
                "400 Client Error: BAD REQUEST for url: https://api.argumentsearch.com/en/classify"
            ),
        )
        mock_post.return_value = mock_resp

        with self.assertRaises(errors.Refused):
            _ = session.fetch(
                session.ApiUrl.CLASSIFY_BASE_URL + "/test_only_args", payload
            )

    @mock.patch("arg_mine.api.session.requests.post")
    def test_fetch_gateway_error(self, mock_post):
        expected = load_json_fixture("response_classify_gateway_error.json")
        payload = expected["payload"]
        print("response json")
        print(expected["response"])

        mock_resp = self._mock_response(
            status=expected["status_code"],
            json_data=expected["response"],
            raise_for_status=requests.HTTPError(
                "400 Client Error: BAD REQUEST for url: https://api.argumentsearch.com/en/classify"
            ),
        )
        mock_post.return_value = mock_resp

        with self.assertRaises(errors.ArgumenTextGatewayError):
            _ = session.fetch(
                session.ApiUrl.CLASSIFY_BASE_URL + "/test_only_args", payload
                    )

    @mock.patch("arg_mine.api.session.requests.post")
    def test_fetch_bad_payload(self, mock_post):
        expected = load_json_fixture("response_classify_500_bad_payload.json")
        payload = expected["payload"]

        mock_resp = self._mock_response(
            status=expected["status_code"],
            json_data=expected["response"],
            raise_for_status=requests.HTTPError(
                "500 Server Error: INTERNAL SERVER ERROR for url: https://api.argumentsearch.com/en/classify"
            ),
        )
        mock_post.return_value = mock_resp

        with self.assertRaises(errors.InternalGatewayError):
            _ = session.fetch(
                session.ApiUrl.CLASSIFY_BASE_URL + "/test_only_args", payload
            )

    @mock.patch("arg_mine.api.session.requests.post")
    def test_fetch_timeout(self, mock_post):
        expected = load_json_fixture("response_classify_only_args.json")
        payload = expected["payload"]

        mock_resp = self._mock_response(
            status=408,
            json_data=None,
            raise_for_status=requests.Timeout(
                "mocked timeout"),
        )
        mock_post.return_value = mock_resp

        with self.assertRaises(errors.NotResponding):
            _ = session.fetch(
                session.ApiUrl.CLASSIFY_BASE_URL + "/test_only_args", payload
            )


if __name__ == "__main__":
    unittest.main()
