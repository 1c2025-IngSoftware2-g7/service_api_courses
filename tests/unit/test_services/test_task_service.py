import pytest
from flask import Flask
from unittest.mock import patch, MagicMock
from src.models.task import Task, TaskType, TaskStatus

@pytest.fixture(scope="session")
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    return app

@pytest.fixture(scope="function", autouse=True)
def app_context(app):
    """Habilita app context automáticamente en todos los tests"""
    with app.app_context():
        yield

@pytest.fixture(scope="session", autouse=True)
def patch_mongo():
    with patch("pymongo.MongoClient") as mock_client:
        mock_client.return_value = MagicMock()
        yield

@pytest.fixture
def mock_repo():
    return MagicMock()

@pytest.fixture
def mock_course_service():
    return MagicMock()

@pytest.fixture
def mock_user_service():
    return MagicMock()

@pytest.fixture
def mock_repository_courses():
    return MagicMock()

@pytest.fixture
def mock_logger():
    return MagicMock()

@pytest.fixture
def service(mock_repo, mock_course_service, mock_user_service, mock_repository_courses, mock_logger):
    from src.services.task_service import TaskService
    return TaskService(
        tasks_repository=mock_repo,
        course_service=mock_course_service,
        user_service=mock_user_service,
        repository_courses=mock_repository_courses,
        logger=mock_logger
    )

def build_task_mock(task_type=TaskType.TASK, status=TaskStatus.INACTIVE):
    task = MagicMock(spec=Task)
    task.course_id = "course123"
    task.task_type = task_type
    task.title = "old title"
    task.description = "old desc"
    task.instructions = "old instr"
    task.due_date = 1000
    task.attachments = ["file1"]
    task.status = status.value

    task.to_dict.return_value = {
        "title": "Test Task",
        "status": status.value,
        "course_id": "course123",
        "_id": "task123",
        "module_id": "module456",
    }
    return task


def test_create_task_missing_fields(service):
    data = {"title": "Task without due_date and course_id"}
    response = service.create_task(data, "user123")
    assert response["code_status"] == 400
    assert "due_date" in response["response"].get_json()["detail"] or "Field due_date is required" in response["response"].get_json()["detail"]


def test_create_task_user_no_permissions(service, mock_user_service, mock_repository_courses):
    data = {"title": "Task", "due_date": "2025-12-31", "course_id": "course123"}
    mock_user_service.check_assistants_permissions.return_value = False
    mock_repository_courses.is_user_owner.return_value = False

    response = service.create_task(data, "user123")
    assert response["code_status"] == 403
    assert "not allowed" in response["response"].get_json()["detail"]


def test_create_task_course_not_found(service, mock_user_service, mock_repository_courses, mock_course_service):
    data = {"title": "Task", "due_date": "2025-12-31", "course_id": "course123"}
    mock_user_service.check_assistants_permissions.return_value = True
    mock_repository_courses.is_user_owner.return_value = False
    mock_course_service.get_course_by_id.return_value = None  # Simula curso no encontrado

    response = service.create_task(data, "user123")
    assert response["code_status"] == 404
    assert "Course not found" in response["response"].get_json()["detail"]


def test_create_task_invalid_due_date_format(service, mock_user_service, mock_repository_courses, mock_course_service):
    data = {"title": "Task", "due_date": "invalid-date", "course_id": "course123"}
    mock_user_service.check_assistants_permissions.return_value = True
    mock_repository_courses.is_user_owner.return_value = True
    mock_course_service.get_course_by_id.return_value = {"code_status": 200}

    response = service.create_task(data, "user123")
    assert response["code_status"] == 400
    assert "Invalid due_date format" in response["response"].get_json()["detail"]


