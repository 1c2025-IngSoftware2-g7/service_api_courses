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
def mock_course_repo():
    return MagicMock()

@pytest.fixture
def mock_user_repo():
    return MagicMock()

@pytest.fixture
def mock_logger():
    return MagicMock()

@pytest.fixture
def service(mock_course_repo, mock_user_repo, mock_logger):
    from src.services.enrollment_service import EnrollmentService
    return EnrollmentService(mock_course_repo, mock_user_repo, mock_logger)

def test_enroll_success(service, mock_course_repo, mock_user_repo):
    mock_course_repo.check_if_course_inscription_is_available.return_value = True
    mock_course_repo.is_student_enrolled_in_course.return_value = False
    mock_course_repo.check_if_course_has_place_to_enroll.return_value = True
    mock_course_repo.get_course_correlatives.return_value = ["math1", "physics1"]
    mock_user_repo.get_student_approved_courses.return_value = ["math1", "physics1"]
    mock_course_repo.enroll_student_in_course.return_value = True

    response = service.enroll_student_in_course("course1", "student1")

    assert response["code_status"] == 200
    assert response["response"]["student_id"] == "student1"

def test_enroll_inscription_closed(service, mock_course_repo):
    mock_course_repo.check_if_course_inscription_is_available.return_value = False

    response = service.enroll_student_in_course("course1", "student1")

    assert response["code_status"] == 403
    assert "inscription is no longer available" in response["response"].get_json()["detail"]

def test_enroll_student_already_enrolled(service, mock_course_repo):
    mock_course_repo.check_if_course_inscription_is_available.return_value = True
    mock_course_repo.is_student_enrolled_in_course.return_value = True

    response = service.enroll_student_in_course("course1", "student1")

    assert response["code_status"] == 403
    assert "already enrolled" in response["response"].get_json()["detail"]

def test_enroll_course_full(service, mock_course_repo):
    mock_course_repo.check_if_course_inscription_is_available.return_value = True
    mock_course_repo.is_student_enrolled_in_course.return_value = False
    mock_course_repo.check_if_course_has_place_to_enroll.return_value = False

    response = service.enroll_student_in_course("course1", "student1")

    assert response["code_status"] == 403
    assert "is full" in response["response"].get_json()["detail"]

def test_enroll_course_already_approved(service, mock_course_repo, mock_user_repo):
    mock_course_repo.check_if_course_inscription_is_available.return_value = True
    mock_course_repo.is_student_enrolled_in_course.return_value = False
    mock_course_repo.check_if_course_has_place_to_enroll.return_value = True
    mock_course_repo.get_course_correlatives.return_value = []
    mock_user_repo.get_student_approved_courses.return_value = ["course1"]

    response = service.enroll_student_in_course("course1", "student1")

    assert response["code_status"] == 403
    assert "already has approved course" in response["response"].get_json()["detail"]

def test_enroll_missing_correlatives(service, mock_course_repo, mock_user_repo):
    mock_course_repo.check_if_course_inscription_is_available.return_value = True
    mock_course_repo.is_student_enrolled_in_course.return_value = False
    mock_course_repo.check_if_course_has_place_to_enroll.return_value = True
    mock_course_repo.get_course_correlatives.return_value = ["math1"]
    mock_user_repo.get_student_approved_courses.return_value = []

    response = service.enroll_student_in_course("course1", "student1")

    assert response["code_status"] == 403
    assert "does not have the correlatives" in response["response"].get_json()["detail"]

def test_enroll_internal_error(service, mock_course_repo):
    mock_course_repo.check_if_course_inscription_is_available.side_effect = Exception("DB down")

    response = service.enroll_student_in_course("course1", "student1")

    assert response["code_status"] == 500
    assert "An error occurred while enrolling the student" in response["response"].get_json()["detail"]

def test_get_enrolled_courses_success(service, mock_course_repo):
    mock_course_repo.get_enrolled_courses.return_value = [{
        "course_name": "Math 101",
        "course_description": "Basic Math",
        "max_students": 30,
        "course_start_date": "2024-01-01",
        "course_end_date": "2024-06-01",
        "creator_id": "teacher123",
        "creator_name": "Prof. X",
        "students": [],
        "_id": "id",
        "modules": [],
        "enroll_date_start": "2024-01-01",
        "enroll_date_end": "2024-01-10",
        "assistants": [],
        "correlatives_required_id": [],
        "background": "blue"
    }]

    response = service.get_enrolled_courses("student1")
    assert response["code_status"] == 200
    assert isinstance(response["response"], list)

def test_get_enrolled_courses_not_found(service, mock_course_repo):
    mock_course_repo.get_enrolled_courses.return_value = []

    response = service.get_enrolled_courses("student1")

    assert response["code_status"] == 404
    assert "No courses found" in response["response"].get_json()["detail"]

def test_get_enrolled_courses_internal_error(service, mock_course_repo):
    mock_course_repo.get_enrolled_courses.side_effect = Exception("db error")

    response = service.get_enrolled_courses("student1")

    assert response["code_status"] == 500
    assert "An error occurred while getting the enrolled courses" in response["response"].get_json()["detail"]
