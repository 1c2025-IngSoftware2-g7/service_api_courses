import pytest
from unittest.mock import MagicMock, patch
from bson import ObjectId
from datetime import datetime, timedelta
from src.repository.courses_repository import CoursesRepository

@pytest.fixture
def mock_collection():
    return MagicMock()

@pytest.fixture
def mock_task_repo():
    repo = MagicMock()
    repo.get_tasks_by_course_ids.return_value = []
    repo.clean_task.return_value = True
    return repo

@pytest.fixture
def mock_logger():
    return MagicMock()

@pytest.fixture
def repo(mock_collection, mock_task_repo, mock_logger):
    return CoursesRepository(mock_collection, mock_task_repo, mock_logger)

def test_create_course(repo, mock_collection, mock_logger):
    mock_collection.insert_one.return_value.inserted_id = ObjectId("64b81e3f4a8f1c1a9f123456")
    course_data = {"name": "Course 1", "description": "desc"}
    course_id = repo.create_course(course_data)
    
    mock_collection.insert_one.assert_called_once()
    mock_logger.debug.assert_called()
    assert course_id == str(mock_collection.insert_one.return_value.inserted_id)
    assert course_data["students"] == []
    assert course_data["modules"] == []

def test_update_course_success(repo, mock_collection, mock_logger):
    mock_collection.update_one.return_value.modified_count = 1
    result = repo.update_course("64b81e3f4a8f1c1a9f123456", {"name": "Updated"})
    assert result is True
    mock_logger.debug.assert_called()

def test_update_course_fail(repo, mock_collection):
    mock_collection.update_one.return_value.modified_count = 0
    result = repo.update_course("64b81e3f4a8f1c1a9f123456", {"name": "Updated"})
    assert result is False

def test_delete_course_success(repo, mock_collection, mock_logger):
    mock_collection.delete_one.return_value.deleted_count = 1
    result = repo.delete_course("64b81e3f4a8f1c1a9f123456")
    assert result is True
    mock_logger.debug.assert_called()

def test_delete_course_fail(repo, mock_collection):
    mock_collection.delete_one.return_value.deleted_count = 0
    result = repo.delete_course("64b81e3f4a8f1c1a9f123456")
    assert result is False

def test_get_course_by_id_found(repo, mock_collection, mock_logger):
    mock_course = {"_id": ObjectId("64b81e3f4a8f1c1a9f123456"), "name": "My Course"}
    mock_collection.find_one.return_value = mock_course
    result = repo.get_course_by_id("64b81e3f4a8f1c1a9f123456")
    assert result == mock_course
    mock_logger.debug.assert_called()

def test_get_course_by_id_not_found(repo, mock_collection):
    mock_collection.find_one.return_value = None
    result = repo.get_course_by_id("64b81e3f4a8f1c1a9f123456")
    assert result is None

def test_enroll_student_in_course_success(repo, mock_collection, mock_logger):
    mock_collection.update_one.return_value.modified_count = 1
    result = repo.enroll_student_in_course("64b81e3f4a8f1c1a9f123456", "student123")
    assert result is True
    mock_logger.debug.assert_called()

def test_enroll_student_in_course_fail(repo, mock_collection):
    mock_collection.update_one.return_value.modified_count = 0
    result = repo.enroll_student_in_course("64b81e3f4a8f1c1a9f123456", "student123")
    assert result is False

def test_is_student_enrolled_in_course(repo, mock_collection):
    course = {"students": ["student123"]}
    repo.get_course_by_id = MagicMock(return_value=course)
    assert repo.is_student_enrolled_in_course("anyid", "student123") is True
    assert repo.is_student_enrolled_in_course("anyid", "other") is False

def test_check_if_course_has_place_to_enroll(repo, mock_collection):
    course = {"students": ["s1", "s2"], "max_students": 3}
    repo.get_course_by_id = MagicMock(return_value=course)
    assert repo.check_if_course_has_place_to_enroll("anyid") is True

    course_full = {"students": ["s1", "s2", "s3"], "max_students": 3}
    repo.get_course_by_id = MagicMock(return_value=course_full)
    assert repo.check_if_course_has_place_to_enroll("anyid") is False

def test_open_course_success(repo, mock_collection, mock_task_repo, mock_logger):
    # Setup mock collection.update_one to pretend successful update
    mock_collection.update_one.return_value.modified_count = 1
    mock_collection.find_one.return_value = {"_id": ObjectId(), "status": "open"}
    mock_task_repo.get_tasks_by_course_ids.return_value = []

    result = repo.open_course("64b81e3f4a8f1c1a9f123456", "2099-01-01", "2099-02-01")
    assert result is not None
    mock_logger.debug.assert_called()

def test_open_course_invalid_dates(repo):
    with pytest.raises(ValueError):
        repo.open_course("id", "2099-02-01", "2099-01-01")  # start after end

    yesterday = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    with pytest.raises(ValueError):
        repo.open_course("id", yesterday, "2099-02-01")  # start date too early

def test_close_course_success(repo, mock_collection, mock_logger):
    mock_collection.update_one.return_value.modified_count = 1
    mock_collection.find_one.return_value = {"_id": ObjectId(), "status": "closed"}

    result = repo.close_course("64b81e3f4a8f1c1a9f123456")
    assert result is not None
    mock_logger.debug.assert_called()
