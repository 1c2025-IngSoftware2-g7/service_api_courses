import logging
import os
from pymongo import MongoClient
from src.repository.courses_repository import CoursesRepository
from src.repository.users_data_repository import UsersDataRepository
from src.services.users_data_service import UsersDataService
from .course_service import CourseService

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("COURSE_DATABASE")]

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("pymongo").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

collection_courses_data = db[os.getenv("COURSES_COLLECTION_NAME")]
collection_users_data = db[os.getenv("USERS_COLLECTION_NAME")]

# Indexes for courses will be the student id.
collection_users_data.create_index(["student_id"], unique=True)


repository_courses_data = CoursesRepository(collection_courses_data, logger)
repository_users_data = UsersDataRepository(collection_users_data, logger)


service_courses = CourseService(repository_courses_data, logger)
# Service users requires the course service to check if the course exists and other checks
service_users = UsersDataService(repository_users_data, service_courses, logger)
