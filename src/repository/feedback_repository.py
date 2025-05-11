from bson import ObjectId
from src.models.feedback import FeedbackCourse, FeedbackStudent


class FeedBackRepository:
    def __init__(
        self, collection_courses_feedback, collection_students_feedback, logger
    ):
        self.collection_courses_feedback = collection_courses_feedback
        self.collection_students_feedback = collection_students_feedback
        self.logger = logger

    def insert_course_feedback(self, feedback_obj: FeedbackCourse):
        """
        Insert feedback for a course into the database.
        """
        feedback_course_id = feedback_obj.course_id

        self.logger.debug(f"feedback_obj: {feedback_obj.to_dict()}")
        result = self.collection_courses_feedback.insert_one(feedback_obj.to_dict())

        self.logger.debug(
            f"[REPOSITORY] Inserted feedback with ID: {result.inserted_id}"
        )

        self.logger.debug(
            f"[REPOSITORY] Inserted feedback for course with ID: {feedback_course_id}"
        )

    def get_course_feedback(self, course_id):
        """
        Get all feedback for a course from the database.
        """
        feedback_result = list(
            self.collection_courses_feedback.find({"course_id": course_id})
        )

        self.logger.debug(
            f"[REPOSITORY] Retrieved feedback for course with ID: {course_id}"
        )

        self.logger.debug(f"[REPOSITORY] Feedback result: {feedback_result}")
        return feedback_result

    def insert_student_feedback(self, feedback_obj: FeedbackStudent):
        """
        Insert feedback for a student into the database.
        """
        feedback_student_id = feedback_obj.student_id

        self.collection_students_feedback.insert_one(feedback_obj.to_dict())

        self.logger.debug(
            f"[REPOSITORY] Inserted feedback for student with ID: {feedback_student_id}"
        )

    def get_student_feedback(self, student_id, course_id):
        """
        Get all feedback for a student from the database.
        """
        feedback_result = list(
            self.collection_students_feedback.find(
                {"student_id": student_id, "course_id": course_id}
            )
        )

        return feedback_result
