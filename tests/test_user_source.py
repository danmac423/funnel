import pytest
import json
from funnel.user_source import JsonUserSource, UserSource


def test_usersource_cannot_instantiate():
    with pytest.raises(
        TypeError, match="Can't instantiate abstract class UserSource"
    ):
        UserSource() # type: ignore


def test_usersource_incomplete_subclass():
    class IncompleteUserSource(UserSource):
        pass

    with pytest.raises(
        TypeError,
        match="Can't instantiate abstract class IncompleteUserSource"
    ):
        IncompleteUserSource() # type: ignore



@pytest.fixture
def valid_user_file(tmp_path):
    file_path = tmp_path / "users.json"
    data = {"users": [{"username": "test_user", "password": "test_pass"}]}
    file_path.write_text(json.dumps(data))
    return file_path


@pytest.fixture
def invalid_user_file(tmp_path):
    file_path = tmp_path / "invalid_users.json"
    file_path.write_text("{ invalid json }")
    return file_path


@pytest.fixture
def missing_file(tmp_path):
    return tmp_path / "missing.json"


@pytest.fixture
def invalid_users_structure(tmp_path):
    file_path = tmp_path / "invalid_users.json"
    data = {"users": "not_a_list"}
    file_path.write_text(json.dumps(data))
    return file_path

@pytest.fixture
def invalid_user_format_no_username(tmp_path):
    file_path = tmp_path / "invalid_user.json"
    data = {"users": [{"not_username": "test_user", "password": "test_pass"}]}
    file_path.write_text(json.dumps(data))
    return file_path

@pytest.fixture
def invalid_user_format_no_dict(tmp_path):
    file_path = tmp_path / "invalid_user.json"
    data = {"users": ["user1", "user2"]}
    file_path.write_text(json.dumps(data))
    return file_path


def test_get_user_existing(valid_user_file):
    json_source = JsonUserSource(valid_user_file)
    user = json_source.get_user("test_user")
    assert user == {"username": "test_user", "password": "test_pass"}


def test_get_user_non_existing(valid_user_file):
    json_source = JsonUserSource(valid_user_file)
    user = json_source.get_user("non_existing_user")
    assert user is None

def test_invalid_json_format(invalid_user_file):
    json_source = JsonUserSource(invalid_user_file)
    with pytest.raises(ValueError, match="Invalid JSON format"):
        json_source.get_user("test_user")


def test_file_not_found(missing_file):
    json_source = JsonUserSource(missing_file)
    with pytest.raises(FileNotFoundError, match="File not found"):
        json_source.get_user("test_user")


def test_invalid_users_key(invalid_users_structure):
    json_source = JsonUserSource(invalid_users_structure)
    with pytest.raises(
        ValueError, match="Invalid data format: 'users' should be a list"
    ):
        json_source.get_user("test_user")


def test_invalid_user_format_no_username(invalid_user_format_no_username):
    json_source = JsonUserSource(invalid_user_format_no_username)
    with pytest.raises(ValueError, match="Invalid user format"):
        json_source.get_user("test_user")


def test_invalid_user_format_no_dict(invalid_user_format_no_dict):
    json_source = JsonUserSource(invalid_user_format_no_dict)
    with pytest.raises(ValueError, match="Invalid user format"):
        json_source.get_user("test_user")