def test_create_task_success(service, mock_user_service, mock_repository_courses, mock_course_service, mock_repo):
    data = {
        "title": "Task 1",
        "due_date": "2025-12-31 23:59:59",
        "course_id": "course123",
        "task_type": "task",
        "description": "desc",
        "instructions": "inst",
        "attachments": ["file1.pdf"]
    }
    mock_user_service.check_assistants_permissions.return_value = True
    mock_repository_courses.is_user_owner.return_value = False
    mock_course_service.get_course_by_id.return_value = {"code_status": 200}
    mock_repo.create_task.return_value = "task123"

    response = service.create_task(data, "user123")
    assert response["code_status"] == 201
    assert response["response"]["message"] == "Task created successfully"
    assert response["response"]["data"]["_id"] == "task123"
    assert response["response"]["data"]["title"] == "Task 1"


def test_create_task_internal_error(service, mock_user_service, mock_repository_courses, mock_course_service, mock_repo, mock_logger):
    data = {
        "title": "Task 1",
        "due_date": "2025-12-31 23:59:59",
        "course_id": "course123"
    }
    mock_user_service.check_assistants_permissions.return_value = True
    mock_repository_courses.is_user_owner.return_value = True
    mock_course_service.get_course_by_id.return_value = {"code_status": 200}
    mock_repo.create_task.side_effect = Exception("DB failure")

    response = service.create_task(data, "user123")

    assert response["code_status"] == 500
    assert "An error occurred while creating the task" in response["response"].get_json()["detail"]
    mock_logger.error.assert_called_once()

def test_update_task_not_found(service, mock_repo):
    mock_repo.get_tasks_by_query.return_value = []
    response = service.update_task("task123", {"title": "new"}, "user123")
    assert response["code_status"] == 404
    assert "The specified task does not exist" in response["response"].get_json()["detail"]

def test_update_task_no_permissions(service, mock_repo, mock_user_service, mock_repository_courses):
    task = build_task_mock()
    mock_repo.get_tasks_by_query.return_value = [task]
    mock_user_service.check_assistants_permissions.return_value = False
    mock_repository_courses.is_user_owner.return_value = False

    response = service.update_task("task123", {"title": "new"}, "user123")
    assert response["code_status"] == 403
    assert "not allowed" in response["response"].get_json()["detail"]

def test_update_task_empty_data(service, mock_repo, mock_user_service, mock_repository_courses):
    task = build_task_mock()
    mock_repo.get_tasks_by_query.return_value = [task]
    mock_user_service.check_assistants_permissions.return_value = True
    mock_repository_courses.is_user_owner.return_value = False

    response = service.update_task("task123", {}, "user123")
    assert response["code_status"] == 400
    assert "No fields provided" in response["response"].get_json()["detail"]

def test_update_task_invalid_due_date_format(service, mock_repo, mock_user_service, mock_repository_courses):
    task = build_task_mock()
    mock_repo.get_tasks_by_query.return_value = [task]
    mock_user_service.check_assistants_permissions.return_value = True
    mock_repository_courses.is_user_owner.return_value = True

    # due_date invalid string format
    response = service.update_task("task123", {"due_date": "bad-date"}, "user123")
    assert response["code_status"] == 400
    assert "Invalid due_date format" in response["response"].get_json()["detail"]

def test_update_task_due_date_wrong_type(service, mock_repo, mock_user_service, mock_repository_courses):
    task = build_task_mock()
    mock_repo.get_tasks_by_query.return_value = [task]
    mock_user_service.check_assistants_permissions.return_value = True
    mock_repository_courses.is_user_owner.return_value = True

    # due_date not int or string
    response = service.update_task("task123", {"due_date": 3.14}, "user123")
    assert response["code_status"] == 400
    assert "due_date must be an integer" in response["response"].get_json()["detail"]

def test_update_task_no_changes(service, mock_repo, mock_user_service, mock_repository_courses):
    task = build_task_mock()
    mock_repo.get_tasks_by_query.return_value = [task]
    mock_user_service.check_assistants_permissions.return_value = True
    mock_repository_courses.is_user_owner.return_value = False

    # Sending the same data as existing task
    data = {
        "title": "old title",
        "description": "old desc",
        "instructions": "old instr",
        "due_date": 1000,
        "attachments": ["file1"],
        "status": "inactive",
    }
    response = service.update_task("task123", data, "user123")
    assert response["code_status"] == 400
    assert "No valid fields provided for update or values are the same" in response["response"].get_json()["detail"]

