import datetime
from error.error import error_generator
from src.headers import FEEDBACK_CREATED
from src.models.feedback import FeedbackCourse, FeedbackStudent

class FeedbackService:
    def __init__(self, repository_feedbacks, service_courses, logger):
        self.repository_feedbacks = repository_feedbacks
        self.service_courses = service_courses
        self.logger = logger

    def create_course_feedback(self, course_id, feedback):
        try:
            # Check if the course exists
            course = self.service_courses.get_course_by_id(course_id)
            if not course:
                error = error_generator("Course not found", "COURSE_NOT_FOUND", 404, "create_course_feedback")
                return error["response"], error["code_status"]

            # Create the feedback object
            feedback_object = FeedbackCourse(
                course_id=course_id,
                feedback=feedback,
                created_at=datetime.datetime.utcnow(),
            )

            # Insert the feedback into the repository
            self.repository_feedbacks.insert_course_feedback(feedback_object)
            
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
            err = error_generator("Internal server error", "INTERNAL_SERVER_ERROR", 500, "create_course_feedback")
            return err["response"], err["code_status"]
        
    def get_course_feedback(self, course_id):
        try:
            # Lets check if the course exists
            course_exists = self.service_courses.get_course_by_id(course_id)
            
            if not course_exists:
                error = error_generator("Course not found", "COURSE_NOT_FOUND", 404, "get_course_feedback")
                return error["response"], error["code_status"]
            
            # Get feedback for the course
            feedback = self.repository_feedbacks.get_course_feedback(course_id)
            
            if not feedback:
                error = error_generator("No feedback found", "NO_FEEDBACK_FOUND", 404, "get_course_feedback")
                return error["response"], error["code_status"]

            return { "response": [feedback.to_dict() for feedback in feedback ], "status": 200 }
        
        except Exception as e:
            err = error_generator("Internal server error", "INTERNAL_SERVER_ERROR", 500, "get_course_feedback")
            return err["response"], err["code_status"]
        
    def create_student_feedback(self, student_id, teacher_id, feedback):
        try:
            # Check if the student exists
            feedback_object = FeedbackStudent(
                student_id=student_id,
                teacher_id=teacher_id,
                feedback=feedback
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
            err = error_generator("Internal server error", "INTERNAL_SERVER_ERROR", 500, "create_student_feedback")
            return err["response"], err["code_status"]
        
    def get_student_feedback(self, student_id, course_id):
        try:
            course_exists = self.service_courses.get_course_by_id(course_id)
            
            if not course_exists:
                error = error_generator("Course not found", "COURSE_NOT_FOUND", 404, "get_student_feedback")
                return error["response"], error["code_status"]
            
            # Get feedback for the student
            feedback = self.repository_feedbacks.get_student_feedback(student_id, course_id)
            
            if not feedback:
                error = error_generator("No feedback found", "NO_FEEDBACK_FOUND", 404, "get_student_feedback")
                return error["response"], error["code_status"]

            return { "response": [feedback.to_dict() for feedback in feedback ], "status": 200 }
        
        except Exception as e:
            err = error_generator("Internal server error", "INTERNAL_SERVER_ERROR", 500, "get_student_feedback")
            return err["response"], err["code_status"]