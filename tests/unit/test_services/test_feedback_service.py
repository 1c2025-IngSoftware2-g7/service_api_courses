import pytest
from flask import Flask
from unittest.mock import patch, MagicMock


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
def mock_service_courses():
    return MagicMock()

@pytest.fixture
def mock_service_users():
    return MagicMock()

@pytest.fixture
def mock_logger():
    return MagicMock()

@pytest.fixture
def service(mock_repo, mock_service_courses, mock_service_users, mock_logger):
    from src.services.feedback_service import FeedbackService
    return FeedbackService(
        repository_feedbacks=mock_repo,
        service_courses=mock_service_courses,
        service_users=mock_service_users,
        logger=mock_logger
    )

def test_create_course_feedback_success(service, mock_service_courses, mock_repo):
    mock_service_courses.get_course_by_id.return_value = {"code_status": 200}

    response = service.create_course_feedback("course1", "Great course!", 5)

    assert response["code_status"] == 201
    assert "created successfully" in response["response"]["detail"]
    mock_repo.insert_course_feedback.assert_called_once()

def test_create_course_feedback_course_not_found(service, mock_service_courses):
    mock_service_courses.get_course_by_id.return_value = {"code_status": 404}

    response = service.create_course_feedback("courseX", "Nice", 4)

    assert response["code_status"] == 404
    assert "Course not found" in response["response"].get_json()["detail"]

def test_create_course_feedback_exception(service, mock_service_courses):
    mock_service_courses.get_course_by_id.side_effect = Exception("Crash")

    response = service.create_course_feedback("courseX", "Nice", 4)

    assert response["code_status"] == 500
    assert "Internal server error" in response["response"].get_json()["title"]

def test_get_course_feedback_success(service, mock_service_courses, mock_repo):
    mock_service_courses.get_course_by_id.return_value = {"code_status": 200}
    mock_repo.get_course_feedback.return_value = [
        {"course_id": "course1", "feedback": "Nice", "rating": 5}
    ]

    response = service.get_course_feedback("course1")

    assert response["code_status"] == 200
    assert isinstance(response["response"], list)

def test_get_course_feedback_not_found(service, mock_service_courses):
    mock_service_courses.get_course_by_id.return_value = {"code_status": 404}

    response = service.get_course_feedback("invalid_course")

    assert response["code_status"] == 404
    assert "Course not found" in response["response"].get_json()["detail"]

def test_get_course_feedback_exception(service, mock_service_courses):
    mock_service_courses.get_course_by_id.side_effect = Exception("Boom")

    response = service.get_course_feedback("course1")

    assert response["code_status"] == 500
    assert "Internal server error" in response["response"].get_json()["title"]

def test_create_student_feedback_success(service, mock_service_courses, mock_service_users, mock_repo):
    mock_service_courses.is_user_owner_of_course.return_value = True
    mock_service_users.check_assistants_permissions.return_value = False

    response = service.create_student_feedback("student1", "course1", "teacher1", "Well done")

    assert response["code_status"] == 201
    assert "created successfully" in response["response"]["detail"]
    mock_repo.insert_student_feedback.assert_called_once()

def test_create_student_feedback_assistant_has_permission(service, mock_service_courses, mock_service_users, mock_repo):
    mock_service_courses.is_user_owner_of_course.return_value = False
    mock_service_users.check_assistants_permissions.return_value = True

    response = service.create_student_feedback("student1", "course1", "assistant1", "Well done")

    assert response["code_status"] == 201
    mock_repo.insert_student_feedback.assert_called_once()

def test_create_student_feedback_not_allowed(service, mock_service_courses, mock_service_users):
    mock_service_courses.is_user_owner_of_course.return_value = False
    mock_service_users.check_assistants_permissions.return_value = False

    response = service.create_student_feedback("student1", "course1", "userX", "Feedback")

    assert response["code_status"] == 403
    assert "not allowed" in response["response"].get_json()["detail"]

def test_create_student_feedback_exception(service, mock_service_courses):
    mock_service_courses.is_user_owner_of_course.side_effect = Exception("Fail")

    response = service.create_student_feedback("student1", "course1", "teacher1", "Feedback")

    assert response["code_status"] == 500
    assert "Internal server error" in response["response"].get_json()["title"]

def test_get_student_feedback_success(service, mock_service_courses, mock_repo):
    mock_service_courses.get_course_by_id.return_value = {"code_status": 200}
    mock_repo.get_student_feedback.return_value = [
        {"student_id": "student1", "course_id": "course1", "teacher_id": "teacher1", "feedback": "Great job"}
    ]

    response = service.get_student_feedback("student1", "course1")

    assert response["code_status"] == 200
    assert isinstance(response["response"], list)

def test_get_student_feedback_course_not_found(service, mock_service_courses):
    mock_service_courses.get_course_by_id.return_value = {"code_status": 404}

    response = service.get_student_feedback("student1", "invalid_course")

    assert response["code_status"] == 404
    assert "Course not found" in response["response"].get_json()["detail"]

def test_get_student_feedback_not_found(service, mock_service_courses, mock_repo):
    mock_service_courses.get_course_by_id.return_value = {"code_status": 200}
    mock_repo.get_student_feedback.return_value = []

    response = service.get_student_feedback("student1", "course1")

    assert response["code_status"] == 204
    assert [] in response["response"]

def test_get_student_feedback_exception(service, mock_service_courses):
    mock_service_courses.get_course_by_id.side_effect = Exception("Boom")

    response = service.get_student_feedback("student1", "course1")

    assert response["code_status"] == 500
    assert "Internal server error" in response["response"].get_json()["title"]