def test_update_task_success(service, mock_repo, mock_user_service, mock_repository_courses):
    task = build_task_mock()
    mock_repo.get_tasks_by_query.return_value = [task]
    mock_user_service.check_assistants_permissions.return_value = False
    mock_repository_courses.is_user_owner.return_value = True

    # El repo confirma la actualización
    mock_repo.update_task.return_value = True

    data = {
        "title": "new title",
        "due_date": 2000,
    }

    response = service.update_task("task123", data, "user123")
    assert response["code_status"] == 200
    assert response["response"]["title"] == "Task updated"
    mock_repo.update_task.assert_called_once()

def test_update_task_repo_fails(service, mock_repo, mock_user_service, mock_repository_courses, mock_logger):
    task = build_task_mock()
    mock_repo.get_tasks_by_query.return_value = [task]
    mock_user_service.check_assistants_permissions.return_value = True
    mock_repository_courses.is_user_owner.return_value = False

    # El repo dice que no se pudo actualizar
    mock_repo.update_task.return_value = False

    data = {"title": "new title"}

    response = service.update_task("task123", data, "user123")
    assert response["code_status"] == 400
    assert "The task could not be updated" in response["response"].get_json()["detail"]

def test_update_task_exception(service, mock_repo, mock_user_service, mock_repository_courses, mock_logger):
    task = build_task_mock()
    mock_repo.get_tasks_by_query.return_value = [task]
    mock_user_service.check_assistants_permissions.return_value = True
    mock_repository_courses.is_user_owner.return_value = False

    mock_repo.update_task.side_effect = Exception("DB error")

    data = {"title": "new title"}

    response = service.update_task("task123", data, "user123")
    assert response["code_status"] == 500
    assert "An error occurred while updating the task" in response["response"].get_json()["detail"]
    mock_logger.error.assert_called_once()

def test_delete_task_not_found(service, mock_repo):
    mock_repo.get_tasks_by_query.return_value = []
    response = service.delete_task("task123", "user123")
    assert response["code_status"] == 404
    assert "The specified task does not exist" in response["response"].get_json()["detail"]

def test_delete_task_no_permissions(service, mock_repo, mock_user_service, mock_repository_courses):
    task = build_task_mock()
    mock_repo.get_tasks_by_query.return_value = [task]
    mock_user_service.check_assistants_permissions.return_value = False
    mock_repository_courses.is_user_owner.return_value = False

    response = service.delete_task("task123", "user123")
    assert response["code_status"] == 403
    assert "not allowed" in response["response"].get_json()["detail"]

def test_delete_task_success(service, mock_repo, mock_user_service, mock_repository_courses):
    task = build_task_mock()
    mock_repo.get_tasks_by_query.return_value = [task]
    mock_user_service.check_assistants_permissions.return_value = True
    mock_repository_courses.is_user_owner.return_value = False

    mock_repo.delete_task.return_value = True

    response = service.delete_task("task123", "user123")
    assert response["code_status"] == 200
    assert response["response"]["title"] == "Task deleted"
    mock_repo.delete_task.assert_called_once_with("task123")

def test_delete_task_repo_fail(service, mock_repo, mock_user_service, mock_repository_courses):
    task = build_task_mock()
    mock_repo.get_tasks_by_query.return_value = [task]
    mock_user_service.check_assistants_permissions.return_value = True
    mock_repository_courses.is_user_owner.return_value = True

    mock_repo.delete_task.return_value = False

    response = service.delete_task("task123", "user123")
    assert response["code_status"] == 400
    assert "The task could not be deleted" in response["response"].get_json()["detail"]

