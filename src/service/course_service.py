
from headers import COURSE_CREATED, COURSE_DELETED, COURSE_NOT_FOUND, INTERNAL_SERVER_ERROR, MISSING_FIELDS, UNAUTHORIZED
from error.error import error_generator
from models.course import Course


class CourseService:
    def __init__(self, course_repository):
        self.course_repository = course_repository

    def create_course(self, data):
        data_required = ["name", "description", "creator_id", "start_date", "end_date", "max_students"]
        for field in data_required:
            if field not in data:
                return error_generator(
                    MISSING_FIELDS,
                    f"Field {field} is required",
                    400,
                    None
                )

        course = Course(data["name"], data["description"], data["max_students"], data["start_date"], data["end_date"], creator_id=data["creator_id"])
        
        dict_course = course.to_dict()
        
        try :
            course_id = self.course_repository.create_course(dict_course)
            return {
                "response": {
                    "type": "about:blank",
                    "title": COURSE_CREATED,
                    "status": 201,
                    "detail": f"Course created with ID {course_id}",
                    "instance": f"/courses"
                },
                "code_status": 201
            }
        except Exception as e:
            return error_generator(
                INTERNAL_SERVER_ERROR,
                f"An error occurred while creating the course: {str(e)}",
                500,
                "create_course"
            )
        
    def update_course(self, course_id, data):
        data_required = ["name", "description", "professor_id", "start_date", "end_date", "max_students"]
        for field in data_required:
            if field not in data:
                return error_generator(
                    MISSING_FIELDS,
                    f"Field {field} is required",
                    400,
                    "update_course"
                )

        try:
            updated = self.course_repository.update_course(course_id, data)
            if updated:
                return {
                    "response": {
                        "type": "about:blank",
                        "title": COURSE_CREATED,
                        "status": 200,
                        "detail": f"Course with ID {course_id} updated successfully",
                        "instance": f"/courses/update/{course_id}"
                    },
                    "code_status": 200
                }
            else:
                return error_generator(
                    COURSE_NOT_FOUND,
                    f"Course with ID {course_id} not found",
                    404,
                    "update_course"
                )
        except Exception as e:
            return error_generator(
                INTERNAL_SERVER_ERROR,
                f"An error occurred while updating the course: {str(e)}",
                500,
                "update_course"
            )

    """ A course can be deleted only by the creator of the course. """
    def delete_course(self, course_id, owner_id):
        try:
            course_owner_from_db = self.course_repository.get_course_owner(course_id)
            
            if course_owner_from_db != owner_id:
                return error_generator(
                    UNAUTHORIZED,
                    f"User {owner_id} is not authorized to delete this course",
                    403,
                    "delete_course"
                )
            
            deleted = self.course_repository.delete_course(course_id)
            
            if deleted:
                return {
                    "response": {
                        "type": "about:blank",
                        "title": COURSE_DELETED,
                        "status": 200,
                        "detail": f"Course with ID {course_id} deleted successfully",
                        "instance": f"/courses/delete/{course_id}"
                    },
                    "code_status": 200
                }
            else:
                return error_generator(
                    COURSE_NOT_FOUND,
                    f"Course with ID {course_id} not found",
                    404,
                    "delete_course"
                )
        except Exception as e:
            return error_generator(
                INTERNAL_SERVER_ERROR,
                f"An error occurred while deleting the course: {str(e)}",
                500,
                "delete_course"
            )