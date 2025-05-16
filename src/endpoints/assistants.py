from flask import Blueprint, request

from src.error.error import error_generator
from src.headers import MISSING_FIELDS
from services import service_courses, logger
from src.models.course import Course


courses_assistants = Blueprint(
    "courses_assistants", __name__, url_prefix="/courses/assistants"
)


@courses_assistants.post("/<string:course_id>")
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

    result = service_courses.add_assistant_to_course(course_id, assistant_id, owner_id)

    return result["response"], result["code_status"]


@courses_assistants.delete("/<string:course_id>/delete_assistant/<string:assistant_id>/with_owner_id/<string:owner_id>")
def remove_assistant_from_course(course_id=None, assistant_id=None, owner_id=None):
    """Remove assistant from course"""
    """ Sending though POST the owner id and the assistant id to be removed"""

    if not course_id:
        error = error_generator(
            "Missing course id", MISSING_FIELDS, 400, "remove_assistant_from_course"
        )
        return error["response"], error["code_status"]

    result = service_courses.remove_assistant_from_course(
        course_id, assistant_id, owner_id
    )

    return result["response"], result["code_status"]
