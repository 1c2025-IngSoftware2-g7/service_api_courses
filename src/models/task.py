from datetime import datetime
from bson import ObjectId
from enum import Enum

from models.submission import Submission


class TaskStatus(str, Enum):
    INACTIVE = "inactivo"
    OPEN = "abierto"
    CLOSED = "cerrado"


class TaskType(str, Enum):
    TASK = "task"
    EXAM = "exam"


class Task:
    def __init__(
        self,
        title: str,
        due_date: datetime,
        course_id: str,
        description: str = "",
        instructions: str = "",
        status: TaskStatus = TaskStatus.INACTIVE,
        task_type: TaskType = TaskType.TASK,
        file_url: str = None,
        submissions: dict[str, Submission] = None,
        _id: ObjectId = None,
        created_at: datetime = datetime.now(),
        updated_at: datetime = datetime.now()
    ):
        self._id = _id if _id else ObjectId()
        self.title = title
        self.description = description
        self.instructions = instructions
        self.due_date = due_date
        self.course_id = course_id
        self.status = status
        self.task_type = task_type
        self.file_url = file_url
        self.submissions = submissions if submissions is not None else {}
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self):
        return {
            "_id": str(self._id),
            "title": self.title,
            "description": self.description,
            "instructions": self.instructions,
            "due_date": self.due_date,
            "course_id": self.course_id,
            "status": self.status.value,
            "task_type": self.task_type.value,
            "file_url": self.file_url,
            "submissions": {k: v.to_dict() for k, v in self.submissions.items()},
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @staticmethod
    def from_dict(data):
        submissions_data = data.get("submissions", {})
        submissions = {k: Submission.from_dict(v) for k, v in submissions_data.items()}

        return Task(
            _id=ObjectId(data["_id"]) if data.get("_id") else None,
            title=data["title"],
            description=data.get("description", ""),
            instructions=data.get("instructions", ""),
            due_date=data["due_date"],
            course_id=data["course_id"],
            status=TaskStatus(data.get("status", TaskStatus.INACTIVE)),
            task_type=TaskType(data.get("task_type", TaskType.TASK)),
            file_url=data.get("file_url"),
            submissions=submissions,
            created_at=data.get("created_at", datetime.now()),
            updated_at=data.get("updated_at", datetime.now())
        )
