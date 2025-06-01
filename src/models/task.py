from bson import ObjectId
from enum import Enum
from typing import Optional

from models.submission import Submission
from utils import parse_date_to_timestamp_ms, parse_to_timestamp_ms_now


class TaskStatus(str, Enum):
    # for teachers:
    INACTIVE = "inactive"
    OPEN = "open"
    CLOSED = "closed"
    # for students:
    COMPLETED = "completed"
    OVERDUE = "overdue"
    PENDING = "pending"


class TaskType(str, Enum):
    TASK = "task"
    EXAM = "exam"


class Task:
    def __init__(
        self,
        title: str,
        due_date: Optional[int],  # timestamp ms
        course_id: str,
        module_id: str,
        description: str = "",
        instructions: str = "",
        status: TaskStatus = TaskStatus.INACTIVE,
        task_type: TaskType = TaskType.TASK,
        file_url: Optional[str] = None,
        submissions: Optional[dict[str, Submission]] = None,
        _id: Optional[ObjectId] = None,
        created_at: Optional[int] = None,  # timestamp ms
        updated_at: Optional[int] = None,  # timestamp ms
    ):
        self._id = _id if _id else ObjectId()
        self.title = title
        self.description = description
        self.instructions = instructions
        self.due_date = due_date
        self.course_id = course_id
        self.module_id = module_id
        self.status = status
        self.task_type = task_type
        self.file_url = file_url
        self.submissions = submissions if submissions is not None else {}
        self.created_at = (
            created_at if created_at is not None else parse_to_timestamp_ms_now()
        )
        self.updated_at = (
            updated_at if updated_at is not None else parse_to_timestamp_ms_now()
        )

    def to_dict(self):
        return {
            "_id": str(self._id),
            "title": self.title,
            "description": self.description,
            "instructions": self.instructions,
            "due_date": self.due_date,
            "course_id": self.course_id,
            "module_id": self.module_id,
            "status": self.status.value,
            "task_type": self.task_type.value,
            "file_url": self.file_url,
            "submissions": {k: v.to_dict() for k, v in self.submissions.items()},
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(data: dict):
        submissions_data = data.get("submissions", {})
        submissions = {k: Submission.from_dict(v) for k, v in submissions_data.items()}

        return Task(
            _id=ObjectId(data["_id"]) if data.get("_id") else None,
            title=data["title"],
            description=data.get("description", ""),
            instructions=data.get("instructions", ""),
            due_date=parse_date_to_timestamp_ms(data.get("due_date")),
            course_id=data["course_id"],
            module_id=data["module_id"],
            status=TaskStatus(data.get("status", TaskStatus.INACTIVE)),
            task_type=TaskType(data.get("task_type", TaskType.TASK)),
            file_url=data.get("file_url"),
            submissions=submissions,
            created_at=parse_date_to_timestamp_ms(data.get("created_at")),
            updated_at=parse_date_to_timestamp_ms(data.get("updated_at")),
        )
