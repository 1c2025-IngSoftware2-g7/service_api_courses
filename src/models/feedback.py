from datetime import datetime

from bson import ObjectId


class FeedbackCourse:
    def __init__(
        self, course_id: str, feedback: str, date_feedback_created: datetime = None
    ):
        self.course_id = course_id
        self.feedback = feedback

        if isinstance(date_feedback_created, str):
            self.feedback_created = datetime.strptime(date_feedback_created, "%Y-%m-%d")
        elif isinstance(date_feedback_created, datetime):
            self.feedback_created = date_feedback_created
        else:
            self.feedback_created = datetime.now()

    def __str__(self):
        return f"FeedbackCourse(course_id={self.course_id}, feedback={self.feedback})"

    def __repr__(self):
        return f"FeedbackCourse(course_id={self.course_id}, feedback={self.feedback})"

    def to_dict(self):
        return {
            "course_id": self.course_id,
            "feedback": self.feedback,
            "feedback_created": self.feedback_created,
        }

    @staticmethod
    def from_dict(data):
        return FeedbackCourse(
            course_id=data.get("course_id"),
            feedback=data.get("feedback"),
            date_feedback_created=data.get("feedback_created"),
        )


class FeedbackStudent:
    def __init__(
        self,
        student_id: str,
        course_id: str,
        teacher_id: str,
        feedback: str,
        feedback_date_created: datetime = None,
    ):
        self.student_id = student_id
        self.course_id = course_id
        self.teacher_id = teacher_id
        self.feedback = feedback
        if isinstance(feedback_date_created, str):
            self.feedback_created = datetime.strptime(feedback_date_created, "%Y-%m-%d")
        elif isinstance(feedback_date_created, datetime):
            self.feedback_created = feedback_date_created
        else:
            self.feedback_created = datetime.now()

    def __repr__(self):
        return f"FeedbackStudent(student_id={self.student_id}, course_id={self.course_id}, teacher_id={self.teacher_id}, feedback={self.feedback})"

    def to_dict(self):
        return {
            "student_id": self.student_id,
            "course_id": self.course_id,
            "teacher_id": self.teacher_id,
            "feedback": self.feedback,
            "feedback_created": self.feedback_created,
        }

    @staticmethod
    def from_dict(data):
        return FeedbackStudent(
            student_id=data.get("student_id"),
            course_id=data.get("course_id"),
            teacher_id=data.get("teacher_id"),
            feedback=data.get("feedback"),
            feedback_date_created=data.get("feedback_created"),
        )
