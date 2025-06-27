import pytest
from unittest.mock import MagicMock
from bson import ObjectId
from src.repository.module_repository import ModuleRepository
from src.models.module import Module
from src.models.resource import Resource

ID = "6498ef1b9a8f4b1234567890"  # string hex de 24 caracteres
ID_OBJ = ObjectId(ID)
ID_2 = "6498ef1b9a8f4b1234567880"  # string hex de 24 caracteres
ID_OBJ_2 = ObjectId(ID)

@pytest.fixture
def mock_collection_modules():
    return MagicMock()

@pytest.fixture
def mock_collection_courses():
    return MagicMock()

@pytest.fixture
def mock_logger():
    return MagicMock()

@pytest.fixture
def repo(mock_collection_modules, mock_collection_courses, mock_logger):
    return ModuleRepository(
        mock_collection_modules,
        mock_collection_courses,
        mock_logger
    )

def test_get_modules_from_course_found(repo, mock_collection_modules, mock_logger):
    course_id = "60b8d295f1d2f93fbcf12345"
    modules_list = [{"_id": 1}, {"_id": 2}]
    mock_collection_modules.find_one.return_value = {"modules": modules_list}

    result = repo.get_modules_from_course(course_id)

    mock_collection_modules.find_one.assert_called_once_with({"course_id": ObjectId(course_id)})
    mock_logger.debug.assert_any_call(f"[MODULE REPOSITORY] Retrieved modules for course with ID: {course_id}")
    assert result == modules_list

def test_get_modules_from_course_not_found(repo, mock_collection_modules, mock_logger):
    course_id = "60b8d295f1d2f93fbcf12345"
    mock_collection_modules.find_one.return_value = None

    result = repo.get_modules_from_course(course_id)

    mock_collection_modules.find_one.assert_called_once_with({"course_id": ObjectId(course_id)})
    mock_logger.debug.assert_called_with(f"[MODULE REPOSITORY] Course with ID: {course_id} not found")
    assert result == []

def test_add_module_to_course_existing_course(repo, mock_collection_modules, mock_collection_courses, mock_logger):
    course_id = "60b8d295f1d2f93fbcf12345"
    module = MagicMock(spec=Module)
    module.to_dict.return_value = {"_id": "module_id", "name": "Module 1"}

    mock_collection_modules.find_one.return_value = {"course_id": ObjectId(course_id)}

    returned_id = repo.add_module_to_course(course_id, module)

    mock_collection_modules.update_one.assert_called_once_with(
        {"course_id": ObjectId(course_id)},
        {"$addToSet": {"modules": module.to_dict()}}
    )
    mock_collection_courses.update_one.assert_called_once_with(
        {"_id": ObjectId(course_id)},
        {"$addToSet": {"modules": "module_id"}}
    )
    mock_logger.debug.assert_called_with(f"[MODULE REPOSITORY] Add module {module} to course {course_id}")
    assert returned_id == "module_id"

def test_add_module_to_course_new_course(repo, mock_collection_modules, mock_collection_courses, mock_logger):
    course_id = "60b8d295f1d2f93fbcf12345"
    module = MagicMock(spec=Module)
    module.to_dict.return_value = {"_id": "module_id", "name": "Module 1"}

    mock_collection_modules.find_one.return_value = None

    returned_id = repo.add_module_to_course(course_id, module)

    mock_collection_modules.insert_one.assert_called_once_with(
        {"course_id": ObjectId(course_id), "modules": [module.to_dict()]}
    )
    mock_collection_courses.update_one.assert_called_once_with(
        {"_id": ObjectId(course_id)},
        {"$addToSet": {"modules": "module_id"}}
    )
    mock_logger.debug.assert_called_with(f"[MODULE REPOSITORY] Add module {module} to course {course_id}")
    assert returned_id == "module_id"

def test_modify_module_in_course_swap_positions(repo, mock_collection_modules, mock_logger):
    course_id = "60b8d295f1d2f93fbcf12345"
    module_id = ID_OBJ
    new_data = {"position": 2, "name": "Updated Module"}

    # Course with the module to update, current position 1
    course_doc = {
        "modules": [
            {"_id": module_id, "position": 1},
            {"_id": "mod456", "position": 2}
        ]
    }
    mock_collection_modules.find_one.side_effect = [
        course_doc,  # first find_one for course + module
        course_doc   # second find_one for swapping
    ]

    mock_collection_modules.update_one.return_value.modified_count = 1

    result = repo.modify_module_in_course(new_data, course_id, module_id)

    # Check that update_one was called with swap positions
    mock_collection_modules.update_one.assert_called_once()
    mock_logger.debug.assert_any_call(f"[MODULE REPOSITORY] Swapped positions between modules {module_id} and mod456")
    assert result is True

