import pytest
from unittest.mock import MagicMock
from src.repository.users_data_repository import UsersDataRepository


@pytest.fixture
def collection_users_mock():
    return MagicMock()


@pytest.fixture
def approved_courses_collection_mock():
    return MagicMock()


@pytest.fixture
def logger_mock():
    return MagicMock()


@pytest.fixture
def repo(collection_users_mock, approved_courses_collection_mock, logger_mock):
    return UsersDataRepository(collection_users_mock, approved_courses_collection_mock, logger_mock)


def test_set_favourite_course_insert(repo, collection_users_mock, logger_mock):
    collection_users_mock.find_one.return_value = None
    result = repo.set_favourite_course("course1", "student1")
    assert result is True
    collection_users_mock.insert_one.assert_called_once_with(
        {"student_id": "student1", "favourite_courses": ["course1"]}
    )
    logger_mock.debug.assert_called()


def test_set_favourite_course_update(repo, collection_users_mock):
    collection_users_mock.find_one.return_value = {"student_id": "student1", "favourite_courses": []}
    result = repo.set_favourite_course("course1", "student1")
    assert result is True
    collection_users_mock.update_one.assert_called_once_with(
        {"student_id": "student1"},
        {"$addToSet": {"favourite_courses": "course1"}},
    )


def test_remove_course_from_favourites_user_not_found(repo, collection_users_mock, logger_mock):
    collection_users_mock.find_one.return_value = None
    result = repo.remove_course_from_favourites("course1", "student1")
    assert result is False
    logger_mock.debug.assert_called()


def test_remove_course_from_favourites_course_not_in_list(repo, collection_users_mock):
    collection_users_mock.find_one.return_value = {"student_id": "student1", "favourite_courses": ["course2"]}
    result = repo.remove_course_from_favourites("course1", "student1")
    assert result is False


def test_remove_course_from_favourites_success(repo, collection_users_mock):
    collection_users_mock.find_one.return_value = {"student_id": "student1", "favourite_courses": ["course1", "course2"]}
    result = repo.remove_course_from_favourites("course1", "student1")
    assert result is True
    collection_users_mock.update_one.assert_called_once_with(
        {"student_id": "student1"},
        {"$pull": {"favourite_courses": "course1"}},
    )


def test_course_already_favourite_true(repo, collection_users_mock):
    collection_users_mock.find_one.return_value = {"student_id": "student1", "favourite_courses": ["course1"]}
    assert repo.course_already_favourite("course1", "student1") is True


def test_course_already_favourite_false(repo, collection_users_mock):
    collection_users_mock.find_one.return_value = {"student_id": "student1", "favourite_courses": ["course2"]}
    assert repo.course_already_favourite("course1", "student1") is False


def test_course_already_favourite_user_not_found(repo, collection_users_mock):
    collection_users_mock.find_one.return_value = None
    assert repo.course_already_favourite("course1", "student1") is False


def test_get_favourites_from_student_id_found(repo, collection_users_mock):
    collection_users_mock.find_one.return_value = {"student_id": "student1", "favourite_courses": ["course1", "course2"]}
    result = repo.get_favourites_from_student_id("student1")
    assert result == ["course1", "course2"]


def test_get_favourites_from_student_id_not_found(repo, collection_users_mock):
    collection_users_mock.find_one.return_value = None
    result = repo.get_favourites_from_student_id("student1")
    assert result is None


def test_check_student_enrollment_true(repo, logger_mock):
    result = repo.check_student_enrollment("student1", "course1", ["student1", "student2"])
    assert result is True
    logger_mock.debug.assert_called()


def test_check_student_enrollment_false(repo):
    result = repo.check_student_enrollment("student3", "course1", ["student1", "student2"])
    assert result is False


def test_approve_student_insert(repo, approved_courses_collection_mock, logger_mock):
    approved_courses_collection_mock.find_one.return_value = None
    result = repo.approve_student("course1", "student1", 95)
    assert result is True
    approved_courses_collection_mock.insert_one.assert_called_once_with(
        {
            "student_id": "student1",
            "approved_courses": [{"course_id": "course1", "final_grade": 95}],
        }
    )
    logger_mock.info.assert_called()


def test_approve_student_update(repo, approved_courses_collection_mock):
    approved_courses_collection_mock.find_one.return_value = {"student_id": "student1", "approved_courses": []}
    result = repo.approve_student("course1", "student1", 95)
    assert result is True
    approved_courses_collection_mock.update_one.assert_called_once_with(
        {"student_id": "student1"},
        {"$addToSet": {"approved_courses": {"course_id": "course1", "final_grade": 95}}},
    )


def test_get_student_approved_courses_found(repo, approved_courses_collection_mock):
    approved_courses_collection_mock.find_one.return_value = {"approved_courses": [{"course_id": "course1"}]}
    result = repo.get_student_approved_courses("student1")
    assert result == [{"course_id": "course1"}]


def test_get_student_approved_courses_not_found(repo, approved_courses_collection_mock):
    approved_courses_collection_mock.find_one.return_value = None
    result = repo.get_student_approved_courses("student1")
    assert result == []


def test_get_approved_signatures_found(repo, approved_courses_collection_mock):
    approved_courses_collection_mock.find_one.return_value = {"approved_courses": [{"course_id": "course1"}]}
    result = repo.get_approved_signatures("student1")
    assert result == [{"course_id": "course1"}]


def test_get_approved_signatures_not_found(repo, approved_courses_collection_mock):
    approved_courses_collection_mock.find_one.return_value = None
    result = repo.get_approved_signatures("student1")
    assert result == []


