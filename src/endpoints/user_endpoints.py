from flask import Blueprint, request

from src.error.error import error_generator
from src.headers import (
    MISSING_FIELDS,
)
from services import service_users, service_enrollment, logger

courses_enrollment_bp = Blueprint("courses_enrollment", __name__, url_prefix="/courses")


# This method is for enrolling a student in a course
@courses_enrollment_bp.route("/<string:course_id>/enroll", methods=["POST"])
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

    result = service_enrollment.enroll_student_in_course(course_id, student_id)

    return result["response"], result["code_status"]


# This method is for list all the courses an user is enrolled
@courses_enrollment_bp.get("/enrolled_courses/<string:student_id>")
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
    result = service_enrollment.get_enrolled_courses(student_id)

    return result["response"], result["code_status"]


users_approvation_bp = Blueprint("users_approve", __name__, url_prefix="/courses")


# This method is for setting a user as approved
@courses_enrollment_bp.route("/<string:course_id>/approve", methods=["POST"])
def approve_student(course_id=None):
    """
    Approve a student in a course.
    """

    if not course_id:
        error = error_generator(
            MISSING_FIELDS, "Course ID is required", 400, "approve_student"
        )
        return error["response"], error["code_status"]

    # Get data from request
    data = request.json

    # Check if the student_id is in the request
    if "student_id" not in data:
        error = error_generator(
            MISSING_FIELDS, "student_id is required", 400, "approve_student"
        )
        return error["response"], error["code_status"]
    
    # Check if the student_id is in the request
    if "final_grade" not in data:
        error = error_generator(
            MISSING_FIELDS, "final_grade is required", 400, "approve_student"
        )
        return error["response"], error["code_status"]

    # Get the student_id from the request
    student_id = data["student_id"]
    final_grade = data["final_grade"]

    logger.debug(
        f"[APP] Approving student with ID: {student_id} in course with ID: {course_id}"
    )
    # Call the service to approve the student
    result = service_users.approve_student_in_course(course_id, student_id, final_grade)

    return result["response"], result["code_status"]

@courses_enrollment_bp.route("/<string:course_id>/student/<string:student_id>/approve", methods=["GET"])
def see_if_student_approved(course_id=None, student_id=None):
    """
    Return True if a student passes a course. Otherwise, return False.
    """

    if not course_id:
        error = error_generator(
            MISSING_FIELDS, "Course ID is required", 400, "/<string:course_id>/student/<string:student_id>/approve"
        )
        return error["response"], error["code_status"]
    
    if not student_id:
        error = error_generator(
            MISSING_FIELDS, "Student ID is required", 400, "/<string:course_id>/student/<string:student_id>/approve"
        )
        return error["response"], error["code_status"]

    logger.debug(
        f"[APP] See if student with ID: {student_id} approved in course with ID: {course_id}"
    )
    # Call the service to approve the student
    result = service_users.see_if_student_approved(course_id, student_id)

    return result["response"], result["code_status"]
