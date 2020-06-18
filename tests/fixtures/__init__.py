import os
import json
from arg_mine import PROJECT_DIR


def load_json_fixture(fixture_filename):
    """Get test fixture data from a JSON filename"""
    # import pkg_resources
    # json_path = pkg_resources.resource_filename("tests.fixtures", fixture_filename)
    json_path = os.path.join(PROJECT_DIR, "tests", "fixtures", fixture_filename)
    with open(json_path, "r") as f:
        json_blob = json.load(f)
    return json_blob


def _drop_keys(my_dict, ignored_keys):
    for k in ignored_keys:
        if k in my_dict:
            del my_dict[k]
    return my_dict


def save_json_request_fixture(
    fixture_filename,
    payload: dict,
    response: dict,
    status_code: int = 200,
    drop_keys: list = None,
):
    """
    Save a requests.post.json return as a test fixture

    Parameters
    ----------
    fixture_filename : str
        saved to tests/fixtures/
    payload
    response
    status_code
    drop_keys : list of keys in payload to NOT save in the output

    Returns
    -------

    """
    import pkg_resources

    json_path = pkg_resources.resource_filename("tests.fixtures", fixture_filename)
    # pop any keywords we don't want to save
    if drop_keys:
        payload = _drop_keys(payload, drop_keys)

    test_data = {
        "payload": payload,
        "response": response,
        "status_code": status_code,
    }
    with open(json_path, "w") as f:
        json.dump(test_data, f, indent=2)
