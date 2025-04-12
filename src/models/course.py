
from bson import ObjectId

class Course:
    def __init__(self, course_name: str, course_description: str, max_students: int, start_date: str, end_date: str, creator_id: str, students: list = None, _id: ObjectId = None, resources: list = None): 
        self._id = str(_id) if _id else ObjectId()
        self.name = course_name
        self.description = course_description
        self.max_students = max_students
        self.start_date = start_date
        self.end_date = end_date
        self.creator_id = creator_id
        self.students = students 
        self.resources = resources if resources else []

    def to_dict(self):
        return {
            "_id": self._id,
            "name": self.name,
            "description": self.description,
            "max_students": self.max_students,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "creator_id": self.creator_id,
            "students": self.students,
            "resources": self.resources
        }
    
    @staticmethod
    def from_dict(data):
        return Course(
            _id=data.get("_id"),
            course_name=data.get("name"),
            course_description=data.get("description"),
            max_students=data.get("max_students"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            creator_id=data.get("creator_id"),
            students=data.get("students", []),
            resources=data.get("resources", [])
        )