def test_delete_task_exception(service, mock_repo, mock_user_service, mock_repository_courses, mock_logger):
    task = build_task_mock()
    mock_repo.get_tasks_by_query.return_value = [task]
    mock_user_service.check_assistants_permissions.return_value = True
    mock_repository_courses.is_user_owner.return_value = True

    mock_repo.delete_task.side_effect = Exception("DB error")

    response = service.delete_task("task123", "user123")
    assert response["code_status"] == 500
    assert "An error occurred while deleting the task" in response["response"].get_json()["detail"]
    mock_logger.error.assert_called_once()

@pytest.mark.parametrize("status", [s.value for s in TaskStatus])
def test_get_tasks_by_course_success(service, mock_repo, mock_course_service, status):
    mock_course_service.get_course_by_id.return_value = {"code_status": 200}
    task = build_task_mock(status=TaskStatus(status))
    mock_repo.get_tasks_by_query.return_value = [task]

    response = service.get_tasks_by_course("course123", status=status)

    assert response["code_status"] == 200
    assert isinstance(response["response"], list)
    assert response["response"][0]["status"] == status
    mock_repo.get_tasks_by_query.assert_called_once()
    query_passed = mock_repo.get_tasks_by_query.call_args[0][0]
    assert query_passed["course_id"] == "course123"
    assert query_passed["status"] == status

def test_get_tasks_by_course_invalid_status(service, mock_course_service):
    mock_course_service.get_course_by_id.return_value = {"code_status": 200}

    response = service.get_tasks_by_course("course123", status="invalid_status")

    assert response["code_status"] == 400
    assert "Invalid status" in response["response"].get_json()["title"]

def test_get_tasks_by_course_course_not_found(service, mock_course_service):
    mock_course_service.get_course_by_id.return_value = {"code_status": 404}

    response = service.get_tasks_by_course("course123")

    assert response["code_status"] == 404
    assert "Course not found" in response["response"].get_json()["detail"]

def test_get_tasks_by_course_exception(service, mock_course_service, mock_repo, mock_logger):
    mock_course_service.get_course_by_id.return_value = {"code_status": 200}
    mock_repo.get_tasks_by_query.side_effect = Exception("DB error")

    response = service.get_tasks_by_course("course123")

    assert response["code_status"] == 500
    assert "An error occurred while getting tasks" in response["response"].get_json()["detail"]
    mock_logger.error.assert_called_once()

def test_get_task_by_id_success(service, mock_repo):
    task = build_task_mock()
    mock_repo.get_tasks_by_query.return_value = [task]

    response = service.get_task_by_id("task123")

    assert response["code_status"] == 200
    assert response["response"]["_id"] == "task123"
    mock_repo.get_tasks_by_query.assert_called_once_with({"_id": "task123"})

def test_get_task_by_id_not_found(service, mock_repo):
    mock_repo.get_tasks_by_query.return_value = []

    response = service.get_task_by_id("task123")

    assert response["code_status"] == 404
    assert "The specified task does not exist" in response["response"].get_json()["detail"]

def test_get_task_by_id_exception(service, mock_repo, mock_logger):
    mock_repo.get_tasks_by_query.side_effect = Exception("DB error")

    response = service.get_task_by_id("task123")

    assert response["code_status"] == 500
    assert "An error occurred while getting the task" in response["response"].get_json()["detail"]
    mock_logger.error.assert_called_once()

def test_submit_task(service, mock_repo):
    
    service.repository.add_task_submission.return_value = True

    result = service.submit_task("task123", "student123", ["file1.pdf"])
    assert result is True
    service.repository.add_task_submission.assert_called_once_with("task123", "student123", ["file1.pdf"])

def test_upload_task_calls_upload_element(service):
    
    service._upload_element = MagicMock(return_value="http://file.url")

    result = service.upload_task("uuid123", 1, MagicMock(filename="file.pdf"))
    assert result == "http://file.url"
    service._upload_element.assert_called_once()

def test_upload_element_raises_if_no_filename(service):
    file_mock = MagicMock(filename="")
    with pytest.raises(FileNotFoundError):
        service._upload_element("uuid", 1, file_mock)

