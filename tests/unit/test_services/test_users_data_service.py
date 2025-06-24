import pytest
from flask import Flask
from unittest.mock import patch, MagicMock

from src.headers import ASSISTANT_ALREADY_EXISTS, ASSISTANT_ERROR, COURSE_NOT_FOUND, MISSING_FIELDS

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
def repository_mock():
    return MagicMock()

@pytest.fixture
def course_service_mock():
    return MagicMock()

@pytest.fixture
def logger_mock():
    return MagicMock()

@pytest.fixture
def service(repository_mock, course_service_mock, logger_mock):
    from src.services.users_data_service import UsersDataService
    return UsersDataService(repository_mock, course_service_mock, logger_mock)

def test_set_favourite_course_success(service, repository_mock, course_service_mock):
    course_service_mock.get_course.return_value = {"code_status": 200}
    repository_mock.course_already_favourite.return_value = False

    result = service.set_favourite_course_for_student("course123", "student123")

    assert result["code_status"] == 200
    assert "Student with ID student123 now has as favourite the course course123" in result["response"]["detail"]
    repository_mock.set_favourite_course.assert_called_once_with("course123", "student123")

def test_set_favourite_course_not_found(service, course_service_mock):
    course_service_mock.get_course.return_value = {"code_status": 404}

    result = service.set_favourite_course_for_student("invalid_course", "student123")

    assert result["code_status"] == 404
    assert result["response"].get_json()["title"] == "Course not found"

def test_set_favourite_course_already_in_favourites(service, course_service_mock, repository_mock):
    course_service_mock.get_course.return_value = {"code_status": 200}
    repository_mock.course_already_favourite.return_value = True

    result = service.set_favourite_course_for_student("course123", "student123")

    assert result["code_status"] == 400
    assert result["response"].get_json()["title"] == "Course already in favourites"

def test_remove_course_from_favourites_success(service, course_service_mock, repository_mock):
    course_service_mock.get_course.return_value = {"code_status": 200}
    repository_mock.course_already_favourite.return_value = True

    result = service.remove_course_from_favourites("course123", "student123")

    assert result["code_status"] == 200
    assert "removed the course id: course123 as favourites" in result["response"]["detail"]
    repository_mock.remove_course_from_favourites.assert_called_once_with("course123", "student123")

def test_remove_course_from_favourites_course_not_found(service, course_service_mock):
    course_service_mock.get_course.return_value = {"code_status": 404}

    result = service.remove_course_from_favourites("invalid_course", "student123")

    assert result["code_status"] == 404
    assert result["response"].get_json()["title"] == "Course not found"

def test_remove_course_not_in_favourites(service, course_service_mock, repository_mock):
    course_service_mock.get_course.return_value = {"code_status": 200}
    repository_mock.course_already_favourite.return_value = False

    result = service.remove_course_from_favourites("course123", "student123")

    assert result["code_status"] == 400
    assert result["response"].get_json()["title"] == "Course not in favourites"

def test_get_favourites_success(service, repository_mock, course_service_mock):
    repository_mock.get_favourites_from_student_id.return_value = ["course1", "course2"]
    course_service_mock.get_course_by_id.side_effect = [
        {"code_status": 200, "response": {"id": "course1"}},
        {"code_status": 200, "response": {"id": "course2"}}
    ]

    result = service.get_favourites_from_student_id("student123", offset=0, max_per_page=10)

    assert result["code_status"] == 200
    assert len(result["response"]) == 2
    assert result["response"][0]["id"] == "course1"
    assert result["response"][1]["id"] == "course2"

def test_get_favourites_no_favourites(service, repository_mock):
    repository_mock.get_favourites_from_student_id.return_value = []

    result = service.get_favourites_from_student_id("student123", 0, 10)

    assert result["code_status"] == 404
    assert result["response"].get_json()["title"] == "Missing required field(s)"

