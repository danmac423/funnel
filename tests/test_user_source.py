import pytest
import json
from funnel.user_source import JsonUserSource, UserSource


def test_usersource_interface():
    class TestSource(UserSource):
        pass

    with pytest.raises(TypeError, match="Can't instantiate abstract class TestSource"):
        TestSource()



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


def test_get_user_existing(valid_user_file):
    json_source = JsonUserSource(valid_user_file)
    user = json_source.get_user("test_user")
    assert user == {"username": "test_user", "password": "test_pass"}


def test_get_user_non_existing(valid_user_file):
    json_source = JsonUserSource(valid_user_file)
    user = json_source.get_user("non_existing_user")
    assert user is None


def test_empty_users_key(tmp_path):
    file_path = tmp_path / "empty_users.json"
    data = {}
    file_path.write_text(json.dumps(data))
    json_source = JsonUserSource(file_path)
    user = json_source.get_user("test_user")
    assert user is None