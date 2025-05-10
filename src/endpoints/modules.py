from flask import Blueprint, request
from services import service_courses, logger
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
    url = url
    type = type # mp4? pdf?
    date_created = datetime.now()
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
    result = service_courses.add_module_to_course(course_id, data)

    return result["response"], result["code_status"]
