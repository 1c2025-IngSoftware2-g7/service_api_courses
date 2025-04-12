import logging
import os
from error.error import error_generator
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from headers import MISSING_FIELDS
from models.course import Course
from repository.courses_repository import CoursesRepository
from service.course_service import CourseService
from pymongo import MongoClient

load_dotenv()


courses_app = Flask(__name__)

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
    result = service.create_course(data)
    
    return result["response"], result["code_status"]

# This method is for editing a course
@courses_app.route("/courses/<course_id>", methods=["PUT"])
def update_course(course_id):
    """
    Update a course by ID.
    """
    # Get data from request
    data = request.json

    # Call the service to update the course
    result = service.update_course(course_id, data)
    
    return result["response"], result["code_status"]

# This method is for deleting a course 
@courses_app.route("/courses/<course_id>", methods=["DELETE"])
def delete_course(course_id):
    """
    Delete a course by ID.
    """    
    owner_id = request.args.get("owner_id")
    
    if not owner_id:
        return error_generator(
            MISSING_FIELDS,
            "Owner ID is required",
            400,
            "delete_course"
        )
                
    # Call the service to delete the course
    result = service.delete_course(course_id, owner_id)
    
    return result["response"], result["code_status"]

@courses_app.route("/courses/<course_id>", methods=["GET"])
def get_course(course_id):
    """
    Get a course by ID.
    """
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
    
    # Check if args contains q as key
    if "q" not in request.args:
        return error_generator(
            MISSING_FIELDS,
            "Query string is required",
            400,
            "search_course"
        )
        
    query_string = request.args.get("q")
    
    if not query_string:
        return error_generator(
            MISSING_FIELDS,
            "Query string is required",
            400,
            "search_course"
        )
    
    # Call the service to search for the course, removing the quotes
    result = service.search_course_by_query(query_string.replace('"', ""))
    
    return result["response"], result["code_status"]

@courses_app.route("/courses", methods=["GET"])
def get_courses():
    """
    Get all courses.
    """
    # Call the service to get all courses
    result = service.get_all_courses()       
    
    return result["response"], result["code_status"]

# This method is for enrolling a student in a course
@courses_app.route("/courses/<course_id>/enroll", methods=["POST"])
def enroll_student(course_id):
    """
    Enroll a student in a course.
    """
    # Get data from request
    data = request.json

    # Check if the student_id is in the request
    if "student_id" not in data:
        return error_generator(
            MISSING_FIELDS,
            "Student ID is required",
            400,
            "enroll_student"
        )
        
    # Get the student_id from the request
    student_id = data["student_id"]
    
    # Call the service to enroll the student
    result = service.enroll_student_in_course(course_id, student_id)
    
    return result["response"], result["code_status"]

# This method is for list all the courses an user is enrolled
@courses_app.route("/courses/enrolled_courses/<student_id>", methods=["GET"])
def get_enrolled_courses(student_id):
    """
    Get all courses a student is enrolled in.
    """
    # Call the service to get all courses
    result = service.get_enrolled_courses(student_id)
    
    return result["response"], result["code_status"]

# This method is for adding a module to a course
@courses_app.route("/courses/<course_id>/modules", methods=["POST"])
def add_module(course_id):
    """
    Add a module to a course.
    Module comes as a json with 
    title = title
    description = description
    url = url
    type = type # mp4? pdf?
    date_created = datetime.now()
    """
    # Get data from request
    data = request.json

    # Call the service to add the module
    result = service.add_module_to_course(course_id, data)
    
    return result["response"], result["code_status"]