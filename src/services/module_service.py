import os
import sys
from error.error import error_generator
from headers import (
    COURSE_NOT_FOUND,
    INTERNAL_SERVER_ERROR,
    MISSING_FIELDS,
    MODULE_CREATED,
    MODULE_MODIFIED,
    MODULE_NOT_FOUND_IN_COURSE,
    MODULE_WASNT_CREATED,
    UNAUTHORIZED,
    USER_NOT_ALLOWED_TO_CREATE,
)
from models.module import Module
from repository.courses_repository import CoursesRepository
from repository.module_repository import ModuleRepository


class ModuleService:

    def __init__(
        self,
        repository_modules: ModuleRepository,
        repository_courses: CoursesRepository,
        logger,
    ):
        self.repository_modules = repository_modules
        self.repository_courses = repository_courses
        self.logger = logger
        
    def get_modules_from_course(self, course_id):
        """
        Get all modules from a course.
        """
        # Check if the course exists
        course = self.repository_courses.get_course_by_id(course_id)

        if not course:
            return error_generator(
                COURSE_NOT_FOUND, "Course not found", 404, "get_modules_from_course"
            )

        # Get all modules from the course
        modules = self.repository_modules.get_modules_from_course(course_id)

        if not modules:
            return error_generator(
                MODULE_NOT_FOUND_IN_COURSE,
                "No modules found in this course",
                404,
                "get_modules_from_course",
            )

        return {
            "response": modules,
            "code_status": 200,
        }

    def add_module_to_course(self, course_id, data, owner_id):
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

        if not owner_id:
            return error_generator(
                MISSING_FIELDS, "Owner ID is required (id_creator)", 400, "add_module_to_course"
            )

        is_allowed_user_to_create_module = (
            self.repository_courses.is_user_allowed_to_create_module(
                course_id, owner_id
            )
        )

        if not is_allowed_user_to_create_module:
            return error_generator(
                USER_NOT_ALLOWED_TO_CREATE,
                "User is not allowed to create module",
                403,
                "add_module_to_course",
            )

        (title, description) = data.get("title"), data.get("description")

        if not title or not description:
            return error_generator(
                MISSING_FIELDS,
                "Title and description are required",
                400,
                "add_module_to_course",
            )

        get_position = (
            len(self.repository_modules.get_modules_from_course(course_id)) + 1
        )
        
        self.logger.debug(f"[SERVICE MODULE] position to be placed: {get_position}")

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

        module_id = module # This returns the ID
        return {
                "response": {
                    "type": "about:blank",
                    "title": MODULE_CREATED,
                    "status": 200,
                    "detail": f"Module with ID {module_id} created on course with ID {course_id}",
                    "instance": f"/courses/modules/{course_id}",
                },
                "code_status": 200,
            }

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
            module = self.repository_modules.get_module_by_id(course_id, module_id)
            if not module:
                return error_generator(
                    MODULE_NOT_FOUND_IN_COURSE,
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
                    f"[SERVICE MODULES] MODIFY MODULE: user with id {owner_id} is not allowed to modify the module id {course_id}, return error"
                )
                return error_generator(
                    UNAUTHORIZED,
                    f"User with ID {owner_id} is not authorized to modify this module",
                    403,
                    "modify_module_in_course",
                )

            self.logger.debug(f"[SERVICE MODULE] AT THIS POINT STILL WORKING")
            module_from_database = Module.from_dict(module)
            self.logger.debug(f"[SERVICE MODULE] MODIFY MODULE: module from database: {module_from_database.to_dict()}")

            optional_modification_parameters = ["title", "description", "position"]

            for field in list(data.keys()):
                if field not in optional_modification_parameters:
                    self.logger.debug(
                        f"[SERVICE MODULE] MODIFY MODULE: field {field} not found in data, so we drop it"
                    )
                    del data[field]
                else:  # if the data is present, we modify the module
                    module_from_database.__setattr__(field, data[field])

            self.logger.debug(
                f"[SERVICE MODULE] MODIFY MODULE: module from database: {module_from_database.to_dict()}"
            )

            self.repository_modules.modify_module_in_course(
                module_from_database.to_dict(), course_id, module_id
            )
            self.logger.debug(f"[SERVICE MODULE] MODIFY MODULE: module modified")

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
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            self.logger.error(f"[SERVICE MODULE] MODIFY MODULE: error: {e}")
            return error_generator(
                INTERNAL_SERVER_ERROR,
                f"An error occurred while modifying the module in the course: {str(e)}",
                500,
                "modify_module_in_course",
            )

    def delete_module_from_course(self, course_id, module_id, owner_id):
        # Check if the course exists
        course = self.repository_courses.get_course_by_id(course_id)

        if not course:
            return error_generator(
                COURSE_NOT_FOUND,
                f"Course with ID {course_id} not found",
                404,
                "delete_module_from_course",
            )

        # Check if the module exists
        module = self.repository_modules.get_module_by_id(course_id, module_id)

        if not module:
            return error_generator(
                MODULE_NOT_FOUND_IN_COURSE,
                f"Module with ID {module_id} not found in course with ID {course_id}",
                404,
                "delete_module_from_course",
            )

        is_allowed_to_delete = (
            self.repository_courses.is_user_allowed_to_create_module(
                course_id, owner_id
            )
        )

        if not is_allowed_to_delete:
            return error_generator(
                UNAUTHORIZED,
                f"User with ID {owner_id} is not authorized to delete this module",
                403,
                "delete_module_from_course",
            )

        # Delete the module from the course
        result = self.repository_modules.delete_module_from_course(
            course_id, module_id
        )
        
        # Now remove from courses collection
        result_from_courses = self.repository_courses.remove_module_from_course(
            course_id, module_id
        )

        if not result or not result_from_courses:
            return error_generator(
                MODULE_NOT_FOUND_IN_COURSE,
                f"Module with ID {module_id} not found in course with ID {course_id}",
                404,
                "delete_module_from_course",
            )

        return {
            "response": {
                "type": "about:blank",
                "title": MODULE_REMOVED,
                "status": 200,
                "detail": f"Module with ID {module_id} deleted from course with ID {course_id}",
                "instance": f"/courses/modules/{course_id}",
            },
            "code_status": 200,
        }