@patch("src.services.task_service.storage")  # Ajustá el path al que uses
@patch("src.services.task_service.os")
def test_save_file_generates_signed_url(mock_os, mock_storage, service):
    file_mock = MagicMock()
    file_mock.filename = "file.pdf"
    file_mock.content_type = "application/pdf"

    mock_blob = MagicMock()
    mock_blob.generate_signed_url.return_value = "http://signed-url"
    mock_blob.upload_from_file.return_value = None

    mock_bucket = MagicMock()
    mock_bucket.blob.return_value = mock_blob
    service._get_gcp_bucket = MagicMock(return_value=mock_bucket)

    url = service._save_file("uuid", 1, file_mock)

    assert url == "http://signed-url"
    mock_bucket.blob.assert_called_once()
    mock_blob.upload_from_file.assert_called_once_with(file_mock, content_type="application/pdf")

def test_get_tasks_by_teacher_success(service):
    
    course1 = MagicMock(_id="c1")
    course2 = MagicMock(_id="c2")
    service.course_service.get_courses_owned_by_user.return_value = [course1, course2]
    service.repository.get_tasks_by_course_ids.return_value = ["task1", "task2"]

    result = service.get_tasks_by_teacher("teacher123")

    assert result == ["task1", "task2"]
    service.repository.get_tasks_by_course_ids.assert_called_once()

def test_get_tasks_by_teacher_no_courses(service):
    
    service.course_service.get_courses_owned_by_user.return_value = []

    result = service.get_tasks_by_teacher("teacher123")

    assert result == []
    service.logger.info.assert_called_once()

def test_get_tasks_by_teacher_exception(service):
    
    service.course_service.get_courses_owned_by_user.side_effect = Exception("Fail")

    with pytest.raises(Exception):
        service.get_tasks_by_teacher("teacher123")
    service.logger.error.assert_called_once()

def test_get_tasks_by_student_success(service):
    
    course1 = MagicMock(_id="c1")
    service.course_service.get_courses_by_student_id.return_value = [course1]

    task1 = MagicMock()
    service.repository.get_tasks_by_course_ids.return_value = [task1]

    service._calculate_status = MagicMock(return_value="pending")
    service._get_submission = MagicMock(return_value=["sub1"])

    result = service.get_tasks_by_student("student123")

    assert len(result) == 1
    assert task1.status == "pending"
    assert task1.submissions == ["sub1"]

def test_get_tasks_by_student_with_course_filter(service):
    
    course1 = MagicMock(_id="c1")
    service.course_service.get_courses_by_student_id.return_value = [course1]

    service.repository.get_tasks_by_course_ids.return_value = []

    result = service.get_tasks_by_student("student123", course_id="c1")

    assert result == []

def test_get_tasks_by_student_no_courses(service):
    
    service.course_service.get_courses_by_student_id.return_value = []

    result = service.get_tasks_by_student("student123")

    assert result == []

def test_get_tasks_by_student_exception(service):
    
    service.course_service.get_courses_by_student_id.side_effect = Exception("Fail")

    with pytest.raises(Exception):
        service.get_tasks_by_student("student123")
    service.logger.error.assert_called_once()

@patch("src.services.task_service.parse_to_timestamp_ms_now")
def test_calculate_status_completed(mock_now, service):
    task = MagicMock()
    task.submissions = {"student123": "submission_data"}
    task.due_date = 9999999999999  # dummy

    status = service._calculate_status(task, "student123")
    assert status == TaskStatus.COMPLETED


@patch("src.services.task_service.parse_to_timestamp_ms_now")
def test_calculate_status_overdue(mock_now, service):
    mock_now.return_value = 2000
    task = MagicMock()
    task.submissions = {}
    task.due_date = 1000

    status = service._calculate_status(task, "student123")
    assert status == TaskStatus.OVERDUE


@patch("src.services.task_service.parse_to_timestamp_ms_now")
def test_calculate_status_pending(mock_now, service):
    mock_now.return_value = 1000
    task = MagicMock()
    task.submissions = {}
    task.due_date = 2000

    status = service._calculate_status(task, "student123")
    assert status == TaskStatus.PENDING

