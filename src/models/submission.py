from typing import List, Optional, Dict, Any
from datetime import datetime
from utils import parse_to_timestamp_ms_now


class Feedback:
    def __init__(
        self,
        corrector_id: str,
        grade: Optional[float] = None,
        comment: Optional[str] = None,
        created_at: Optional[int] = None
    ):
        self.corrector_id = corrector_id
        self.grade = grade
        self.comment = comment
        self.created_at = created_at or parse_to_timestamp_ms_now()

    def to_dict(self):
        return {
            "corrector_id": self.corrector_id,
            "grade": self.grade,
            "comment": self.comment,
            "created_at": self.created_at
        }

    @staticmethod
    def from_dict(data: dict):
        return Feedback(
            corrector_id=data["corrector_id"],
            grade=data.get("grade"),
            comment=data.get("comment"),
            created_at=data.get("created_at")
        )

class Submission:
    def __init__(
        self,
        attachments: Optional[List[Dict[str, str]]] = None,
        feedbacks: Optional[Dict[str, Dict[str, Any]]] = None
    ):
        self.attachments = attachments or []
        self.feedbacks = {}
        if feedbacks:
            for corrector_id, feedback_data in feedbacks.items():
                self.feedbacks[corrector_id] = Feedback.from_dict(
                    feedback_data)

    def to_dict(self):
        return {
            "attachments": self.attachments,
            "feedbacks": {k: v.to_dict() for k, v in self.feedbacks.items()}
        }

    @staticmethod
    def from_dict(data: dict):
        return Submission(
            attachments=data.get("attachments", []),
            feedbacks=data.get("feedbacks", {})
        )
