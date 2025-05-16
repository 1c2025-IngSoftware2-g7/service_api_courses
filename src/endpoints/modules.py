from flask import Blueprint, request
from services import service_modules, logger
from src.error.error import error_generator
from src.headers import MISSING_FIELDS


modules_bp = Blueprint("modules", __name__, url_prefix="/courses")


# This method is for adding a module to a course
@modules_bp.route("/<string:course_id>/modules", methods=["POST"])
def add_module(course_id=None):
    """
    Add a module to a course.
    Module comes as a json with
    title = title
    description = description
    owner_course = id of the attempt creator
    """

    if not course_id:
        error = error_generator(
            MISSING_FIELDS, "Course ID is required", 400, "add_module"
        )
        return error["response"], error["code_status"]

    # Get data from request
    data = request.json

    logger.debug(f"[APP] Adding module to course with ID: {course_id} and data: {data}")
    # Call the service to add the module
    result = service_modules.add_module_to_course(course_id, data)

    return result["response"], result["code_status"]


# Lets add a modification id
@modules_bp.route("/<string:course_id>/modules/<string:module_id>", methods=["PUT"])
def modify_module(course_id=None, module_id=None):
    """
    Modify a module in a course.
    Module comes as a json with
    title = title
    description = description
    url = url
    type = type
    """

    if not course_id:
        error = error_generator(
            MISSING_FIELDS, "Course ID is required", 400, "modify_module"
        )
        return error["response"], error["code_status"]

    if not module_id:
        error = error_generator(
            MISSING_FIELDS, "Module ID is required", 400, "modify_module"
        )
        return error["response"], error["code_status"]

    # Get data from request
    data = request.json

    owner_id = data.get("owner_id", None)

    if not owner_id:
        error = error_generator(
            MISSING_FIELDS, "Owner ID is required", 400, "modify_module"
        )
        return error["response"], error["code_status"]

    """
    Modify a module in a course.
    Module comes as a json with
    title = title
    description = description
    url = url
    type = type
    """

    logger.debug(
        f"[APP] Modifying module with ID: {module_id} in course with ID: {course_id} and data: {data}"
    )
    # Call the service to modify the module
    result = service_courses.modify_module_in_course(
        course_id, module_id, owner_id, data
    )

    return result["response"], result["code_status"]


@modules_bp.route(
    "/<string:course_id>/modules/<string:module_id>/<string:owner_id>",
    methods=["DELETE"],
)
def delete_module_from_course(course_id=None, module_id=None, owner_id=None):
    """
    Delete a module from a course.
    Module comes as a json with
    title = title
    description = description
    url = url
    type = type
    """

    if not course_id:
        error = error_generator(
            MISSING_FIELDS, "Course ID is required", 400, "delete_module"
        )
        return error["response"], error["code_status"]

    if not module_id:
        error = error_generator(
            MISSING_FIELDS, "Module ID is required", 400, "delete_module"
        )
        return error["response"], error["code_status"]

    if not owner_id:
        error = error_generator(
            MISSING_FIELDS, "Owner ID is required", 400, "delete_module"
        )
        return error["response"], error["code_status"]

    logger.debug(
        f"[APP] Deleting module with ID: {module_id} in course with ID: {course_id}"
    )
    # Call the service to delete the module
    result = service_courses.delete_module_from_course(course_id, module_id, owner_id)

    return result["response"], result["code_status"]