def test_get_submission_found(service):
    task = MagicMock()
    task.submissions = {"student123": {"data": "value"}}

    result = service._get_submission(task, "student123")
    assert result == {"student123": {"data": "value"}}

def test_get_submission_not_found(service):
    task = MagicMock()
    task.submissions = {}

    result = service._get_submission(task, "student123")
    assert result == {}

def test_add_feedback_success(service):
    task_id = "task123"
    student_id = "student123"
    corrector_id = "corrector456"

    submission_mock = MagicMock()
    submission_mock.feedbacks = {}

    task_mock = MagicMock()
    task_mock.submissions = {student_id: submission_mock}
    
    repo = service.repository
    repo.get_tasks_by_query = MagicMock(return_value=[task_mock])
    repo.update_task = MagicMock(return_value=MagicMock(to_dict=lambda: {"ok": True}))

    result = service.add_or_update_feedback(task_id, student_id, corrector_id, 9.5, "Buen trabajo")

    assert result["code_status"] == 200
    assert result["response"].json["ok"] == True

def test_add_feedback_task_not_found(service):
    service.repository.get_tasks_by_query = MagicMock(return_value=[])

    result = service.add_or_update_feedback("taskX", "studentX", "correctorX", 8.0, "Comentario")

    assert result["code_status"] == 404
    assert "Task not found" in result["response"].get_json()["title"]

def test_add_feedback_submission_missing(service):
    task_mock = MagicMock()
    task_mock.submissions = {}  # No submission

    service.repository.get_tasks_by_query = MagicMock(return_value=[task_mock])

    result = service.add_or_update_feedback("taskX", "studentX", "correctorX", 8.0, "Comentario")

    assert result["code_status"] == 404
    assert "Submission not found" in result["response"].get_json()["title"]

def test_add_feedback_existing_corrector_mismatch(service):
    feedback_mock = MagicMock()
    submission_mock = MagicMock()
    submission_mock.feedbacks = {"old_corrector": feedback_mock}

    task_mock = MagicMock()
    task_mock.submissions = {"studentX": submission_mock}

    service.repository.get_tasks_by_query = MagicMock(return_value=[task_mock])

    result = service.add_or_update_feedback("taskX", "studentX", "new_corrector", 9.0, "comentario")

    assert result["code_status"] == 400
    assert "Invalid corrector change" in result["response"].get_json()["title"]

def test_add_feedback_update_fails(service):
    task_id = "taskX"
    student_id = "studentX"
    corrector_id = "correctorX"

    submission_mock = MagicMock()
    submission_mock.feedbacks = {}

    task_mock = MagicMock()
    task_mock.submissions = {student_id: submission_mock}

    service.repository.get_tasks_by_query = MagicMock(return_value=[task_mock])
    service.repository.update_task = MagicMock(return_value=None)  # Simula fallo

    result = service.add_or_update_feedback(task_id, student_id, corrector_id, 9.0, "Comentario")

    assert result["code_status"] == 500
    assert "Update failed" in result["response"].get_json()["title"]

def test_add_feedback_unassign_corrector(service):
    task_id = "taskX"
    student_id = "studentX"
    existing_corrector_id = "correctorOld"

    feedback_mock = MagicMock()
    submission_mock = MagicMock()
    submission_mock.feedbacks = {existing_corrector_id: feedback_mock}

    task_mock = MagicMock()
    task_mock.submissions = {student_id: submission_mock}

    service.repository.get_tasks_by_query = MagicMock(return_value=[task_mock])
    service.repository.update_task = MagicMock(return_value=MagicMock(to_dict=lambda: {"ok": True}))

    result = service.add_or_update_feedback(task_id, student_id, corrector_id=None)

    service.repository.update_task.assert_called_once()
    assert "$unset" in list(service.repository.update_task.call_args[0][1].keys())[0]
    assert result["code_status"] == 200