def test_get_favourites_course_data_missing(service, repository_mock, course_service_mock):
    repository_mock.get_favourites_from_student_id.return_value = ["courseX"]
    course_service_mock.get_course_by_id.return_value = {"code_status": 404}

    result = service.get_favourites_from_student_id("student123", 0, 10)

    assert result["code_status"] == 404
    assert result["response"].get_json()["title"] == "Course not found"

def test_search_favourite_courses_success(service, mocker):
    mock_courses = [
        {
            "id": "course1",
            "name": "Python for Beginners",
            "description": "Learn Python",
            "creator_name": "Alice"
        },
        {
            "id": "course2",
            "name": "Advanced Java",
            "description": "Deep dive into Java",
            "creator_name": "Bob"
        },
    ]
    mock_response = {"code_status": 200, "response": mock_courses}
    mocker.patch.object(service, "get_favourites_from_student_id", return_value=mock_response)

    result = service.search_favourite_courses("student123", query="python", offset=0, max_per_page=10)

    assert result["code_status"] == 200
    assert len(result["response"]) == 1
    assert result["response"][0]["name"] == "Python for Beginners"

def test_search_favourite_courses_no_favourites(service, mocker):
    mocker.patch.object(service, "get_favourites_from_student_id", return_value=None)

    result = service.search_favourite_courses("student123", "anything", 0, 10)

    assert result["code_status"] == 404
    assert result["response"].get_json()["title"] == "Missing required field(s)"

def test_approve_student_success(service, course_service_mock, repository_mock):
    course_service_mock.get_students_in_course.return_value = {
        "code_status": 200,
        "response": ["student123"]
    }
    repository_mock.check_student_enrollment.return_value = True

    result = service.approve_student_in_course("course123", "student123", 90)

    assert result["code_status"] == 200
    assert result["response"]["title"] == "Student Approved"
    repository_mock.approve_student.assert_called_once_with("course123", "student123", 90)
    course_service_mock.remove_student_from_course.assert_called_once_with("course123", "student123")

def test_approve_student_course_not_found(service, course_service_mock):
    course_service_mock.get_students_in_course.return_value = {"code_status": 404}

    result = service.approve_student_in_course("courseX", "student123", 100)

    assert result["code_status"] == 404
    assert result["response"].get_json()["title"] == "Course not found"

def test_approve_student_not_enrolled(service, course_service_mock, repository_mock):
    course_service_mock.get_students_in_course.return_value = {
        "code_status": 200,
        "response": ["other_student"]
    }
    repository_mock.check_student_enrollment.return_value = False

    result = service.approve_student_in_course("course123", "student123", 60)

    assert result["code_status"] == 400
    assert result["response"].get_json()["title"] == "User not enrolled into the course"

def test_approve_student_id_not_in_course(service, course_service_mock, repository_mock):
    course_service_mock.get_students_in_course.return_value = {
        "code_status": 200,
        "response": ["other_student"]
    }
    repository_mock.check_student_enrollment.return_value = True

    result = service.approve_student_in_course("course123", "student123", 70)

    assert result["code_status"] == 404
    assert result["response"].get_json()["title"] == "Missing required field(s)"


def test_get_approved_signatures_success(service, repository_mock):
    repository_mock.get_approved_signatures.return_value = ["SIG1", "SIG2"]

    result = service.get_approved_signatures_from_user_id("student123")

    assert result["code_status"] == 200
    assert result["response"] == ["SIG1", "SIG2"]

def test_get_approved_signatures_empty(service, repository_mock):
    repository_mock.get_approved_signatures.return_value = []

    result = service.get_approved_signatures_from_user_id("student123")

    assert result["code_status"] == 404
    assert result["response"].get_json()["title"] == MISSING_FIELDS

