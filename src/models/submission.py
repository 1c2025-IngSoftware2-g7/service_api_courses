from typing import List, Optional

class Submission:
    def __init__(
        self,
        attachment_links: List[str],
        feedback: Optional[str] = None
    ):
        self.attachment_links = attachment_links
        self.feedback = feedback

    def to_dict(self):
        return {
            "attachment_links": self.attachment_links,
            "feedback": self.feedback
        }

    @staticmethod
    def from_dict(data: dict):
        return Submission(
            attachment_links=data.get("attachment_links", []),
            feedback=data.get("feedback")
        )
