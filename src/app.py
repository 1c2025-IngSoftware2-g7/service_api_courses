import logging
import os
from error.error import error_generator
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from headers import MISSING_FIELDS
from models.course import Course
from flask_cors import CORS
from repository.courses_repository import CoursesRepository
from service.course_service import CourseService
from pymongo import MongoClient

load_dotenv()


courses_app = Flask(__name__)
CORS(courses_app, origins=["*"])

# Session config
courses_app.secret_key = os.getenv("SECRET_KEY_SESSION")

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("COURSE_DATABASE")]
collection = db[os.getenv("COURSES_COLLECTION_NAME")]

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("pymongo").setLevel(logging.WARNING)

# Set up the logger
logger = logging.getLogger(__name__)

repository = CoursesRepository(collection, logger)
service = CourseService(repository, logger)


@courses_app.get("/courses/health")
def health_check():
    return {"status": "ok"}, 200


@courses_app.route("/courses", methods=["POST"])
def create_course():
    """
    Create a new course.
    """
    # Get data from request
    data = request.json

    # Call the service to create the course
    logger.debug(f"[APP] Creating course with data: {data}")
    result = service.create_course(data)

    return result["response"], result["code_status"]


# This method is for editing a course
@courses_app.route("/courses/<string:course_id>", methods=["PUT"])
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
    result = service.update_course(course_id, data, owner_id)

    return result["response"], result["code_status"]


# This method is for deleting a course
@courses_app.route("/courses/<string:course_id>", methods=["DELETE"])
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
    result = service.delete_course(course_id, owner_id)

    return result["response"], result["code_status"]


@courses_app.route("/courses/<string:course_id>", methods=["GET"])
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
    result = service.get_course(course_id)

    return result["response"], result["code_status"]


# This allow us to search a course by /courses/search?q=<string>
@courses_app.route("/courses/search", methods=["GET"])
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
    result = service.search_course_by_query(query_string.replace('"', ""))

    return result["response"], result["code_status"]


@courses_app.route("/courses", methods=["GET"])
def get_courses():
    """
    Get all courses.
    """
    logger.debug(f"[APP] Getting all courses")
    # Call the service to get all courses
    result = service.get_all_courses()

    return result["response"], result["code_status"]


# This method is for enrolling a student in a course
@courses_app.route("/courses/<string:course_id>/enroll", methods=["POST"])
def enroll_student(course_id=None):
    """
    Enroll a student in a course.
    """

    if not course_id:
        error = error_generator(
            MISSING_FIELDS, "Course ID is required", 400, "enroll_student"
        )
        return error["response"], error["code_status"]

    # Get data from request
    data = request.json

    # Check if the student_id is in the request
    if "student_id" not in data:
        return error_generator(
            MISSING_FIELDS, "Student ID is required", 400, "enroll_student"
        )

    # Get the student_id from the request
    student_id = data["student_id"]

    logger.debug(
        f"[APP] Enrolling student with ID: {student_id} in course with ID: {course_id}"
    )
    # Call the service to enroll the student
    result = service.enroll_student_in_course(course_id, student_id)

    return result["response"], result["code_status"]


# This method is for list all the courses an user is enrolled
@courses_app.route("/courses/enrolled_courses/<string:student_id>", methods=["GET"])
def get_enrolled_courses(student_id=None):
    """
    Get all courses a student is enrolled in.
    """

    if not student_id:
        error = error_generator(
            MISSING_FIELDS, "Student ID is required", 400, "get_enrolled_courses"
        )
        return error["response"], error["code_status"]

    logger.debug(f"[APP] Getting all courses for student with ID: {student_id}")
    # Call the service to get all courses
    result = service.get_enrolled_courses(student_id)

    return result["response"], result["code_status"]


# This method is for adding a module to a course
@courses_app.route("/courses/<string:course_id>/modules", methods=["POST"])
def add_module(course_id=None):
    """
    Add a module to a course.
    Module comes as a json with
    title = title
    description = description
    url = url
    type = type # mp4? pdf?
    date_created = datetime.now()
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
    result = service.add_module_to_course(course_id, data)

    return result["response"], result["code_status"]


# This methods is for listing the courses with pagination (we gave access to front to the offset)
# This endpoint will be called as example
# /courses/paginated?offset=0
@courses_app.route("/courses/paginated", methods=["GET"])
def get_paginated_courses():
    """
    Get all courses with pagination.
    """
    # Get the offset from the request
    offset = request.args.get("offset", default=0, type=int)
    max_per_page = request.args.get("max_page", default=10, type=int)

    logger.debug(
        f"[APP] Getting all courses with offset: {offset} and max_per_page: {max_per_page}"
    )
    # Call the service to get all courses
    result = service.get_paginated_courses(offset, max_per_page)

    return result["response"], result["code_status"]
