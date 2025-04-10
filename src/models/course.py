
class Course:
    def __init__(self, course_id: str, course_name: str, course_description: str, professor_id: str, students=None):
        self.course_id = course_id
        self.course_name = course_name
        self.course_description = course_description
        self.students = students if students is not None else []

    def to_dict(self):
        return {
            "course_id": self.course_id,
            "course_name": self.course_name,
            "course_description": self.course_description,
            "students": self.students
        }