
import datetime


class FeedbackCourse:
    def __init__(self, course_id: str, feedback: str):
        self.course_id = course_id
        self.feedback = feedback
        self.feedback_created = datetime.datetime.utc()

    def __repr__(self):
        return f"FeedbackCourse(course_id={self.course_id}, feedback={self.feedback})"

    def to_dict(self):
        return {
            "course_id": self.course_id,
            "feedback": self.feedback,
            "feedback_created": self.feedback_created,
        }
        
    def from_dict(self, data):
        self.course_id = data.get("course_id")
        self.feedback = data.get("feedback")
        self.feedback_created = data.get("feedback_created")
        return self
    
class FeedbackStudent:
    def __init__(self, student_id: str, course_id: str, teacher_id: str, feedback: str):
        self.student_id = student_id
        self.course_id = course_id
        self.teacher_id = teacher_id
        self.feedback = feedback
        self.feedback_created = datetime.datetime.utc()

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
        
    def from_dict(self, data):
        self.student_id = data.get("student_id")
        self.course_id = data.get("course_id")
        self.teacher_id = data.get("teacher_id")
        self.feedback = data.get("feedback")
        self.feedback_created = data.get("feedback_created")
        return self