

from src.error.error import error_generator
from src.headers import COURSE_NOT_FOUND, INTERNAL_SERVER_ERROR, MISSING_FIELDS, MODULE_MODIFIED, MODULE_WASNT_CREATED, UNAUTHORIZED, USER_NOT_ALLOWED_TO_CREATE
from src.models.module import Module
from src.repository.courses_repository import CoursesRepository
from src.repository.module_repository import ModuleRepository


class ModuleService:
    
    def __init__(self, repository_modules: ModuleRepository, repository_courses: CoursesRepository, logger):
        self.repository_modules = repository_modules
        self.repository_courses = repository_courses
        self.logger = logger
        
    def add_module_to_course(self, course_id, data):
        """
        Add a module to a course.
        Module comes as a json with
        title = title
        description = description
        """
        # Check if the course exists
        course = self.repository_courses.get_course_by_id(course_id)
        
        if not course:
            return error_generator(
                COURSE_NOT_FOUND, "Course not found", 404, "add_module_to_course"
            )
        
        owner_id = data.get("owner_course", None)
        
        if not owner_id:
            return error_generator(
                MISSING_FIELDS, "Owner ID is required", 400, "add_module_to_course"
            )
        
        is_allowed_user_to_create_module = self.repository_courses.is_user_allowed_to_create_module(
            course_id, owner_id
        )
        
        if not is_allowed_user_to_create_module:
            return error_generator(
                USER_NOT_ALLOWED_TO_CREATE, "User is not allowed to create module", 403, "add_module_to_course"
            )
        

        (title, description) = data.get("title"), data.get("description")
        
        if not title or not description:
            return error_generator(
                MISSING_FIELDS, "Title and description are required", 400, "add_module_to_course"
            )
            
        get_position = len(self.repository_modules.get_modules_from_course(course_id)) + 1
            
        module = Module.from_dict(
            {
                "title": title,
                "description": description,
                "position": get_position,
                "resources": [],
            }
        )
        
        # Add the module to the course
        module = self.repository_modules.add_module_to_course(course_id, module)
        
        if not module:
            return error_generator(
                MODULE_WASNT_CREATED, "Module not added", 400, "add_module_to_course"
            )
        
        return { "response": module.to_dict(), "code_status": 200 }
    
    def modify_module_in_course(self, course_id, module_id, owner_id, data):
        try:

            # Lets check beforehand if the course exists
            course = self.repository_courses.get_course_by_id(course_id)
            if not course:
                return error_generator(
                    COURSE_NOT_FOUND,
                    f"Course with ID {course_id} not found",
                    404,
                    "modify_module_in_course",
                )

            # Lets check beforehand if the module exists
            module = self.repository_courses.get_module_by_id(course_id, module_id)
            if not module:
                return error_generator(
                    COURSE_NOT_FOUND,
                    f"Module with ID {module_id} not found in course with ID {course_id}",
                    404,
                    "modify_module_in_course",
                )

            is_allowed_to_update = (
                self.repository_courses.is_user_allowed_to_create_module(
                    course_id, owner_id
                )
            )

            if not is_allowed_to_update:
                self.logger.debug(
                    f"[SERVICE] MODIFY MODULE: user with id {owner_id} is not the owner of the course with id {course_id}, return error"
                )
                return error_generator(
                    UNAUTHORIZED,
                    f"User with ID {owner_id} is not authorized to modify this module",
                    403,
                    "modify_module_in_course",
                )

            module_from_database = Module.from_dict(module)

            optional_modification_parameters = ["title", "description"]

            for field in list(data.keys()):
                if field not in optional_modification_parameters:
                    self.logger.debug(
                        f"[SERVICE] MODIFY MODULE: field {field} not found in data, so we drop it"
                    )
                    del data[field]
                else:  # if the data is present, we modify the module
                    module_from_database.__setattr__(field, data[field])

            self.logger.debug(
                f"[SERVICE] MODIFY MODULE: module from database: {module_from_database.to_dict()}"
            )

            self.course_repository.modify_module_in_course(
                module_from_database.to_dict(), course_id, module_id
            )
            self.logger.debug(f"[SERVICE] MODIFY MODULE: module modified")

            return {
                "response": {
                    "type": "about:blank",
                    "title": MODULE_MODIFIED,
                    "status": 200,
                    "detail": f"Module with ID {module_id} modified in course with ID {course_id}",
                    "instance": f"/courses/modules/{course_id}",
                },
                "code_status": 200,
            }
        except Exception as e:
            self.logger.error(f"[SERVICE] MODIFY MODULE: error: {e}")
            return error_generator(
                INTERNAL_SERVER_ERROR,
                f"An error occurred while modifying the module in the course: {str(e)}",
                500,
                "modify_module_in_course",
            )