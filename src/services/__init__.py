from dotenv import load_dotenv

from src.repository.feedback_repository import FeedBackRepository
from src.services.feedback_service import FeedbackService

load_dotenv()

import logging
import os
from pymongo import MongoClient
from repository.courses_repository import CoursesRepository
from repository.users_data_repository import UsersDataRepository
from services.users_data_service import UsersDataService
from .course_service import CourseService
from services.logger_config import get_logger


client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("COURSE_DATABASE")]

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("pymongo").setLevel(logging.WARNING)
logger = get_logger("api-courses")

collection_courses_data = db[os.getenv("COURSES_COLLECTION_NAME")]
collection_users_data = db[os.getenv("USERS_COLLECTION_NAME")]

collection_feedback_students = db[os.getenv("FEEDBACK_STUDENTS_COLLECTION_NAME")]
collection_feedback_courses = db[os.getenv("FEEDBACK_COURSES_COLLECTION_NAME")]

# Indexes for courses will be the student id.
collection_users_data.create_index(["student_id"], unique=True)


repository_courses_data = CoursesRepository(collection_courses_data, logger)
repository_users_data = UsersDataRepository(collection_users_data, logger)
repository_feedbacks = FeedBackRepository(
    collection_feedback_courses, collection_feedback_students, logger
)


service_courses = CourseService(repository_courses_data, logger)
# Service users requires the course service to check if the course exists and other checks
service_users = UsersDataService(repository_users_data, service_courses, logger)

service_feedbacks = FeedbackService(repository_feedbacks, service_courses, logger)
