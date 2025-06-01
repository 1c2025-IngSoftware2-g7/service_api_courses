from flask import Blueprint, request

from src.error.error import error_generator
from src.headers import MISSING_FIELDS
from services import service_users, logger
from src.models.course import Course
from src.models.permissions import AssistantPermissions
from flasgger import swag_from

courses_assistants = Blueprint(
    "courses_assistants", __name__, url_prefix="/courses/assistants"
)


@courses_assistants.post("/<string:course_id>")
@swag_from(
    {
        "tags": ["Assistants"],
        "summary": "Add an assistant to a course",
        "parameters": [
            {
                "name": "course_id",
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
            }
        ],
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/AssistantPermission"}
                }
            },
        },
        "responses": {
            "200": {"description": "Assistant added"},
            "400": {"description": "Missing parameters"},
            "403": {"description": "User is not the owner of the course"},
            "404": {"description": "Course not found"},
            "409": {"description": "Assistant already exists"},
        },
    }
)
def add_assistant_to_course(course_id=None):
    """Add assistant to course"""
    """ Sending though POST the owner id and the assistant id to be added"""

    data = request.json

    if not course_id:
        error = error_generator(
            "Missing course id", MISSING_FIELDS, 400, "add_assistant_to_course"
        )
        return error["response"], error["code_status"]

    if not data:
        error = error_generator(
            "Missing data", MISSING_FIELDS, 400, "add_assistant_to_course"
        )
        return error["response"], error["code_status"]

    if "assistant_id" not in data:
        error = error_generator(
            "Missing assistand id", MISSING_FIELDS, 400, "add_assistant_to_course"
        )
        return error["response"], error["code_status"]

    if "owner_id" not in data:
        error = error_generator(
            "Missing owner id", MISSING_FIELDS, 400, "add_assistant_to_course"
        )
        return error["response"], error["code_status"]

    assistant_id = data["assistant_id"]
    owner_id = data["owner_id"]

    if "permissions" not in data:
        error = error_generator(
            "Missing permissions", MISSING_FIELDS, 400, "add_assistant_to_course"
        )
        return error["response"], error["code_status"]

    result = service_users.add_assistant_to_course(
        course_id, assistant_id, owner_id, data
    )

    return result["response"], result["code_status"]


@courses_assistants.put("/<string:course_id>")
@swag_from(
    {
        "tags": ["Assistants"],
        "summary": "Update an assistant's permissions for a course",
        "parameters": [
            {
                "name": "course_id",
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
            }
        ],
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/AssistantPermission"}
                }
            },
        },
        "responses": {
            "200": {"description": "Assistant permissions updated"},
            "400": {"description": "Missing parameters"},
            "403": {"description": "User is not the owner of the course"},
            "404": {"description": "Course or assistant not found"},
        },
    }
)
def modify_assistant_permissions(course_id=None):
    """Modify assistant permissions"""
    """ Sending though PUT the owner id and the assistant id to be modified"""

    data = request.json

    if not course_id:
        error = error_generator(
            "Missing course id", MISSING_FIELDS, 400, "modify_assistant_permissions"
        )
        return error["response"], error["code_status"]

    if not data:
        error = error_generator(
            "Missing data", MISSING_FIELDS, 400, "modify_assistant_permissions"
        )
        return error["response"], error["code_status"]

    if "assistant_id" not in data:
        error = error_generator(
            "Missing assistand id", MISSING_FIELDS, 400, "modify_assistant_permissions"
        )
        return error["response"], error["code_status"]

    if "owner_id" not in data:
        error = error_generator(
            "Missing owner id", MISSING_FIELDS, 400, "modify_assistant_permissions"
        )
        return error["response"], error["code_status"]

    assistant_id = data["assistant_id"]
    owner_id = data["owner_id"]

    if (
        "permissions" not in data
        or not isinstance(data["permissions"], dict)
        or len(data["permissions"]) == 0
    ):
        error = error_generator(
            "Missing permissions or incorrect kind of permissions given",
            MISSING_FIELDS,
            400,
            "modify_assistant_permissions",
        )
        return error["response"], error["code_status"]

    result = service_users.modify_assistant_permissions(
        course_id, assistant_id, owner_id, data
    )

    return result["response"], result["code_status"]


@courses_assistants.delete(
    "/<string:course_id>/delete_assistant/<string:assistant_id>/with_owner_id/<string:owner_id>"
)
@swag_from(
    {
        "tags": ["Assistants"],
        "summary": "Remove an assistant from a course",
        "parameters": [
            {
                "name": "course_id",
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
            },
            {
                "name": "assistant_id",
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
            },
            {
                "name": "owner_id",
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
            },
        ],
        "responses": {
            "200": {"description": "Assistant removed"},
            "400": {"description": "Missing parameters"},
            "403": {"description": "User is not the owner to remove the assistant"},
            "404": {"description": "Course or assistant not found"},
        },
    }
)
def remove_assistant_from_course(course_id=None, assistant_id=None, owner_id=None):
    """Remove assistant from course"""
    """ Sending though POST the owner id and the assistant id to be removed"""

    if not course_id:
        error = error_generator(
            "Missing course id", MISSING_FIELDS, 400, "remove_assistant_from_course"
        )
        return error["response"], error["code_status"]

    result = service_users.remove_assistant_from_course(
        course_id, assistant_id, owner_id
    )

    return result["response"], result["code_status"]


# Get permissions from a certain assistant id
@courses_assistants.get("/<string:course_id>/assistant/<string:assistant_id>")
def get_assistant_permissions(course_id=None, assistant_id=None):
    """Get assistant permissions"""
    """ Sending though GET the owner id and the assistant id to get permissions"""

    if not course_id:
        error = error_generator(
            "Missing course id", MISSING_FIELDS, 400, "get_assistant_permissions"
        )
        return error["response"], error["code_status"]

    if not assistant_id:
        error = error_generator(
            "Missing assistant id", MISSING_FIELDS, 400, "get_assistant_permissions"
        )
        return error["response"], error["code_status"]

    result = service_users.get_assistant_permissions(course_id, assistant_id)

    return result["response"], result["code_status"]