def test_add_assistant_success(service, repository_mock, course_service_mock):
    course_service_mock.is_user_owner_of_course.return_value = True
    course_service_mock.get_course.return_value = {"code_status": 200}
    repository_mock.check_assistant_already_in_course.return_value = False
    course_service_mock.add_assistant_to_course.return_value = {"code_status": 200}

    data = {
        "permissions": {
            "can_grade": True,
            "can_edit": False,
        }
    }

    result = service.add_assistant_to_course("course1", "assistant1", "owner1", data)

    assert result["code_status"] == 200
    assert result["response"]["title"] == "Assistant Added"
    repository_mock.add_assistant_to_course.assert_called_once()

def test_add_assistant_not_owner(service, course_service_mock):
    course_service_mock.is_user_owner_of_course.return_value = False

    result = service.add_assistant_to_course(
        "course1", "assistant1", "owner1", {"permissions": {}}
    )

    assert result["code_status"] == 403
    assert result["response"].get_json()["title"] == MISSING_FIELDS

def test_add_assistant_course_not_found(service, course_service_mock):
    course_service_mock.is_user_owner_of_course.return_value = True
    course_service_mock.get_course.return_value = {"code_status": 404}

    result = service.add_assistant_to_course(
        "course1", "assistant1", "owner1", {"permissions": {}}
    )

    assert result["code_status"] == 404
    assert result["response"].get_json()["title"] == COURSE_NOT_FOUND

def test_add_assistant_already_exists(service, course_service_mock, repository_mock):
    course_service_mock.is_user_owner_of_course.return_value = True
    course_service_mock.get_course.return_value = {"code_status": 200}
    repository_mock.check_assistant_already_in_course.return_value = True

    result = service.add_assistant_to_course(
        "course1", "assistant1", "owner1", {"permissions": {}}
    )

    assert result["code_status"] == 409
    assert result["response"].get_json()["title"] == ASSISTANT_ALREADY_EXISTS

def test_add_assistant_error_in_course_update(service, course_service_mock, repository_mock):
    course_service_mock.is_user_owner_of_course.return_value = True
    course_service_mock.get_course.return_value = {"code_status": 200}
    repository_mock.check_assistant_already_in_course.return_value = False
    course_service_mock.add_assistant_to_course.return_value = {"code_status": 500}

    result = service.add_assistant_to_course(
        "course1", "assistant1", "owner1", {"permissions": {}}
    )

    assert result["code_status"] == 500
    assert result["response"].get_json()["title"] == ASSISTANT_ERROR

def test_add_assistant_with_invalid_permissions(service, course_service_mock, repository_mock, mocker):
    course_service_mock.is_user_owner_of_course.return_value = True
    course_service_mock.get_course.return_value = {"code_status": 200}
    repository_mock.check_assistant_already_in_course.return_value = False
    course_service_mock.add_assistant_to_course.return_value = {"code_status": 200}

    # Spy sobre el método set_permission para ver si se llama
    spy = mocker.spy(service, "add_assistant_to_course")

    data = {
        "permissions": {
            "invalid_permission_1": True,
            "invalid_permission_2": True,
        }
    }

    result = service.add_assistant_to_course("course1", "assistant1", "owner1", data)

    assert result["code_status"] == 200
    repository_mock.add_assistant_to_course.assert_called_once()

    # Si se usan permisos inválidos, el diccionario de permisos debería estar vacío
    args, kwargs = repository_mock.add_assistant_to_course.call_args
    added_permissions = args[2]
    assert all(value is False for value in added_permissions.values())

def test_add_assistant_with_no_permissions(service, course_service_mock, repository_mock):
    course_service_mock.is_user_owner_of_course.return_value = True
    course_service_mock.get_course.return_value = {"code_status": 200}
    repository_mock.check_assistant_already_in_course.return_value = False
    course_service_mock.add_assistant_to_course.return_value = {"code_status": 200}

    data = {
        "permissions": {}
    }

    result = service.add_assistant_to_course("course1", "assistant1", "owner1", data)

    assert result["code_status"] == 200

    args, kwargs = repository_mock.add_assistant_to_course.call_args
    permissions_dict = args[2]
    assert isinstance(permissions_dict, dict)
    assert all(v is False for v in permissions_dict.values())

