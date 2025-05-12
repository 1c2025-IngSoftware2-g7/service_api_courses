from bson import ObjectId
from datetime import datetime


class Course:
    def __init__(
        self,
        course_name: str,
        course_description: str,
        max_students: int,
        course_start_date: str,
        course_end_date: str,
        creator_id: str,
        creator_name: str,
        students: list = None,
        _id: ObjectId = None,
        resources: list = None,
        enroll_date_start: datetime = datetime.now(),
        enroll_date_end: str = None,
        assistants: list = None,
        correlatives_required_id: list = None,
    ):
        self._id = str(_id) if _id else ObjectId()
        self.name = course_name
        self.description = course_description
        self.max_students = max_students
        self.course_start_date = course_start_date
        self.course_end_date = course_end_date
        self.enroll_date_start = enroll_date_start
        # lets convert the str as datetime
        self.enroll_date_end = (
            datetime.strptime(enroll_date_end, "%Y-%m-%d") if enroll_date_end else None
        )
        self.creator_id = creator_id
        self.creator_name = creator_name
        self.students = students
        self.resources = resources if resources else []
        self.assistants = assistants if assistants else []
        self.correlatives_required_id = correlatives_required_id if correlatives_required_id else []

    def to_dict(self):
        return {
            "_id": self._id,
            "name": self.name,
            "description": self.description,
            "max_students": self.max_students,
            "course_start_date": self.course_start_date,
            "course_end_date": self.course_end_date,
            "enroll_date_start": self.enroll_date_start,
            "enroll_date_end": self.enroll_date_end,
            "creator_id": self.creator_id,
            "creator_name": self.creator_name,
            "students": self.students,
            "resources": self.resources,
            "assistants": self.assistants,
            "correlatives_required_id": self.correlatives_required_id,
        }

    @staticmethod
    def from_dict(data):
        return Course(
            _id=data.get("_id"),
            course_name=data.get("name"),
            course_description=data.get("description"),
            max_students=data.get("max_students"),
            course_start_date=data.get("course_start_date"),
            course_end_date=data.get("course_end_date"),
            enroll_date_end=data.get("enroll_date_end"),
            enroll_date_start=data.get("enroll_date_start"),
            creator_id=data.get("creator_id"),
            creator_name=data.get("creator_name"),
            students=data.get("students", []),
            resources=data.get("resources", []),
            assistants=data.get("assistants", []),
            correlatives_required_id=data.get("correlatives_required_id", []),
        )