def test_modify_module_in_course_update_fields_only(repo, mock_collection_modules, mock_logger):
    course_id = "60b8d295f1d2f93fbcf12345"
    module_id = ID_OBJ
    new_data = {"name": "Updated Module", "description": "New Desc"}

    course_doc = {
        "modules": [
            {"_id": module_id, "position": 1}
        ]
    }
    # find_one returns course with the module (no swap)
    mock_collection_modules.find_one.return_value = course_doc
    mock_collection_modules.update_one.return_value.modified_count = 1

    result = repo.modify_module_in_course(new_data, course_id, module_id)

    mock_collection_modules.update_one.assert_called_once_with(
        {"course_id": ObjectId(course_id), "modules._id": module_id},
        {"$set": {
            "modules.$.name": "Updated Module",
            "modules.$.description": "New Desc"
        }}
    )
    mock_logger.debug.assert_any_call(
        f"[MODULE REPOSITORY] Updated module {module_id} in course {course_id}: "
        "{'modules.$.name': 'Updated Module', 'modules.$.description': 'New Desc'}"
    )
    assert result is True

def test_modify_module_in_course_no_course_found(repo, mock_collection_modules, mock_logger):
    course_id = ID_OBJ
    module_id = ID_OBJ
    new_data = {"name": "Updated"}

    mock_collection_modules.find_one.return_value = None

    result = repo.modify_module_in_course(new_data, course_id, module_id)

    mock_logger.debug.assert_called_with(f"[MODULE REPOSITORY] Module {module_id} not found in course {course_id}")
    assert result is False

def test_delete_module_from_course_success(repo, mock_collection_modules, mock_collection_courses, mock_logger):
    course_id = ID_OBJ
    module_id = ID_OBJ
    module_data = {"position": 2}

    repo.get_module_by_id = MagicMock(return_value=module_data)

    mock_collection_modules.update_one.return_value.modified_count = 1

    result = repo.delete_module_from_course(course_id, module_id)

    repo.get_module_by_id.assert_called_once_with(course_id, module_id)
    mock_collection_modules.update_one.assert_called_with(
        {"course_id": ObjectId(course_id)},
        {"$pull": {"modules": {"_id": module_id}}}
    )
    mock_collection_modules.update_many.assert_called_once()
    mock_collection_courses.update_one.assert_called_once_with(
        {"_id": ObjectId(course_id)},
        {"$pull": {"modules": module_id}}
    )
    mock_logger.debug.assert_called_with(f"[MODULE REPOSITORY] Deleted module {module_id} from course {course_id}")
    assert result is True

def test_delete_module_from_course_not_modified(repo, mock_collection_modules, mock_collection_courses, mock_logger):
    course_id = ID_OBJ
    module_id = ID_OBJ
    module_data = {"position": 2}

    repo.get_module_by_id = MagicMock(return_value=module_data)

    mock_collection_modules.update_one.return_value.modified_count = 0

    result = repo.delete_module_from_course(course_id, module_id)

    assert result is False

def test_get_module_by_id_not_found(repo, mock_collection_modules, mock_logger):
    course_id = ID_OBJ
    module_id = ID_OBJ
    mock_collection_modules.find_one.return_value = None

    result = repo.get_module_by_id(course_id, module_id)

    mock_logger.debug.assert_any_call(f"[MODULE REPOSITORY] Module with ID {module_id} not found in course with ID {course_id}")
    assert result is None

def test_get_resources_from_module_found(repo, mock_collection_modules):
    course_id = ID_OBJ
    module_id = ID_OBJ
    resource_dict = {"_id": ID, "title": "Resource 1"}
    resource_obj = MagicMock()
    resource_obj.to_dict.return_value = resource_dict

    # Patch Resource.from_dict to return a MagicMock with to_dict
    Resource.from_dict = MagicMock(return_value=resource_obj)

    # The aggregation returns a list with one dict containing "resources"
    mock_collection_modules.aggregate.return_value = [
        {"resources": [resource_dict]}
    ]

    result = repo.get_resources_from_module(course_id, module_id)

    assert result[0]["_id"] == resource_dict["_id"]
    assert result[0]["title"] == resource_dict["title"]

