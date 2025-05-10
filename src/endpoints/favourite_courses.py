from flask import Blueprint, request

from src.error.error import error_generator
from src.headers import MISSING_FIELDS
from services import service_users, logger, service_courses

courses_favourites = Blueprint(
    "courses_favourites", __name__, url_prefix="/courses/favourites"
)


# This method is for adding a course to the favourites list
@courses_favourites.post("/")
def add_favourite_course():
    """
    Add a course to the favourites list.
    """

    # Get data from request
    data = request.json

    # Check if the student_id is in the request
    if "student_id" not in data:
        error = error_generator(
            MISSING_FIELDS, "Student ID is required", 400, "add_favourite_course"
        )
        return error["response"], error["code_status"]

    # Check if the course_id is in the request
    if "course_id" not in data:
        error = error_generator(
            MISSING_FIELDS, "Course ID is required", 400, "add_favourite_course"
        )
        return error["response"], error["code_status"]

    # Get the student_id and course_id from the request
    student_id = data["student_id"]
    course_id = data["course_id"]

    logger.debug(
        f"[APP] Adding course with ID: {course_id} to favourites for student with ID: {student_id}"
    )
    # Call the service to add the course to favourites
    result = service_users.set_favourite_course_for_student(course_id, student_id)

    return result["response"], result["code_status"]


@courses_favourites.delete("/")
def remove_favourite_course():
    """
    Remove a course from the favourites list.
    """

    student_id = request.args.get("student_id", None)
    course_id = request.args.get("course_id", None)

    # Check if the student_id is in the request
    if not student_id:
        error = error_generator(
            MISSING_FIELDS, "Student ID is required", 400, "remove_favourite_course"
        )
        return error["response"], error["code_status"]

    # Check if the course_id is in the request

    if not course_id:
        error = error_generator(
            MISSING_FIELDS, "Course ID is required", 400, "remove_favourite_course"
        )
        return error["response"], error["code_status"]

    logger.debug(
        f"[APP] Removing course with ID: {course_id} from favourites for student with ID: {student_id}"
    )
    # Call the service to remove the course from favourites
    result = service_users.remove_course_from_favourites(course_id, student_id)

    return result["response"], result["code_status"]


@courses_favourites.get("/<string:student_id>")
def get_favourite_courses(student_id=None):

    if not student_id:
        error = error_generator(
            MISSING_FIELDS, "Student ID is required", 400, "get_favourite_courses"
        )
        return error["response"], error["code_status"]
    
    offset = request.args.get("offset", default=0, type=int)
    max_per_page = request.args.get("max_per_page", default=10, type=int)

    logger.debug(f"[APP] Getting favourite courses for student with ID: {student_id}")

    # Call the service to get the favourite courses
    result = service_users.get_favourites_from_student_id(student_id, offset, max_per_page)

    return result["response"], result["code_status"]
