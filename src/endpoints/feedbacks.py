from flask import Blueprint, request
from services import service_feedbacks, logger
from src.error.error import error_generator
from src.headers import MISSING_FIELDS


feedbacks_bp = Blueprint("feedbacks", __name__, url_prefix="/courses/feedback")

##############################
# Feedbacks for courses
##############################


@feedbacks_bp.post("/add_feedback_to_course")
def add_feedback_to_course():
    """Add feedback to course"""
    """ Sending though POST the owner id and the assistant id to be added """
    """ A feedback is made by an user and only requires the course_id and feedback since 
    all feedbacks are anonymous """

    data = request.json

    if not data:
        error = error_generator(
            "Missing data", MISSING_FIELDS, 400, "add_feedback_to_course"
        )
        return error["response"], error["code_status"]

    if "course_id" not in data:
        error = error_generator(
            "Missing course id", MISSING_FIELDS, 400, "add_feedback_to_course"
        )
        return error["response"], error["code_status"]

    if "feedback" not in data:
        error = error_generator(
            "Missing feedback", MISSING_FIELDS, 400, "add_feedback_to_course"
        )
        return error["response"], error["code_status"]
    
    if "rating" not in data:
        error = error_generator(
            "Missing rating", MISSING_FIELDS, 400, "add_feedback_to_course"
        )
        return error["response"], error["code_status"]

    course_id = data["course_id"]
    feedback = data["feedback"]
    rating = data["feedback"]

    result = service_feedbacks.create_course_feedback(course_id, feedback, rating)
    logger.debug(f"[Feedbacks] Feedback created for course {course_id}")
    logger.debug(f"[Feedbacks] Feedback: {feedback}")
    logger.debug(f"[Feedbacks] Result: {result}")

    return result["response"], result["code_status"]


@feedbacks_bp.get("/get_course_feedback/<string:course_id>")
def get_course_feedback(course_id=None):
    """Get feedback for a course"""
    """ Sending though GET the course id to get the feedbacks """

    if not course_id:
        error = error_generator(
            "Missing course id", MISSING_FIELDS, 400, "get_course_feedback"
        )
        return error["response"], error["code_status"]

    result = service_feedbacks.get_course_feedback(course_id)

    return result["response"], result["code_status"]


###############################
# Feedbacks for students
###############################


@feedbacks_bp.post("/add_feedback_to_student")
def add_feedback_to_student():
    """Add feedback to student"""
    """ Sending though POST the owner id and the assistant id to be added """
    """ A feedback is made by an user and only requires the course_id and feedback since 
    all feedbacks are anonymous """

    data = request.json

    if not data:
        error = error_generator(
            "Missing data", MISSING_FIELDS, 400, "add_feedback_to_student"
        )
        return error["response"], error["code_status"]

    required_fields = ["course_id", "student_id", "teacher_id", "feedback"]

    for field in required_fields:
        if field not in data:
            error = error_generator(
                f"Missing {field}", MISSING_FIELDS, 400, "add_feedback_to_student"
            )
            return error["response"], error["code_status"]

    # Lets delete the other fields if they exist

    for field in data.keys():
        if field not in required_fields:
            del data[field]

    student_id = data["student_id"]
    feedback = data["feedback"]
    teacher_id = data["teacher_id"]
    course_id = data["course_id"]

    result = service_feedbacks.create_student_feedback(
        student_id, course_id, teacher_id, feedback
    )

    return result["response"], result["code_status"]


@feedbacks_bp.get("/get_student_feedback/<string:student_id>/<string:course_id>")
def get_student_feedback(student_id=None, course_id=None):
    """Get feedback for a student"""
    """ Sending though GET the course id to get the feedbacks """

    if not student_id:
        error = error_generator(
            "Missing student id", MISSING_FIELDS, 400, "get_student_feedback"
        )
        return error["response"], error["code_status"]

    if not course_id:
        error = error_generator(
            "Missing course id", MISSING_FIELDS, 400, "get_student_feedback"
        )
        return error["response"], error["code_status"]

    result = service_feedbacks.get_student_feedback(student_id, course_id)

    return result["response"], result["code_status"]