def test_modify_assistant_permissions_success(service, course_service_mock, repository_mock):
    course_service_mock.is_user_owner_of_course.return_value = True
    course_service_mock.get_course.return_value = {"code_status": 200}
    repository_mock.check_assistant_already_in_course.return_value = True
    repository_mock.get_assistant_permissions_for_course.return_value = {
        "can_grade": True,
        "can_edit": False,
    }
    repository_mock.update_assistant_permissions.return_value = True

    data = {"permissions": {"can_grade": False}}

    result = service.modify_assistant_permissions("course1", "assistant1", "owner1", data)

    assert result["code_status"] == 200
    repository_mock.update_assistant_permissions.assert_called_once()

def test_modify_assistant_permissions_not_owner(service, course_service_mock):
    course_service_mock.is_user_owner_of_course.return_value = False

    result = service.modify_assistant_permissions("course1", "assistant1", "owner1", {"permissions": {}})

    assert result["code_status"] == 403
    assert "not the owner" in result["response"].get_json()["detail"].lower()

def test_modify_assistant_permissions_course_not_found(service, course_service_mock):
    course_service_mock.is_user_owner_of_course.return_value = True
    course_service_mock.get_course.return_value = {"code_status": 404}

    result = service.modify_assistant_permissions("course1", "assistant1", "owner1", {"permissions": {}})

    assert result["code_status"] == 404
    assert "course id not found" in result["response"].get_json()["detail"].lower()

def test_modify_assistant_permissions_assistant_not_in_course(service, course_service_mock, repository_mock):
    course_service_mock.is_user_owner_of_course.return_value = True
    course_service_mock.get_course.return_value = {"code_status": 200}
    repository_mock.check_assistant_already_in_course.return_value = False

    result = service.modify_assistant_permissions("course1", "assistant1", "owner1", {"permissions": {}})

    assert result["code_status"] == 404
    assert "assistant doesn't exist" in result["response"].get_json()["detail"].lower()

def test_modify_assistant_permissions_assistant_perms_not_found(service, course_service_mock, repository_mock):
    course_service_mock.is_user_owner_of_course.return_value = True
    course_service_mock.get_course.return_value = {"code_status": 200}
    repository_mock.check_assistant_already_in_course.return_value = True
    repository_mock.get_assistant_permissions_for_course.return_value = None

    result = service.modify_assistant_permissions("course1", "assistant1", "owner1", {"permissions": {}})

    assert result["code_status"] == 404
    assert "assistant not found" in result["response"].get_json()["detail"].lower()

def test_modify_assistant_permissions_invalid_permission(service, course_service_mock, repository_mock):
    course_service_mock.is_user_owner_of_course.return_value = True
    course_service_mock.get_course.return_value = {"code_status": 200}
    repository_mock.check_assistant_already_in_course.return_value = True
    repository_mock.get_assistant_permissions_for_course.return_value = {"can_grade": True}

    data = {"permissions": {"invalid_perm": True}}

    result = service.modify_assistant_permissions("course1", "assistant1", "owner1", data)

    assert result["code_status"] == 400
    assert "doesn't exist" in result["response"].get_json()["detail"].lower()

def test_modify_assistant_permissions_update_fails(service, course_service_mock, repository_mock):
    course_service_mock.is_user_owner_of_course.return_value = True
    course_service_mock.get_course.return_value = {"code_status": 200}
    repository_mock.check_assistant_already_in_course.return_value = True
    repository_mock.get_assistant_permissions_for_course.return_value = {"can_grade": True}
    repository_mock.update_assistant_permissions.return_value = False

    data = {"permissions": {"can_grade": False}}

    result = service.modify_assistant_permissions("course1", "assistant1", "owner1", data)

    assert result["code_status"] == 500
    assert "error modifying" in result["response"].get_json()["detail"].lower()

