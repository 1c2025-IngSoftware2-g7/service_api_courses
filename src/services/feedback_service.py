import datetime

from flask import jsonify
from error.error import error_generator
from src.headers import (
    COURSE_NOT_FOUND,
    FEEDBACK_CREATED,
    INTERNAL_SERVER_ERROR,
    USER_NOT_ALLOWED_TO_CREATE_FEEDBACK,
)
from src.models.feedback import FeedbackCourse, FeedbackStudent
from src.repository.feedback_repository import FeedBackRepository


class FeedbackService:
    def __init__(
        self,
        repository_feedbacks: FeedBackRepository,
        service_courses,
        service_users,
        logger,
    ):
        self.repository_feedbacks = repository_feedbacks
        self.service_courses = service_courses
        self.service_users = service_users
        self.logger = logger

    def create_course_feedback(self, course_id, feedback, rating):
        try:
            # Check if the course exists
            self.logger.debug(
                f"[FeedbackService] Creating feedback for course {course_id}"
            )
            course = self.service_courses.get_course_by_id(course_id)
            if course["code_status"] != 200:
                self.logger.debug(f"[FeedbackService] Course {course_id} not found")
                return error_generator(
                    "Course not found", COURSE_NOT_FOUND, 404, "create_course_feedback"
                )

            self.logger.debug(f"[FeedbackService] Course {course_id} found")
            # Create the feedback object
            feedback_object = FeedbackCourse(
                course_id=course_id, feedback=feedback, rating=rating
            )

            self.logger.debug(f"[FeedbackService] Feedback object: {feedback_object}")

            # Insert the feedback into the repository
            self.repository_feedbacks.insert_course_feedback(feedback_object)

            self.logger.debug(f"[FeedbackService] Feedback inserted successfully")

            return {
                "response": {
                    "type": "about:blank",
                    "title": FEEDBACK_CREATED,
                    "status": 201,
                    "detail": f"Feedback for course {course_id} created successfully.",
                    "instance": f"/feedback/course/{course_id}",
                },
                "code_status": 201,
            }
        except Exception as e:
            return error_generator(
                "Internal server error",
                INTERNAL_SERVER_ERROR,
                500,
                "create_course_feedback",
            )

    def get_course_feedback(self, course_id):
        try:
            # Lets check if the course exists
            course_exists = self.service_courses.get_course_by_id(course_id)

            if course_exists["code_status"] != 200:
                return error_generator(
                    "Course not found", COURSE_NOT_FOUND, 404, "get_course_feedback"
                )

            self.logger.debug(f"[FeedbackService] Course {course_id} found")
            # Get feedback for the course
            feedback_result = self.repository_feedbacks.get_course_feedback(course_id)

            self.logger.debug(f"[FeedbackService] Feedback result: {feedback_result}")
            return {
                "response": [
                    FeedbackCourse.from_dict(feedback).to_dict()
                    for feedback in feedback_result
                ],
                "code_status": 200,
            }

        except Exception as e:
            self.logger.debug(f"[FeedbackService] Error: {e}")
            return error_generator(
                "Internal server error",
                INTERNAL_SERVER_ERROR,
                500,
                "get_course_feedback",
            )

    def create_student_feedback(self, student_id, course_id, teacher_id, feedback):
        try:

            is_teacher_owner = self.service_courses.is_user_owner_of_course(
                course_id, teacher_id
            )
            is_assistant_with_permissions = (
                self.service_users.check_assistants_permissions(
                    course_id, teacher_id, "Feedbacks"
                )
            )

            if not is_teacher_owner and not is_assistant_with_permissions:
                return error_generator(
                    "You are not allowed to create feedback to students to this course",
                    USER_NOT_ALLOWED_TO_CREATE_FEEDBACK,
                    403,
                    "create_student_feedback",
                )

            # Check if the student exists
            feedback_object = FeedbackStudent(
                student_id=student_id,
                course_id=course_id,
                teacher_id=teacher_id,
                feedback=feedback,
            )

            # Insert the feedback into the repository
            self.repository_feedbacks.insert_student_feedback(feedback_object)

            return {
                "response": {
                    "type": "about:blank",
                    "title": FEEDBACK_CREATED,
                    "status": 201,
                    "detail": f"Feedback for student {student_id} created successfully.",
                    "instance": f"/feedback/student/{student_id}",
                },
                "code_status": 201,
            }
        except Exception as e:
            self.logger.debug(f"[FeedbackService] Create Student Feedback Error: {e}")
            return error_generator(
                "Internal server error",
                INTERNAL_SERVER_ERROR,
                500,
                "create_student_feedback",
            )

    def get_student_feedback(self, student_id, course_id):
        try:
            course_exists = self.service_courses.get_course_by_id(course_id)

            if course_exists["code_status"] != 200:
                return error_generator(
                    "Course not found", COURSE_NOT_FOUND, 404, "get_student_feedback"
                )

            # Get feedback for the student
            feedback = self.repository_feedbacks.get_student_feedback(
                student_id, course_id
            )

            if not feedback:
                return {
                    "response": {
                        "type": "about:blank",
                        "title": "No feedback found",
                        "status": 404,
                        "detail": f"No feedback found for student {student_id} in course {course_id}.",
                        "instance": f"/feedback/student/{student_id}",
                    },
                    "code_status": 404,
                }

            return {
                "response": (
                    [
                        FeedbackStudent.from_dict(feedback).to_dict()
                        for feedback in feedback
                    ]
                ),
                "code_status": 200,
            }

        except Exception as e:
            self.logger.debug(f"[FeedbackService] Get Student Feedback Error: {e}")
            return error_generator(
                "Internal server error",
                INTERNAL_SERVER_ERROR,
                500,
                "get_student_feedback",
            )
