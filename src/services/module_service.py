

from src.error.error import error_generator
from src.headers import COURSE_NOT_FOUND, MISSING_FIELDS, MODULE_WASNT_CREATED, USER_NOT_ALLOWED_TO_CREATE
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