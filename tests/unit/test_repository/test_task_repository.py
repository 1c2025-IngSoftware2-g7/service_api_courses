import pytest
from unittest.mock import MagicMock, patch
from bson import ObjectId

from src.repository.tasks_repository import TasksRepository
from src.models.task import Task
from src.models.submission import Submission

ID = "6498ef1b9a8f4b1234567890"  # string hex de 24 caracteres
ID_OBJ = ObjectId(ID)
ID_2 = "6498ef1b9a8f4b1234567880"  # string hex de 24 caracteres
ID_OBJ_2 = ObjectId(ID)

@pytest.fixture
def collection_mock():
    return MagicMock()


@pytest.fixture
def logger_mock():
    return MagicMock()


@pytest.fixture
def repo(collection_mock, logger_mock):
    return TasksRepository(collection_mock, logger_mock)


def test_create_task_success(repo, collection_mock, logger_mock):
    task = Task(title="Test Task", course_id="course123", submissions={}, due_date="2025-10-10", module_id="")
    collection_mock.insert_one.return_value.inserted_id = ObjectId("507f1f77bcf86cd799439011")

    inserted_id = repo.create_task(task)

    assert inserted_id == "507f1f77bcf86cd799439011"
    logger_mock.debug.assert_called()


def test_get_task_by_id_found(repo, collection_mock):
    task_dict = {"_id": ID_OBJ, "title": "Test", "course_id": "c123", "module_id": "m111"}
    collection_mock.find_one.return_value = task_dict

    task = repo.get_task_by_id(ID_OBJ)

    assert task.__class__.__name__ == "Task"
    collection_mock.find_one.assert_called_with({"_id": ID_OBJ})


def test_get_task_by_id_not_found(repo, collection_mock):
    collection_mock.find_one.return_value = None

    task = repo.get_task_by_id(ID_OBJ)

    assert task is None


def test_delete_task_success(repo, collection_mock):
    collection_mock.delete_one.return_value.deleted_count = 1

    result = repo.delete_task(ID_OBJ)

    assert result is True
    collection_mock.delete_one.assert_called_with({"_id": ID_OBJ})


def test_delete_task_fail(repo, collection_mock):
    collection_mock.delete_one.return_value.deleted_count = 0

    result = repo.delete_task(ID_OBJ)

    assert result is False


def test_get_tasks_by_query(repo, collection_mock):
    tasks_dicts = [
        {"_id": ID_OBJ, "title": "TEST", "course_id": "c123", "module_id": "m111"}, 
        {"_id": ID_OBJ_2, "title": "TEST2", "course_id": "c122", "module_id": "m191"}
        ]
    collection_mock.find.return_value = tasks_dicts

    tasks = repo.get_tasks_by_query({"status": "active"})

    assert len(tasks) == 2
    collection_mock.find.assert_called_with({"status": "active"})


def test_get_task_with_submission_for_student_exists(repo):
    task = Task(title="Test", submissions={"student1": {"attachments": []}}, due_date="2025-10-10", course_id="c123", module_id="m123")
    with patch.object(repo, "get_tasks_by_query", return_value=[task]):
        result = repo.get_task_with_submission_for_student("taskid", "student1")

    assert result is not None
    assert result.submissions == {"student1": {"attachments": []}}


def test_get_task_with_submission_for_student_no_submissions(repo):
    task = Task(title="Test", submissions={}, due_date="2025-10-10", course_id="c123", module_id="m123")
    with patch.object(repo, "get_tasks_by_query", return_value=[task]):
        result = repo.get_task_with_submission_for_student("taskid", "student1")

    assert result is not None
    assert result.submissions == {}


def test_add_task_submission_success(repo, collection_mock, logger_mock):
    collection_mock.update_one.return_value.matched_count = 1
    submission = Submission(attachments=[{"file": "file1"}])
    with patch.object(
        repo, 
        "get_task_with_submission_for_student", 
        return_value=Task(title="Test", submissions={"student1": submission.to_dict()}, due_date="2025-10-10", course_id="c123", module_id="m123")
        ):
        task = repo.add_task_submission("taskid", "student1", [{"file": "file1"}],True)

    assert "student1" in task.submissions
    logger_mock.info.assert_called()


def test_add_task_submission_task_not_found(repo, collection_mock):
    collection_mock.update_one.return_value.matched_count = 0

    with pytest.raises(ValueError):
        repo.add_task_submission("taskid", "student1", [{"file": "file1"}],True)


def test_get_tasks_by_course_ids_with_filters(repo, collection_mock):
    tasks_dicts = [{"_id": ID_OBJ, "course_id": "course1", "title": "TEST1", "module_id": "mod123"}, {"_id": ID_OBJ_2, "course_id": "course2", "title": "TEST2", "module_id": "mod345"}]
    collection_mock.find.return_value.skip.return_value.limit.return_value = tasks_dicts

    result = repo.get_tasks_by_course_ids(["course1", "course2"], status="active", page=1, limit=2)

    assert len(result) == 2
    collection_mock.find.assert_called()


def test_update_task_success(repo, collection_mock):
    updated_task_dict = {"_id": ID_OBJ, "title": "Updated", "course_id": "c123", "module_id": "m123"}
    collection_mock.find_one_and_update.return_value = updated_task_dict

    task = repo.update_task(ID_OBJ, {"$set": {"title": "Updated"}})

    assert task.title == "Updated"


def test_get_tasks_done_by_student(repo, collection_mock):
    tasks_dicts = [
        {"_id": ID_OBJ_2, "course_id": "course1", "status": "completed", "submissions": {"student1": {}}, "title": "TEST", "module_id": "mod123"},
    ]
    collection_mock.find.return_value = tasks_dicts

    tasks = repo.get_tasks_done_by_student("student1", "course1")

    assert len(tasks) == 1
    collection_mock.find.assert_called()


def test_clean_task(repo, collection_mock):
    repo.clean_task("taskid")

    collection_mock.update_one.assert_called_with(
        {"_id": "taskid"},
        {"$set": {"status": "inactive", "submissions": {}}}
    )
