

class CourseService:
    def __init__(self, course_repository):
        self.course_repository = course_repository

    def get_all_courses(self):
        return self.course_repository.get_all_courses()

    def get_course_by_id(self, course_id):
        return self.course_repository.get_course_by_id(course_id)

    def create_course(self, course_data):
        return self.course_repository.create_course(course_data)

    def update_course(self, course_id, course_data):
        return self.course_repository.update_course(course_id, course_data)

    def delete_course(self, course_id):
        return self.course_repository.delete_course(course_id)