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

COURSE_ID = "course123"
MODULE_ID = "module123"
OWNER_ID = "owner123"
RESOURCE_ID = "resource123"

@pytest.fixture
def mock_dependencies():
    repo_modules = MagicMock()
    repo_courses = MagicMock()
    service_users = MagicMock()
    logger = MagicMock()
    return repo_modules, repo_courses, service_users, logger

@pytest.fixture
def module_service(mock_dependencies):
    from src.services.module_service import ModuleService
    return ModuleService(*mock_dependencies)

def test_get_modules_from_course_success(module_service, mock_dependencies):
    repo_modules, repo_courses, *_ = mock_dependencies
    repo_courses.get_course_by_id.return_value = {"_id": COURSE_ID}
    repo_modules.get_modules_from_course.return_value = [{"title": "Test Module"}]

    result = module_service.get_modules_from_course(COURSE_ID)

    assert result["code_status"] == 200
    assert "response" in result

def test_get_modules_from_course_not_found(module_service, mock_dependencies):
    repo_modules, repo_courses, *_ = mock_dependencies
    repo_courses.get_course_by_id.return_value = None

    result = module_service.get_modules_from_course(COURSE_ID)

    assert result["code_status"] == 404
    assert result["response"].get_json()["title"] == "Course not found"

def test_add_module_to_course_success(module_service, mock_dependencies):
    repo_modules, repo_courses, service_users, logger = mock_dependencies
    repo_courses.get_course_by_id.return_value = {"_id": COURSE_ID}
    repo_modules.get_modules_from_course.return_value = []
    repo_modules.add_module_to_course.return_value = MODULE_ID
    service_users.check_assistants_permissions.return_value = True

    data = {"title": "Module", "description": "Desc"}

    result = module_service.add_module_to_course(COURSE_ID, data, OWNER_ID)

    assert result["code_status"] == 200
    assert result["response"]["title"] == "Module created successfully"

def test_add_module_to_course_unauthorized(module_service, mock_dependencies):
    repo_modules, repo_courses, service_users, logger = mock_dependencies
    repo_courses.get_course_by_id.return_value = {"_id": COURSE_ID}
    service_users.check_assistants_permissions.return_value = False
    repo_courses.is_user_owner.return_value = False

    result = module_service.add_module_to_course(COURSE_ID, {"title": "X", "description": "Y"}, OWNER_ID)

    assert result["code_status"] == 403
    assert result["response"].get_json()["title"] == "User not allowed to create in this instance"

def test_modify_module_success(module_service, mock_dependencies):
    repo_modules, repo_courses, service_users, logger = mock_dependencies
    repo_courses.get_course_by_id.return_value = {"_id": COURSE_ID}
    repo_modules.get_module_by_id.return_value = {
        "id": MODULE_ID,
        "title": "Old Title",
        "description": "Old Desc",
        "position": 1,
        "resources": [],
    }
    service_users.check_assistants_permissions.return_value = True
    data = {"title": "New Title"}

    result = module_service.modify_module_in_course(COURSE_ID, MODULE_ID, OWNER_ID, data)

    assert result["code_status"] == 200
    assert result["response"]["title"] == "Module modified successfully"

def test_get_module_from_course_success(module_service, mock_dependencies):
    repo_modules, repo_courses, *_ = mock_dependencies
    repo_courses.get_course_by_id.return_value = True
    repo_modules.get_module_by_id.return_value = {"title": "Test"}

    result = module_service.get_module_from_course(COURSE_ID, MODULE_ID)

    assert result["code_status"] == 200
    assert "response" in result

def test_get_resource_from_module_not_found(module_service, mock_dependencies):
    repo_modules, repo_courses, *_ = mock_dependencies
    repo_courses.get_course_by_id.return_value = True
    repo_modules.get_module_by_id.return_value = True
    repo_modules.get_resource_from_module.return_value = None

    result = module_service.get_resource_from_module(COURSE_ID, MODULE_ID, RESOURCE_ID)

    assert result["code_status"] == 404

def test_add_resource_success(module_service, mock_dependencies):
    repo_modules, repo_courses, service_users, logger = mock_dependencies
    repo_courses.get_course_by_id.return_value = True
    repo_modules.get_module_by_id.return_value = True
    repo_modules.get_resources_from_module.return_value = []
    repo_modules.add_resource_to_module.return_value = RESOURCE_ID
    service_users.check_assistants_permissions.return_value = True

    data = {
        "title": "Res",
        "source": "http://example.com",
        "mimetype": "video/mp4"
    }

    result = module_service.add_resource_to_module(COURSE_ID, MODULE_ID, data, OWNER_ID)

    assert result["code_status"] == 200
    assert result["response"]["title"] == "Module created successfully"

def test_delete_resource_from_module_success(module_service, mock_dependencies):
    repo_modules, repo_courses, service_users, logger = mock_dependencies
    repo_courses.get_course_by_id.return_value = True
    repo_modules.get_module_by_id.return_value = True
    repo_modules.get_resource_from_module.return_value = True
    repo_modules.delete_resource_from_module.return_value = True
    service_users.check_assistants_permissions.return_value = True

    result = module_service.delete_resource_from_module(
        COURSE_ID, MODULE_ID, RESOURCE_ID, OWNER_ID
    )

    assert result["code_status"] == 200
    assert result["response"]["title"] == "Module removed successfully"
