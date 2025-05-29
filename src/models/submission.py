from typing import Optional

class Submission:
    def __init__(
        self,
        file_link: str,
        feedback: Optional[str] = None
    ):
        self.file_link = file_link
        self.feedback = feedback

    def to_dict(self):
        return {
            "file_link": self.file_link,
            "feedback": self.feedback
        }

    @staticmethod
    def from_dict(data: dict):
        return Submission(
            file_link=data.get("file_link"),
            feedback=data.get("feedback")
        )
