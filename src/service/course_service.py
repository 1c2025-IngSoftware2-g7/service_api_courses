
from headers import COURSE_CREATED, COURSE_DELETED, COURSE_IS_FULL, COURSE_NOT_FOUND, INTERNAL_SERVER_ERROR, MISSING_FIELDS, UNAUTHORIZED
from error.error import error_generator
from models.course import Course
from models.module import Module


class CourseService:
    def __init__(self, course_repository, logger):
        self.course_repository = course_repository
        self.logger = logger

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
        data_required = ["name", "description", "start_date", "end_date", "max_students"]
        
        for field in data_required:
            if field not in data:
                return error_generator(
                    MISSING_FIELDS,
                    f"Field {field} is required",
                    400,
                    "update_course"
                )

        # Lets drop other fields that we don't want to update
        for field in list(data.keys()):
            if field not in data_required:
                del data[field]
        
        self.logger.debug(f"[DEBUG] data_required: {data_required}")
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
                    f"Course with ID {course_id} not modified or not found",
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
    
    def get_course(self, course_id):
        try:
            course = self.course_repository.get_course_by_id(course_id)
            self.logger.debug(f"[DEBUG] course searched: {course}")
            self.logger.debug(f"[DEBUG] course_id: [{course_id}]")
            if course:
                # we change the _id to str since isn't serializable
                course_as_json_response = Course.from_dict(course).to_dict()
                return {
                    "response": course_as_json_response,
                    "code_status": 200
                }
            else:
                return error_generator(
                    COURSE_NOT_FOUND,
                    f"Course with ID {course_id} not found",
                    404,
                    "get_course"
                )
        except Exception as e:
            return error_generator(
                INTERNAL_SERVER_ERROR,
                f"An error occurred while getting the course: {str(e)}",
                500,
                "get_course"
            )
            
    def search_course_by_query(self, string_to_find):
        try:
            courses = self.course_repository.search_course_by_partial_information(string_to_find)
            self.logger.debug(f"[DEBUG] courses searched: {courses}")
            self.logger.debug(f"[DEBUG] string_to_find: {string_to_find}")
            if courses:
                
                # We do this to print it propertly in the response
                courses = [ Course.from_dict(course).to_dict() for course in courses ]
                    
                return {
                    "response": courses,
                    "code_status": 200
                }
            else:
                return error_generator(
                    COURSE_NOT_FOUND,
                    f"No courses found with the search string {string_to_find}",
                    404,
                    "search_course"
                )
        except Exception as e:
            return error_generator(
                INTERNAL_SERVER_ERROR,
                f"An error occurred while searching for courses: {str(e)}",
                500,
                "search_course"
            )
            
    def get_all_courses(self):
        try:
            courses = self.course_repository.get_all_courses()
            if courses:
                # we make a fix to _id since isn't serializable
                courses = [ Course.from_dict(course).to_dict() for course in courses ]
                    
                return {
                    "response": courses,
                    "code_status": 200
                }
            else:
                return error_generator(
                    COURSE_NOT_FOUND,
                    f"No courses found",
                    404,
                    "get_all_courses"
                )
        except Exception as e:
            return error_generator(
                INTERNAL_SERVER_ERROR,
                f"An error occurred while getting all courses: {str(e)}",
                500,
                "get_all_courses"
            )
            
    def enroll_student_in_course(self, course_id, student_id):
        try:
            # First we check if the user is already enrolled in the course
            is_already_enrolled = self.course_repository.is_student_enrolled_in_course(course_id, student_id)
            
            if is_already_enrolled:
                return error_generator(
                    UNAUTHORIZED,
                    f"Student with ID {student_id} is already enrolled in course with ID {course_id}",
                    403,
                    "enroll_student"
                )
                
            # then we check if the course still has a place to enroll an user 
            still_has_place = self.course_repository.check_if_course_has_place(course_id)
            
            if not still_has_place:
                return error_generator(
                    COURSE_IS_FULL,
                    f"Course with ID {course_id} is full",
                    403,
                    "enroll_student"
                )

            enrolled = self.course_repository.enroll_student_in_course(course_id, student_id)
            if enrolled:
                return {
                    "response": {
                        "type": "about:blank",
                        "title": COURSE_CREATED,
                        "status": 200,
                        "detail": f"Student with ID {student_id} enrolled in course with ID {course_id}",
                        "instance": f"/courses/enroll/{course_id}"
                    },
                    "code_status": 200
                }
            else:
                return error_generator(
                    COURSE_NOT_FOUND,
                    f"Course with ID {course_id} not found",
                    404,
                    "enroll_student"
                )
        except Exception as e:
            return error_generator(
                INTERNAL_SERVER_ERROR,
                f"An error occurred while enrolling the student in the course: {str(e)}",
                500,
                "enroll_student"
            )
            
    def get_enrolled_courses(self, student_id):
        try:
            courses = self.course_repository.get_enrolled_courses(student_id)
            if courses:
                # we make a fix to _id since isn't serializable
                courses = [ Course.from_dict(course).to_dict() for course in courses ]
                    
                return {
                    "response": courses,
                    "code_status": 200
                }
            else:
                return error_generator(
                    COURSE_NOT_FOUND,
                    f"No courses found for student with ID {student_id}",
                    404,
                    "get_enrolled_courses"
                )
        except Exception as e:
            return error_generator(
                INTERNAL_SERVER_ERROR,
                f"An error occurred while getting the enrolled courses: {str(e)}",
                500,
                "get_enrolled_courses"
            )
    
    def add_module_to_course(self, course_id, data):
        data_required = ["title", "description", "url", "type"]
        for field in data_required:
            if field not in data:
                return error_generator(
                    MISSING_FIELDS,
                    f"Field {field} is required",
                    400,
                    "add_module_to_course"
                )
                
        # Lets drop other fields that we don't want to update
        for field in list(data.keys()):
            if field not in data_required:
                del data[field]
        
        try:
            new_module = Module(data["title"], data["description"], data["url"], data["type"])
            module_dict = new_module.to_dict()
            
            # Lets check beforehand if the course exists 
            course = self.course_repository.get_course_by_id(course_id)
            if not course:
                return error_generator(
                    COURSE_NOT_FOUND,
                    f"Course with ID {course_id} not found",
                    404,
                    "add_module_to_course"
                )
            
            module_added = self.course_repository.add_module_to_course(course_id, module_dict)
            if module_added:
                return {
                    "response": {
                        "type": "about:blank",
                        "title": COURSE_CREATED,
                        "status": 200,
                        "detail": f"Module added to course with ID {course_id}",
                        "instance": f"/courses/modules/{course_id}"
                    },
                    "code_status": 200
                }
            else:
                return error_generator(
                    COURSE_NOT_FOUND,
                    f"Course with ID {course_id} not found",
                    404,
                    "add_module_to_course"
                )
        except Exception as e:
            return error_generator(
                INTERNAL_SERVER_ERROR,
                f"An error occurred while adding the module to the course: {str(e)}",
                500,
                "add_module_to_course"
            )