def test_check_assistant_already_in_course_true(repo, collection_users_mock):
    collection_users_mock.find_one.return_value = {"assistant": {"course1": {"perm": True}}}
    assert repo.check_assistant_already_in_course("course1", "assistant1") is True


def test_check_assistant_already_in_course_false_no_user(repo, collection_users_mock):
    collection_users_mock.find_one.return_value = None
    assert repo.check_assistant_already_in_course("course1", "assistant1") is False


def test_check_assistant_already_in_course_false_no_assistant_key(repo, collection_users_mock):
    collection_users_mock.find_one.return_value = {"student_id": "assistant1"}
    assert repo.check_assistant_already_in_course("course1", "assistant1") is False


def test_check_assistant_already_in_course_false_no_course_key(repo, collection_users_mock):
    collection_users_mock.find_one.return_value = {"assistant": {}}
    assert repo.check_assistant_already_in_course("course1", "assistant1") is False


def test_add_assistant_to_course_insert(repo, collection_users_mock):
    collection_users_mock.find_one.return_value = None
    repo.add_assistant_to_course("course1", "assistant1", {"read": True})
    collection_users_mock.insert_one.assert_called_once_with(
        {"student_id": "assistant1", "assistant": {"course1": {"read": True}}}
    )


def test_add_assistant_to_course_update(repo, collection_users_mock):
    collection_users_mock.find_one.return_value = {"student_id": "assistant1", "assistant": {}}
    repo.add_assistant_to_course("course1", "assistant1", {"read": True})
    collection_users_mock.update_one.assert_called_once_with(
        {"student_id": "assistant1"},
        {"$set": {"assistant.course1": {"read": True}}},
    )


def test_get_assistant_permissions_for_course_found(repo, collection_users_mock):
    collection_users_mock.find_one.return_value = {"assistant": {"course1": {"read": True}}}
    perms = repo.get_assistant_permissions_for_course("course1", "assistant1")
    assert perms == {"read": True}


def test_get_assistant_permissions_for_course_user_not_found(repo, collection_users_mock):
    collection_users_mock.find_one.return_value = None
    perms = repo.get_assistant_permissions_for_course("course1", "assistant1")
    assert perms is None


def test_get_assistant_permissions_for_course_not_in_course(repo, collection_users_mock):
    collection_users_mock.find_one.return_value = {"assistant": {}}
    perms = repo.get_assistant_permissions_for_course("course1", "assistant1")
    assert perms is None


def test_update_assistant_permissions_success(repo, collection_users_mock):
    collection_users_mock.find_one.return_value = {"assistant": {"course1": {"read": True}}}
    update_result_mock = MagicMock()
    update_result_mock.modified_count = 1
    collection_users_mock.update_one.return_value = update_result_mock

    result = repo.update_assistant_permissions("course1", "assistant1", {"write": True})
    assert result is True


def test_update_assistant_permissions_fail_no_user(repo, collection_users_mock):
    collection_users_mock.find_one.return_value = None
    result = repo.update_assistant_permissions("course1", "assistant1", {"write": True})
    assert result is False


def test_update_assistant_permissions_fail_no_assistant_key(repo, collection_users_mock):
    collection_users_mock.find_one.return_value = {"student_id": "assistant1"}
    result = repo.update_assistant_permissions("course1", "assistant1", {"write": True})
    assert result is False


def test_update_assistant_permissions_fail_no_course_key(repo, collection_users_mock):
    collection_users_mock.find_one.return_value = {"assistant": {}}
    result = repo.update_assistant_permissions("course1", "assistant1", {"write": True})
    assert result is False


def test_remove_assistant_from_course_success(repo, collection_users_mock):
    update_result_mock = MagicMock()
    update_result_mock.modified_count = 1
    collection_users_mock.update_one.return_value = update_result_mock

    result = repo.remove_assistant_from_course_with_id("course1", "assistant1")
    assert result is True


def test_remove_assistant_from_course_fail(repo, collection_users_mock):
    update_result_mock = MagicMock()
    update_result_mock.modified_count = 0
    collection_users_mock.update_one.return_value = update_result_mock

    result = repo.remove_assistant_from_course_with_id("course1", "assistant1")
    assert result is False


def test_check_assistants_permissions_true(repo, collection_users_mock):
    collection_users_mock.find_one.return_value = {"assistant": {"course1": {"perm1": True}}}
    result = repo.check_assistants_permissions("course1", "assistant1", "perm1")
    assert result is True


def test_check_assistants_permissions_false_no_user(repo, collection_users_mock):
    collection_users_mock.find_one.return_value = None
    result = repo.check_assistants_permissions("course1", "assistant1", "perm1")
    assert result is False


def test_check_assistants_permissions_false_no_assistant_key(repo, collection_users_mock):
    collection_users_mock.find_one.return_value = {"student_id": "assistant1"}
    result = repo.check_assistants_permissions("course1", "assistant1", "perm1")
    assert result is False


def test_check_assistants_permissions_false_no_course_key(repo, collection_users_mock):
    collection_users_mock.find_one.return_value = {"assistant": {}}
    result = repo.check_assistants_permissions("course1", "assistant1", "perm1")
    assert result is False


def test_check_assistants_permissions_false_perm_missing(repo, collection_users_mock):
    collection_users_mock.find_one.return_value = {"assistant": {"course1": {}}}
    result = repo.check_assistants_permissions("course1", "assistant1", "perm1")
    assert result is False