def test_remove_assistant_from_course_success(service, course_service_mock, repository_mock):
    course_service_mock.is_user_owner_of_course.return_value = True
    course_service_mock.get_course.return_value = {"code_status": 200}
    repository_mock.check_assistant_already_in_course.return_value = True
    course_service_mock.remove_assistant_from_course.return_value = {"code_status": 200}
    repository_mock.remove_assistant_from_course_with_id.return_value = True

    result = service.remove_assistant_from_course("course1", "assistant1", "owner1")

    assert result["code_status"] == 200
    repository_mock.remove_assistant_from_course_with_id.assert_called_once()

def test_remove_assistant_from_course_not_owner(service, course_service_mock):
    course_service_mock.is_user_owner_of_course.return_value = False

    result = service.remove_assistant_from_course("course1", "assistant1", "owner1")

    assert result["code_status"] == 403
    assert "not the owner" in result["response"].get_json()["detail"].lower()

def test_remove_assistant_from_course_course_not_found(service, course_service_mock):
    course_service_mock.is_user_owner_of_course.return_value = True
    course_service_mock.get_course.return_value = {"code_status": 404}

    result = service.remove_assistant_from_course("course1", "assistant1", "owner1")

    assert result["code_status"] == 404
    assert "course id not found" in result["response"].get_json()["detail"].lower()

def test_remove_assistant_from_course_assistant_not_in_course(service, course_service_mock, repository_mock):
    course_service_mock.is_user_owner_of_course.return_value = True
    course_service_mock.get_course.return_value = {"code_status": 200}
    repository_mock.check_assistant_already_in_course.return_value = False

    result = service.remove_assistant_from_course("course1", "assistant1", "owner1")

    assert result["code_status"] == 404
    assert "assistant doesn't exist" in result["response"].get_json()["detail"].lower()

def test_remove_assistant_from_course_remove_fails(service, course_service_mock, repository_mock):
    course_service_mock.is_user_owner_of_course.return_value = True
    course_service_mock.get_course.return_value = {"code_status": 200}
    repository_mock.check_assistant_already_in_course.return_value = True
    course_service_mock.remove_assistant_from_course.return_value = {"code_status": 500}

    result = service.remove_assistant_from_course("course1", "assistant1", "owner1")

    assert result["code_status"] == 500
    assert "error removing" in result["response"].get_json()["detail"].lower()

def test_remove_assistant_from_course_delete_fails(service, course_service_mock, repository_mock):
    course_service_mock.is_user_owner_of_course.return_value = True
    course_service_mock.get_course.return_value = {"code_status": 200}
    repository_mock.check_assistant_already_in_course.return_value = True
    course_service_mock.remove_assistant_from_course.return_value = {"code_status": 200}
    repository_mock.remove_assistant_from_course_with_id.return_value = False

    result = service.remove_assistant_from_course("course1", "assistant1", "owner1")

    assert result["code_status"] == 500
    assert "error removing" in result["response"].get_json()["detail"].lower()

def test_get_assistant_permissions_success(service, course_service_mock, repository_mock):
    course_service_mock.get_course.return_value = {"code_status": 200}
    repository_mock.get_assistant_permissions_for_course.return_value = {
        "can_grade": True,
        "can_edit": False,
    }

    result = service.get_assistant_permissions("course1", "assistant1")

    assert result["code_status"] == 200
    assert "can_grade" in result["response"]

def test_get_assistant_permissions_course_not_found(service, course_service_mock):
    course_service_mock.get_course.return_value = {"code_status": 404}

    result = service.get_assistant_permissions("course1", "assistant1")

    assert result["code_status"] == 404
    assert "course id not found" in result["response"].get_json()["detail"].lower()

def test_get_assistant_permissions_assistant_not_found(service, course_service_mock, repository_mock):
    course_service_mock.get_course.return_value = {"code_status": 200}
    repository_mock.get_assistant_permissions_for_course.return_value = None

    result = service.get_assistant_permissions("course1", "assistant1")

    assert result["code_status"] == 404
    assert "assistant not found" in result["response"].get_json()["detail"].lower()
