from flask import Blueprint, request, jsonify

from src.error.error import error_generator
from src.headers import MISSING_FIELDS
from services import service_courses, logger


courses_bp = Blueprint("courses_actions", __name__, url_prefix="/courses")


@courses_bp.post("/")
def create_course():
    """
    Create a new course.
    """
    # Get data from request
    data = request.json

    # Call the service to create the course
    logger.debug(f"[APP] Creating course with data: {data}")
    result = service_courses.create_course(data)

    return result["response"], result["code_status"]


# This method is for editing a course
@courses_bp.put("/<string:course_id>")
def update_course(course_id=None):
    """
    Update a course by ID.
    """
    # Get data from request

    if not course_id:
        error = error_generator(
            MISSING_FIELDS, "Course ID is required", 400, "update_course"
        )
        return error["response"], error["code_status"]

    data = request.json

    owner_id = request.args.get("owner_id", None)

    if not owner_id:
        error = error_generator(
            MISSING_FIELDS, "Owner ID is required", 400, "update_course"
        )
        return error["response"], error["code_status"]

    # Call the service to update the course
    logger.debug(f"[APP] Updating course with ID: {course_id} and data: {data}")
    result = service_courses.update_course(course_id, data, owner_id)

    return result["response"], result["code_status"]


# This method is for deleting a course
@courses_bp.delete("/<string:course_id>")
def delete_course(course_id=None):
    """
    Delete a course by ID.
    """
    if not course_id:
        error = error_generator(
            MISSING_FIELDS, "Course ID is required", 400, "delete_course"
        )
        return error["response"], error["code_status"]

    # Get the owner_id from the request
    owner_id = request.args.get("owner_id")

    if not owner_id:
        error = error_generator(
            MISSING_FIELDS, "Owner ID is required", 400, "delete_course"
        )
        return error["response"], error["code_status"]

    logger.debug(f"[APP] Deleting course with ID: {course_id} and owner ID: {owner_id}")
    # Call the service to delete the course
    result = service_courses.delete_course(course_id, owner_id)

    return result["response"], result["code_status"]


@courses_bp.get("/<string:course_id>")
def get_course(course_id=None):
    """
    Get a course by ID.
    """

    if not course_id:
        error = error_generator(
            MISSING_FIELDS, "Course ID is required", 400, "get_course"
        )
        return error["response"], error["code_status"]

    logger.debug(f"[APP] Getting course with ID: {course_id}")
    # Call the service to get the course
    result = service_courses.get_course(course_id)

    return result["response"], result["code_status"]


# This allow us to search a course by /courses/search?q=<string>
@courses_bp.get("/search")
def search_course():
    """
    Search for a course by name or description.
    """
    # Get the query string

    query_string = request.args.get("q", None)

    if not query_string:
        error = error_generator(
            MISSING_FIELDS,
            'Query string is required (?q="<string>")',
            400,
            "search_course",
        )
        return error["response"], error["code_status"]

    logger.debug(f"[APP] Searching for course with query: {query_string}")
    # Call the service to search for the course, removing the quotes
    result = service_courses.search_course_by_query(query_string.replace('"', ""))

    return result["response"], result["code_status"]


@courses_bp.get("/")
def get_courses():
    """
    Get all courses.
    """
    logger.debug(f"[APP] Getting all courses")
    # Call the service to get all courses
    result = service_courses.get_all_courses()

    return result["response"], result["code_status"]


# This methods is for listing the courses with pagination (we gave access to front to the offset)
# This endpoint will be called as example
# /courses/paginated?offset=0&max_per_page=5
@courses_bp.get("/paginated")
def get_paginated_courses():
    """
    Get all courses with pagination.
    """
    # Get the offset from the request
    # By default offset is 0, and max_per_page is 10
    offset = request.args.get("offset", default=0, type=int)
    max_per_page = request.args.get("max_per_page", default=10, type=int)

    logger.debug(
        f"[APP] Getting all courses with offset: {offset} and max_per_page: {max_per_page}"
    )
    # Call the service to get all courses
    result = service_courses.get_paginated_courses(offset, max_per_page)

    return result["response"], result["code_status"]


""" this endpoint is for getting the courses created by an user """


@courses_bp.get("/courses_owned/<string:user_id>")
def get_courses_owned_by_user(user_id=None):
    """
    Get all courses owned by a user.
    """

    offset = request.args.get("offset", default=0, type=int)
    max_per_page = request.args.get("max_per_page", default=10, type=int)

    if not user_id:
        error = error_generator(
            f"[COURSES][CONTROLLER] {MISSING_FIELDS}", "User ID is required", 400, "/courses_owned/<string:user_id>"
        )
        return error["response"], error["code_status"]

    logger.debug(f"[COURSES][CONTROLLER] Getting all courses owned by user with ID: {user_id}")
    # Call the service to get all courses
    try:
        courses = service_courses.get_courses_owned_by_user(user_id, offset, max_per_page)
        return jsonify([c.to_dict() for c in courses]), 200
    except Exception as e:
        error = error_generator("[COURSES][CONTROLLER] Error", e, 500, "/courses_owned/<string:user_id>")
        return error["response"], error["code_status"]
