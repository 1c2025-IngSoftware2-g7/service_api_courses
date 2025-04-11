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

repository = CoursesRepository(collection)
service = CourseService(repository)


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