def test_get_resources_from_module_not_found(repo, mock_collection_modules, mock_logger):
    course_id = ID_OBJ
    module_id = ID_OBJ

    mock_collection_modules.aggregate.return_value = []

    result = repo.get_resources_from_module(course_id, module_id)

    mock_logger.debug.assert_called_with(
        f"[MODULE REPOSITORY] Module with ID {module_id} not found in course with ID {course_id}"
    )
    assert result is None

def test_get_resource_from_module_found(repo, mock_collection_modules):
    course_id = ID_OBJ
    module_id = ID_OBJ
    resource_id = ID_OBJ_2
    resource_dict = {"_id": ID_2, "title": "Resource 1"}
    resource_obj = MagicMock()
    resource_obj.to_dict.return_value = resource_dict

    Resource.from_dict = MagicMock(return_value=resource_obj)

    mock_collection_modules.aggregate.return_value = [
        {"resource": resource_dict}
    ]

    result = repo.get_resource_from_module(course_id, module_id, resource_id)

    assert result["_id"] == resource_dict["_id"]
    assert result["title"] == resource_dict["title"]

def test_get_resource_from_module_not_found(repo, mock_collection_modules, mock_logger):
    course_id = ID_OBJ
    module_id = ID_OBJ
    resource_id = ID_OBJ_2

    mock_collection_modules.aggregate.return_value = []

    result = repo.get_resource_from_module(course_id, module_id, resource_id)

    mock_logger.debug.assert_called_with(
        f"[MODULE REPOSITORY] Resource with ID {resource_id} not found in module with ID {module_id} in course with ID {course_id}"
    )
    assert result is None

def test_add_resource_to_module_success(repo, mock_collection_modules, mock_logger):
    course_id = ID_OBJ
    module_id = ID_OBJ
    resource_dict = {"_id": ID_OBJ_2, "name": "Resource 1"}

    mock_collection_modules.update_one.return_value.modified_count = 1

    result = repo.add_resource_to_module(course_id, module_id, resource_dict)

    mock_collection_modules.update_one.assert_called_once_with(
        {"course_id": ObjectId(course_id), "modules._id": module_id},
        {"$addToSet": {"modules.$.resources": resource_dict}},
    )
    mock_logger.debug.assert_called_with(f"[MODULE REPOSITORY] Resource {resource_dict} added to module {module_id}")
    assert result is True

def test_add_resource_to_module_failure(repo, mock_collection_modules, mock_logger):
    course_id = ID_OBJ
    module_id = ID_OBJ
    resource_dict = {"_id": ID_OBJ_2, "name": "Resource 1"}

    mock_collection_modules.update_one.return_value.modified_count = 0

    result = repo.add_resource_to_module(course_id, module_id, resource_dict)

    mock_logger.debug.assert_called_with(f"[MODULE REPOSITORY] Failed to add resource {resource_dict} to module {module_id}")
    assert result is False

def test_delete_resource_from_module_success(repo, mock_collection_modules, mock_logger):
    course_id = ID_OBJ
    module_id = ID_OBJ
    resource_id = ID_OBJ_2
    resource_data = {"position": 3}

    repo.get_resource_from_module = MagicMock(return_value=resource_data)

    mock_collection_modules.update_one.return_value.modified_count = 1

    result = repo.delete_resource_from_module(course_id, module_id, resource_id)

    repo.get_resource_from_module.assert_called_once_with(course_id, module_id, resource_id)
    mock_collection_modules.update_one.assert_called_once_with(
        {"course_id": ObjectId(course_id), "modules._id": module_id},
        {"$pull": {"modules.$.resources": {"_id": resource_id}}},
    )
    mock_collection_modules.update_many.assert_called_once()
    mock_logger.debug.assert_called_with(f"[MODULE REPOSITORY] Resource {resource_id} deleted from module {module_id}")
    assert result is True

def test_delete_resource_from_module_failure(repo, mock_collection_modules, mock_logger):
    course_id = ID_OBJ
    module_id = ID_OBJ
    resource_id = ID_OBJ_2

    repo.get_resource_from_module = MagicMock(return_value={"position": 3})

    mock_collection_modules.update_one.return_value.modified_count = 0

    result = repo.delete_resource_from_module(course_id, module_id, resource_id)

    mock_logger.debug.assert_called_with(f"[MODULE REPOSITORY] Failed to delete resource {resource_id} from module {module_id}")
    assert result is False
