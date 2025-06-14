import pytest
from flask import Flask
from unittest.mock import patch, MagicMock


@pytest.fixture(scope="session", autouse=True)
def patch_mongo():
    with patch("pymongo.MongoClient") as mock_client:
        mock_client.return_value = MagicMock()
        yield

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
    repo = MagicMock()
    repo.get_course_by_id.return_value = {
        "name": "Math 101",
        "description": "Algebra and geometry",
        "max_students": 30,
        "course_start_date": "2025-01-01",
        "course_end_date": "2025-06-01",
        "creator_id": "owner123",
        "creator_name": "Alice",
        "students": [],
        "_id": "course123",
        "modules": [],
        "enroll_date_start": "2024-12-01",
        "enroll_date_end": "2024-12-20",
        "assistants": [],
        "correlatives_required_id": [],
        "background": "blue",
    }
    return repo

@pytest.fixture
def mock_logger():
    return MagicMock()

@pytest.fixture
def service(mock_repo, mock_logger):
    from src.services.course_service import CourseService
    return CourseService(mock_repo, mock_logger)

@pytest.fixture
def mock_course():
    return {
        "course_name": "Test Course",
        "course_description": "Test Description",
        "max_students": 30,
        "course_start_date": "2025-01-01",
        "course_end_date": "2025-12-31",
        "creator_id": "owner123",
        "creator_name": "Test Owner",
        "students": [],
        "_id": "course123",
        "modules": [],
        "enroll_date_start": "2025-01-01",
        "enroll_date_end": "2025-06-01",
        "assistants": ["assistant123"],
        "correlatives_required_id": [],
        "background": "blue",
    }

# -------- create_course --------
def test_create_course_missing_fields(service):
    data = {
        "name": "Math 101",
        "description": "Basic Math"
    }

    response = service.create_course(data)

    assert response["code_status"] == 400
    response_json = response["response"].get_json()
    assert "Field creator_id is required" in response_json["detail"]


def test_create_course_success(service, mock_repo):
    data = {
        "name": "Math 101",
        "description": "Basic Math",
        "creator_id": "user123",
        "creator_name": "Test",
        "course_start_date": "2025-01-01",
        "course_end_date": "2025-06-01",
        "max_students": 50
    }

    mock_repo.create_course.return_value = {"_id": "course123", **data}

    response = service.create_course(data)

    assert response["code_status"] == 201
    response_json = response["response"]
    assert response_json["data"]["_id"] == "course123"


def test_create_course_internal_error(service, mock_repo):
    data = {
        "name": "Math 101",
        "description": "Basic Math",
        "creator_id": "user123",
        "creator_name": "Test",
        "course_start_date": "2025-01-01",
        "course_end_date": "2025-06-01",
        "max_students": 50
    }

    mock_repo.create_course.side_effect = Exception("DB fail")

    response = service.create_course(data)

    assert response["code_status"] == 500
    response = response["response"].get_json()
    assert "DB fail" in response["detail"]


# -------- delete_course --------
def test_delete_course_success(service, mock_repo):
    mock_repo.delete_course.return_value = True

    response = service.delete_course("course123", "user123")

    assert response["code_status"] == 200
    assert "deleted successfully" in response["response"]["detail"]


def test_delete_course_not_found(service, mock_repo):
    mock_repo.delete_course.return_value = False

    response = service.delete_course("nonexistent_course", "user123")

    assert response["code_status"] == 404
    response = response["response"].get_json()
    assert "not found" in response["detail"]


def test_delete_course_internal_error(service, mock_repo):
    mock_repo.delete_course.side_effect = Exception("DB error")

    response = service.delete_course("course123", "user123")

    assert response["code_status"] == 500
    response = response["response"].get_json()
    assert "DB error" in response["detail"]


# -------- add_assistant_to_course --------
def test_add_assistant_to_course_success(service, mock_repo):
    mock_repo.add_assistant_to_course.return_value = True

    response = service.add_assistant_to_course("course123", "assistant123", "owner123")

    assert response["code_status"] == 200
    assert "Assistant with ID assistant123 added to course" in response["response"]["detail"]


def test_add_assistant_to_course_course_not_found(service, mock_repo):
    mock_repo.add_assistant_to_course.return_value = False

    response = service.add_assistant_to_course("courseNOTFOUND", "assistant123", "owner123")

    assert response["code_status"] == 404
    response = response["response"].get_json()
    assert "not found" in response["detail"]


def test_add_assistant_to_course_internal_error(service, mock_repo):
    mock_repo.add_assistant_to_course.side_effect = Exception("DB error")
    
    with pytest.raises(Exception) as exc_info:
        service.add_assistant_to_course("course123", "assistant123", "owner123")

    assert str(exc_info.value) == "DB error"


# -------- remove_assistant --------
def test_remove_assistant_success(service, mock_repo, mock_course):
    mock_repo.get_course_by_id.return_value = mock_course
    mock_repo.remove_assistant.return_value = True

    response = service.remove_assistant_from_course("course123", "assistant123", "owner123")

    assert response["code_status"] == 200
    assert "Assistant with ID assistant123 removed from course with ID course123" in response["response"]["detail"]


def test_remove_assistant_not_found(service, mock_repo):
    mock_repo.remove_assistant.return_value = False

    response = service.remove_assistant_from_course("course123", "assistant123", "owner123")

    assert response["code_status"] == 400
    response = response["response"].get_json()
    assert "User is not an assistant" in response["detail"]


def test_remove_assistant_internal_error(service, mock_repo, mock_course):
    mock_repo.get_course_by_id.return_value = mock_course
    mock_repo.remove_assistant_from_course.side_effect = Exception("DB crash")

    response = service.remove_assistant_from_course("course123", "assistant123", "owner123")

    assert response["code_status"] == 500
    response = response["response"].get_json()
    assert "DB crash" in response["detail"]


# -------- get_all_courses --------
def test_get_all_courses_success(service, mock_repo):
    mock_repo.get_all_courses.return_value = [
        {"_id": "c1", "name": "Math"}, {"_id": "c2", "name": "Physics"}
    ]

    response = service.get_all_courses()

    assert response["code_status"] == 200
    assert isinstance(response["response"], list)
    assert len(response["response"]) == 2


def test_get_all_courses_internal_error(service, mock_repo):
    mock_repo.get_all_courses.side_effect = Exception("Read error")

    response = service.get_all_courses()

    assert response["code_status"] == 500
    response = response["response"].get_json()
    assert "Read error" in response["detail"]


# -------- get_specific_course --------
def test_get_specific_course_found(service, mock_repo):
    course_data = {"_id": "course123", "name": "Math"}
    mock_repo.get_course_by_id.return_value = course_data

    response = service.get_course_by_id("course123")

    assert response["code_status"] == 200
    assert response["response"]["_id"] == "course123"


def test_get_specific_course_not_found(service, mock_repo):
    mock_repo.get_course_by_id.return_value = None

    response = service.get_course_by_id("course123")

    assert response["code_status"] == 404
    response = response["response"].get_json()
    assert "not found" in response["detail"]


def test_get_specific_course_internal_error(service, mock_repo):
    mock_repo.get_course_by_id.side_effect = Exception("DB fail")

    response = service.get_course_by_id("course123")

    assert response["code_status"] == 500
    response = response["response"].get_json()
    assert "DB fail" in response["detail"]
