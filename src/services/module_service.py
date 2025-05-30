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
    MODULE_REMOVED,
    MODULE_WASNT_CREATED,
    UNAUTHORIZED,
    USER_NOT_ALLOWED_TO_CREATE,
)
from models.module import Module
from repository.courses_repository import CoursesRepository
from repository.module_repository import ModuleRepository
from models.resource import Resource


class ModuleService:
    def __init__(
        self,
        repository_modules: ModuleRepository,
        repository_courses: CoursesRepository,
        service_users,
        logger,
    ):
        self.repository_modules = repository_modules
        self.repository_courses = repository_courses
        self.service_users = service_users
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
                MISSING_FIELDS,
                "Owner ID is required (id_creator)",
                400,
                "add_module_to_course",
            )

        has_permissions = self.service_users.check_assistants_permissions(
            course_id, owner_id, "ModulesAndResources"
        )
        is_owner_course = self.repository_courses.is_user_owner(course_id, owner_id)
        # Here we need to check if its either the owner of the course or an assistant
        self.logger.debug(
            f"[MODULE SERVICE] has_permissions as assistant? : {has_permissions} <<<<<======="
        )
        self.logger.debug(
            f"[MODULE SERVICE] is_owner_course? : {is_owner_course} <<<<<======="
        )

        if not has_permissions and not is_owner_course:
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

        module_id = module  # This returns the ID
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

            has_permissions = self.service_users.check_assistants_permissions(
                course_id, owner_id, "ModulesAndResources"
            )
            is_owner_course = self.repository_courses.is_user_owner(course_id, owner_id)
            # Here we need to check if its either the owner of the course or an assistant
            self.logger.debug(
                f"[MODULE SERVICE] has_permissions as assistant? : {has_permissions} <<<<<======="
            )
            self.logger.debug(
                f"[MODULE SERVICE] is_owner_course? : {is_owner_course} <<<<<======="
            )

            if not has_permissions and not is_owner_course:
                return error_generator(
                    USER_NOT_ALLOWED_TO_CREATE,
                    "User is not allowed to create module",
                    403,
                    "add_module_to_course",
                )

            self.logger.debug(f"[SERVICE MODULE] AT THIS POINT STILL WORKING")
            module_from_database = Module.from_dict(module)
            self.logger.debug(
                f"[SERVICE MODULE] MODIFY MODULE: module from database: {module_from_database.to_dict()}"
            )

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

        has_permissions = self.service_users.check_assistants_permissions(
            course_id, owner_id, "ModulesAndResources"
        )
        is_owner_course = self.repository_courses.is_user_owner(course_id, owner_id)
        # Here we need to check if its either the owner of the course or an assistant
        self.logger.debug(
            f"[MODULE SERVICE] has_permissions as assistant? : {has_permissions} <<<<<======="
        )
        self.logger.debug(
            f"[MODULE SERVICE] is_owner_course? : {is_owner_course} <<<<<======="
        )

        if not has_permissions and not is_owner_course:
            return error_generator(
                USER_NOT_ALLOWED_TO_CREATE,
                "User is not allowed to remove a module",
                403,
                "add_module_to_course",
            )

        # Delete the module from the course
        result = self.repository_modules.delete_module_from_course(course_id, module_id)

        # Now remove from courses collection
        result_from_courses = self.repository_courses.remove_module_from_course(
            course_id, module_id
        )

        if not result and not result_from_courses:
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

    def get_module_from_course(self, course_id, module_id):
        """
        Get a module from a course.
        """
        # Check if the course exists
        course = self.repository_courses.get_course_by_id(course_id)

        if not course:
            return error_generator(
                COURSE_NOT_FOUND,
                f"Course with ID {course_id} not found",
                404,
                "get_module_from_course",
            )

        # Check if the module exists
        module = self.repository_modules.get_module_by_id(course_id, module_id)

        if not module:
            return error_generator(
                MODULE_NOT_FOUND_IN_COURSE,
                f"Module with ID {module_id} not found in course with ID {course_id}",
                404,
                "get_module_from_course",
            )

        return {
            "response": module,
            "code_status": 200,
        }

    def get_resources_from_module(self, course_id, module_id):
        """
        Get all resources from a module.
        """
        # Check if the course exists
        course = self.repository_courses.get_course_by_id(course_id)

        if not course:
            return error_generator(
                COURSE_NOT_FOUND,
                f"Course with ID {course_id} not found",
                404,
                "get_resources_from_module",
            )

        # Check if the module exists
        module = self.repository_modules.get_module_by_id(course_id, module_id)

        if not module:
            return error_generator(
                MODULE_NOT_FOUND_IN_COURSE,
                f"Module with ID {module_id} not found in course with ID {course_id}",
                404,
                "get_resources_from_module",
            )

        # Get all resources from the module
        resources = self.repository_modules.get_resources_from_module(
            course_id, module_id
        )

        if not resources:
            return error_generator(
                MODULE_NOT_FOUND_IN_COURSE,
                f"No resources found in module with ID {module_id} in course with ID {course_id}",
                404,
                "get_resources_from_module",
            )

        return {
            "response": resources,
            "code_status": 200,
        }

    def get_resource_from_module(self, course_id, module_id, resource_id):
        """
        Get a resource from a module.
        """
        # Check if the course exists
        course = self.repository_courses.get_course_by_id(course_id)

        if not course:
            return error_generator(
                COURSE_NOT_FOUND,
                f"Course with ID {course_id} not found",
                404,
                "get_resource_from_module",
            )

        # Check if the module exists
        module = self.repository_modules.get_module_by_id(course_id, module_id)

        if not module:
            return error_generator(
                MODULE_NOT_FOUND_IN_COURSE,
                f"Module with ID {module_id} not found in course with ID {course_id}",
                404,
                "get_resource_from_module",
            )

        # Get the resource from the module
        resource = self.repository_modules.get_resource_from_module(
            course_id, module_id, resource_id
        )

        if not resource:
            return error_generator(
                MODULE_NOT_FOUND_IN_COURSE,
                f"Resource with ID {resource_id} not found in module with ID {module_id} in course with ID {course_id}",
                404,
                "get_resource_from_module",
            )

        return {
            "response": resource,
            "code_status": 200,
        }

    def add_resource_to_module(self, course_id, module_id, data, owner_id):
        """
        Add a resource to a module.
        """

        has_permissions = self.service_users.check_assistants_permissions(
            course_id, owner_id, "ModulesAndResources"
        )
        is_owner_course = self.repository_courses.is_user_owner(course_id, owner_id)
        # Here we need to check if its either the owner of the course or an assistant
        self.logger.debug(
            f"[MODULE SERVICE] has_permissions as assistant? : {has_permissions} <<<<<======="
        )
        self.logger.debug(
            f"[MODULE SERVICE] is_owner_course? : {is_owner_course} <<<<<======="
        )

        if not has_permissions and not is_owner_course:
            return error_generator(
                USER_NOT_ALLOWED_TO_CREATE,
                "User is not allowed to create module",
                403,
                "add_module_to_course",
            )

        # Check if the course exists
        course = self.repository_courses.get_course_by_id(course_id)

        if not course:
            return error_generator(
                COURSE_NOT_FOUND,
                f"Course with ID {course_id} not found",
                404,
                "add_resource_to_module",
            )

        # Check if the module exists
        module = self.repository_modules.get_module_by_id(course_id, module_id)

        if not module:
            return error_generator(
                MODULE_NOT_FOUND_IN_COURSE,
                f"Module with ID {module_id} not found in course with ID {course_id}",
                404,
                "add_resource_to_module",
            )

        required_fields = ["title", "source", "mimetype"]

        optional_fields = ["description"]

        # Lets drop the fields that are not in the required fields or optional fields
        for field in list(data.keys()):
            if field not in required_fields and field not in optional_fields:
                self.logger.debug(
                    f"[MODULE SERVICE] add_resource_to_module: field {field} not found in data, so we drop it"
                )
                del data[field]

        # Lets get the new position

        position = (
            len(self.repository_modules.get_resources_from_module(course_id, module_id))
            + 1
        )

        # Lets create a new Resource element
        resource = Resource.from_dict(data)
        resource.position = position

        if not "source" in data:
            return error_generator(
                MISSING_FIELDS,
                "Source",
                400,
                "add_resource_to_module",
            )

        # Add the resource to the module
        result = self.repository_modules.add_resource_to_module(
            course_id, module_id, resource.to_dict()
        )

        if not result:
            return error_generator(
                MODULE_NOT_FOUND_IN_COURSE,
                f"Resource not added to module with ID {module_id} in course with ID {course_id}",
                400,
                "add_resource_to_module",
            )

        return {
            "response": {
                "type": "about:blank",
                "title": MODULE_CREATED,
                "status": 200,
                "detail": f"Resource added to module with ID {module_id} in course with ID {course_id}",
                "instance": f"/courses/modules/{course_id}/resources/{result}",
            },
            "code_status": 200,
        }

    def delete_resource_from_module(self, course_id, module_id, resource_id, owner_id):

        has_permissions = self.service_users.check_assistants_permissions(
            course_id, owner_id, "ModulesAndResources"
        )
        is_owner_course = self.repository_courses.is_user_owner(course_id, owner_id)
        # Here we need to check if its either the owner of the course or an assistant
        self.logger.debug(
            f"[MODULE SERVICE] has_permissions as assistant? : {has_permissions} <<<<<======="
        )
        self.logger.debug(
            f"[MODULE SERVICE] is_owner_course? : {is_owner_course} <<<<<======="
        )

        if not has_permissions and not is_owner_course:
            return error_generator(
                USER_NOT_ALLOWED_TO_CREATE,
                "User is not allowed to create module",
                403,
                "add_module_to_course",
            )

        # Check if the course exists
        course = self.repository_courses.get_course_by_id(course_id)

        if not course:
            return error_generator(
                COURSE_NOT_FOUND,
                f"Course with ID {course_id} not found",
                404,
                "delete_resource_from_module",
            )

        # Check if the module exists
        module = self.repository_modules.get_module_by_id(course_id, module_id)

        if not module:
            return error_generator(
                MODULE_NOT_FOUND_IN_COURSE,
                f"Module with ID {module_id} not found in course with ID {course_id}",
                404,
                "delete_resource_from_module",
            )

        # Check if the resource exists
        resource = self.repository_modules.get_resource_from_module(
            course_id, module_id, resource_id
        )

        if not resource:
            return error_generator(
                MODULE_NOT_FOUND_IN_COURSE,
                f"Resource with ID {resource_id} not found in module with ID {module_id} in course with ID {course_id}",
                404,
                "delete_resource_from_module",
            )

        # Delete the resource from the module
        result = self.repository_modules.delete_resource_from_module(
            course_id, module_id, resource_id
        )

        if not result:
            return error_generator(
                MODULE_NOT_FOUND_IN_COURSE,
                f"Resource with ID {resource_id} not found in module with ID {module_id} in course with ID {course_id}",
                404,
                "delete_resource_from_module",
            )

        return {
            "response": {
                "type": "about:blank",
                "title": MODULE_REMOVED,
                "status": 200,
                "detail": f"Resource with ID {resource_id} deleted from module with ID {module_id} in course with ID {course_id}",
                "instance": f"/courses/modules/{course_id}/resources/{resource_id}",
            },
            "code_status": 200,
        }
