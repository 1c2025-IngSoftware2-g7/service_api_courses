from dotenv import load_dotenv

from src.repository.feedback_repository import FeedBackRepository
from src.repository.module_repository import ModuleRepository
from src.services.enrollment_service import EnrollmentService
from src.services.feedback_service import FeedbackService
from src.services.module_service import ModuleService

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

collection_modules_and_resources = db[
    os.getenv("MODULES_AND_RESOURCES_COLLECTION_NAME")
]

collection_approved_courses_students = db[
    os.getenv("APPROVED_COURSES_STUDENTS_COLLECTION_NAME")
]

# Indexes for courses will be the student id.
collection_users_data.create_index(["student_id"], unique=True)
collection_users_data.create_index(["course_id"], unique=True)

""" REPOSITORY CREATION """
repository_courses_data = CoursesRepository(collection_courses_data, logger)

repository_users_data = UsersDataRepository(
    collection_users_data, collection_approved_courses_students, logger
)

repository_feedbacks = FeedBackRepository(
    collection_feedback_courses, collection_feedback_students, logger
)

repository_modules_and_resources = ModuleRepository(
    collection_modules_and_resources, collection_courses_data, logger
)


""" SERVICE CREATION """
service_courses = CourseService(repository_courses_data, logger)

# Service users requires the course service to check if the course exists and other checks
service_users = UsersDataService(repository_users_data, service_courses, logger)

service_feedbacks = FeedbackService(repository_feedbacks, service_courses, logger)


service_enrollment = EnrollmentService(
    repository_courses_data, repository_users_data, logger
)

service_modules = ModuleService(
    repository_modules_and_resources, repository_courses_data, logger
)
