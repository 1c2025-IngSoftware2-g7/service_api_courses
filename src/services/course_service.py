from headers import (
    ASSISTANT_ADDED,
    ASSISTANT_REMOVED,
    COURSE_CREATED,
    COURSE_DELETED,
    COURSE_IS_FULL,
    COURSE_NOT_FOUND,
    INTERNAL_SERVER_ERROR,
    MISSING_FIELDS,
    MODULE_CREATED,
    MODULE_MODIFIED,
    UNAUTHORIZED,
    USER_HAS_NOT_ENOUGH_CORRELATIVES_APPROVED_TO_ENROLL,
    USER_IS_ALREADY_AN_ASSISTANT,
    USER_NOT_ALLOWED_TO_ADD_ASSISTANT,
    USER_NOT_AN_ASSISTANT,
)
from error.error import error_generator
from models.course import Course
from models.module import Module
from repository.courses_repository import CoursesRepository


class CourseService:
    def __init__(self, course_repository: CoursesRepository, course_logger):
        self.course_repository = course_repository
        self.logger = course_logger

    def create_course(self, data):
        data_required = [
            "name",
            "description",
            "creator_id",
            "course_start_date",
            "course_end_date",
            "max_students",
            "creator_name",
        ]
        optional_data = ["enroll_date_end", "correlatives_required_id", "background"]

        for field in data_required:
            if field not in data:
                self.logger.debug(
                    f"[SERVICE] CREATE: field {field} not found in data, so we throw error"
                )
                return error_generator(
                    MISSING_FIELDS, f"Field {field} is required", 400, "create_course"
                )

        # lets drop other fields that doesn't exists either on data or optional_data
        for field in list(data.keys()):
            if field not in data_required and field not in optional_data:
                self.logger.debug(
                    f"[SERVICE] CREATE: field {field} not found in data, so we drop it"
                )
                del data[field]

        course = Course(
            data["name"],
            data["description"],
            data["max_students"],
            data["course_start_date"],
            data["course_end_date"],
            data["creator_id"],
            data["creator_name"],
            enroll_date_end=(
                data["enroll_date_end"] if "enroll_date_end" in data else None
            ),
            correlatives_required_id=(
                data["correlatives_required_id"]
                if "correlatives_required_id" in data
                else None
            ),
            background=(data["background"] if "background" in data else None),
        )

        dict_course = course.to_dict()

        try:
            course_id = self.course_repository.create_course(dict_course)
            self.logger.debug(f"[SERVICE] CREATE: course created with ID: {course_id}")
            return {
                "response": {
                    "data": course_id,
                    "type": "about:blank",
                    "title": COURSE_CREATED,
                    "status": 201,
                    "detail": f"Course created with ID {course_id}",
                    "instance": f"/courses",
                },
                "code_status": 201,
            }
        except Exception as e:
            self.logger.error(f"[Course Service Error] Error creating course: {e}")
            return error_generator(
                INTERNAL_SERVER_ERROR,
                f"An error occurred while creating the course: {str(e)}",
                500,
                "create_course",
            )

    def update_course(self, course_id, data, owner_id):
        optional_data = [
            "name",
            "description",
            "course_start_date",
            "course_end_date",
            "max_students",
            "background",
        ]

        if len(data.keys()) == 0:
            self.logger.debug(f"[SERVICE] UPDATE data is empty, so we throw error")
            return error_generator(
                MISSING_FIELDS, f"At least one field is required", 400, "update_course"
            )

        # Lets drop other fields that we don't want to update
        for field in list(data.keys()):
            if field not in optional_data:
                self.logger.debug(
                    f"[SERVICE] UPDATE: field {field} not found in data, so we drop it"
                )
                del data[field]

        self.logger.debug(f"[SERVICE] Update data_required: {optional_data}")
        try:

            # Lets check beforehand if the creator of the course is the same as the one who is trying to update it
            if not self.course_repository.is_user_owner(course_id, owner_id):
                self.logger.debug(
                    f"[SERVICE] Update: owner with id {owner_id} is not the owner of the course with id {course_id}, return error"
                )
                return error_generator(
                    UNAUTHORIZED,
                    f"User {owner_id} is not authorized to update this course",
                    403,
                    "update_course",
                )

            updated = self.course_repository.update_course(course_id, data)

            self.logger.debug(f"[SERVICE] Update: course updated: {updated}")
            if updated:
                return {
                    "response": {
                        "type": "about:blank",
                        "title": COURSE_CREATED,
                        "status": 200,
                        "detail": f"Course with ID {course_id} updated successfully",
                        "instance": f"/courses/update/{course_id}",
                    },
                    "code_status": 200,
                }
            else:
                return error_generator(
                    COURSE_NOT_FOUND,
                    f"Course with ID {course_id} not modified or not found",
                    404,
                    "update_course",
                )
        except Exception as e:
            self.logger.error(f"[Course Service Error] Error updating course: {e}")
            return error_generator(
                INTERNAL_SERVER_ERROR,
                f"An error occurred while updating the course: {str(e)}",
                500,
                "update_course",
            )

    """ A course can be deleted only by the creator of the course. """

    def delete_course(self, course_id, owner_id):
        try:
            if not self.course_repository.is_user_owner(course_id, owner_id):
                self.logger.debug(
                    f"[SERVICE] Delete: owner with id {owner_id} is not the owner of the course with id {course_id}, return error"
                )
                return error_generator(
                    UNAUTHORIZED,
                    f"User {owner_id} is not authorized to delete this course",
                    403,
                    "delete_course",
                )

            # Lets check if the course exists
            course_exists = self.course_repository.get_course_by_id(course_id)

            self.logger.debug(f"[SERVICE] Delete: course exists: {course_exists}")
            if not course_exists:
                self.logger.debug(
                    f"[SERVICE] Delete: course with id {course_id} not found, return error"
                )
                return error_generator(
                    COURSE_NOT_FOUND,
                    f"Course with ID {course_id} not found",
                    404,
                    "delete_course",
                )

            deleted = self.course_repository.delete_course(course_id)

            if deleted:

                self.logger.debug(f"[SERVICE] Delete: course deleted: {deleted}")
                return {
                    "response": {
                        "type": "about:blank",
                        "title": COURSE_DELETED,
                        "status": 200,
                        "detail": f"Course with ID {course_id} deleted successfully",
                        "instance": f"/courses/delete/{course_id}",
                    },
                    "code_status": 200,
                }
            else:
                return error_generator(
                    COURSE_NOT_FOUND,
                    f"Course with ID {course_id} not found",
                    404,
                    "delete_course",
                )
        except Exception as e:
            self.logger.error(f"[Course Service Error] Error deleting course: {e}")
            return error_generator(
                INTERNAL_SERVER_ERROR,
                f"An error occurred while deleting the course: {str(e)}",
                500,
                "delete_course",
            )

    def get_course(self, course_id):
        try:
            course = self.course_repository.get_course_by_id(course_id)
            self.logger.debug(f"[SERVICE] course searched: {course}")
            self.logger.debug(f"[SERVICE] course_id: [{course_id}]")
            if course:
                # we change the _id to str since isn't serializable
                course_as_json_response = Course.from_dict(course).to_dict()
                return {"response": course_as_json_response, "code_status": 200}
            else:
                return error_generator(
                    COURSE_NOT_FOUND,
                    f"Course with ID {course_id} not found",
                    404,
                    "get_course",
                )
        except Exception as e:
            self.logger.error(f"[Course Service Error] Error getting course: {e}")
            return error_generator(
                INTERNAL_SERVER_ERROR,
                f"An error occurred while getting the course: {str(e)}",
                500,
                "get_course",
            )

    def search_course_by_query(self, string_to_find):
        try:
            courses = self.course_repository.search_course_by_partial_information(
                string_to_find
            )
            self.logger.debug(f"[SERVICE] courses searched: {courses}")
            self.logger.debug(f"[SERVICE] string_to_find: {string_to_find}")
            if courses:

                # We do this to print it propertly in the response
                courses = [Course.from_dict(course).to_dict() for course in courses]

                return {"response": courses, "code_status": 200}
            else:
                return error_generator(
                    COURSE_NOT_FOUND,
                    f"No courses found with the search string {string_to_find}",
                    404,
                    "search_course",
                )
        except Exception as e:
            self.logger.error(f"[Course Service Error] Error searching course: {e}")
            return error_generator(
                INTERNAL_SERVER_ERROR,
                f"An error occurred while searching for courses: {str(e)}",
                500,
                "search_course",
            )

    def get_all_courses(self):
        try:
            courses = self.course_repository.get_all_courses()
            if courses:
                # we make a fix to _id since isn't serializable
                self.logger.debug(f"[SERVICE] courses searched: {courses}")
                courses = [Course.from_dict(course).to_dict() for course in courses]

                return {"response": courses, "code_status": 200}
            else:
                return error_generator(
                    COURSE_NOT_FOUND, f"No courses found", 404, "get_all_courses"
                )
        except Exception as e:
            self.logger.error(f"[Course Service Error] Error getting all courses: {e}")
            return error_generator(
                INTERNAL_SERVER_ERROR,
                f"An error occurred while getting all courses: {str(e)}",
                500,
                "get_all_courses",
            )

    def enroll_student_in_course(
        self, course_id, student_id, approved_signatures_from_user
    ):
        try:
            # We check if the course inscription is still open
            inscription_available = (
                self.course_repository.check_if_course_inscription_is_available(
                    course_id
                )
            )

            if not inscription_available:

                self.logger.debug(
                    f"[SERVICE] Enroll: inscription is not available for course with ID {course_id}"
                )
                return error_generator(
                    UNAUTHORIZED,
                    f"Course with ID {course_id} inscription is no longer available",
                    403,
                    "enroll_student",
                )

            # First we check if the user is already enrolled in the course
            is_already_enrolled = self.course_repository.is_student_enrolled_in_course(
                course_id, student_id
            )

            if is_already_enrolled:

                self.logger.debug(
                    f"[SERVICE] Enroll: student with ID {student_id} is already enrolled in course with ID {course_id}"
                )
                return error_generator(
                    UNAUTHORIZED,
                    f"Student with ID {student_id} is already enrolled in course with ID {course_id}",
                    403,
                    "enroll_student",
                )

            # then we check if the course still has a place to enroll an user
            still_has_place = (
                self.course_repository.check_if_course_has_place_to_enroll(course_id)
            )

            if not still_has_place:

                self.logger.debug(
                    f"[SERVICE] Enroll: course with ID {course_id} is full"
                )
                return error_generator(
                    COURSE_IS_FULL,
                    f"Course with ID {course_id} is full",
                    403,
                    "enroll_student",
                )

            # In order an user to be able to enroll in a course, the user MUST have the correlatives signatures approved.
            # We check if the user has ALL the correlatives approved from approved_signatures_from_user
            courses_correlatives = self.course_repository.get_course_correlatives(
                course_id
            )

            if (
                courses_correlatives
            ):  # if the course has correlatives, we need to check them, else we skip this step
                for assignatures_aproved in approved_signatures_from_user:
                    if assignatures_aproved not in courses_correlatives:
                        self.logger.debug(
                            f"[SERVICE] Enroll: student with ID {student_id} doesn't have the correlatives approved to enroll in course with ID {course_id}"
                        )
                        return error_generator(
                            USER_HAS_NOT_ENOUGH_CORRELATIVES_APPROVED_TO_ENROLL,
                            f"Student with ID {student_id} doesn't have the correlatives approved to enroll in course with ID {course_id}",
                            403,
                            "enroll_student",
                        )

            enrolled = self.course_repository.enroll_student_in_course(
                course_id, student_id
            )
            if enrolled:
                self.logger.debug(
                    f"[SERVICE] Enroll: student with ID {student_id} enrolled in course with ID {course_id}"
                )
                return {
                    "response": {
                        "type": "about:blank",
                        "title": COURSE_CREATED,
                        "status": 200,
                        "detail": f"Student with ID {student_id} enrolled in course with ID {course_id}",
                        "instance": f"/courses/enroll/{course_id}",
                    },
                    "code_status": 200,
                }
            else:
                return error_generator(
                    COURSE_NOT_FOUND,
                    f"Course with ID {course_id} not found",
                    404,
                    "enroll_student",
                )
        except Exception as e:
            self.logger.error(
                f"[Course Service Error] Error enrolling student in course: {e}"
            )
            return error_generator(
                INTERNAL_SERVER_ERROR,
                f"An error occurred while enrolling the student in the course: {str(e)}",
                500,
                "enroll_student",
            )

    def get_enrolled_courses(self, student_id):
        try:
            courses = self.course_repository.get_enrolled_courses(student_id)
            if courses:
                # we make a fix to _id since isn't serializable
                courses = [Course.from_dict(course).to_dict() for course in courses]

                self.logger.debug(f"[SERVICE] courses searched: {courses}")
                return {"response": courses, "code_status": 200}
            else:
                return error_generator(
                    COURSE_NOT_FOUND,
                    f"No courses found for student with ID {student_id}",
                    404,
                    "get_enrolled_courses",
                )
        except Exception as e:
            self.logger.error(
                f"[Course Service Error] Error getting enrolled courses: {e}"
            )
            return error_generator(
                INTERNAL_SERVER_ERROR,
                f"An error occurred while getting the enrolled courses: {str(e)}",
                500,
                "get_enrolled_courses",
            )

    def add_module_to_course(self, course_id, data):
        data_required = ["title", "description", "url", "type", "owner_id"]
        for field in data_required:
            if field not in data:
                return error_generator(
                    MISSING_FIELDS,
                    f"Field {field} is required",
                    400,
                    "add_module_to_course",
                )

        # Lets drop other fields that we don't want to update
        for field in list(data.keys()):
            if field not in data_required:
                self.logger.debug(
                    f"[SERVICE] ADD MODULE: field {field} not found in data, so we drop it"
                )
                del data[field]

        owner_course = data["owner_id"]

        # Lets check if the course exists
        course = self.course_repository.get_course_by_id(course_id)
        if not course:
            return error_generator(
                COURSE_NOT_FOUND,
                f"Course with ID {course_id} not found",
                404,
                "add_module_to_course",
            )
        # Lets check beforehand if the user is the owner of the course
        is_user_allowed_to_add_module = (
            self.course_repository.is_user_allowed_to_create_module(
                course_id, owner_course
            )
        )

        if not is_user_allowed_to_add_module:
            self.logger.debug(
                f"[SERVICE] ADD MODULE: user with id {owner_course} is not the owner of the course with id {course_id}, return error"
            )
            return error_generator(
                UNAUTHORIZED,
                f"User with ID {owner_course} is not authorized to add a module to this course",
                403,
                "add_module_to_course",
            )

        try:
            # A module can only be created by an user who is the owner or assistant
            new_module = Module(
                data["title"], data["description"], data["url"], data["type"]
            )
            module_dict = new_module.to_dict()

            module_added = self.course_repository.add_module_to_course(
                course_id, module_dict
            )
            if module_added:
                return {
                    "response": {
                        "type": "about:blank",
                        "title": MODULE_CREATED,
                        "status": 200,
                        "detail": f"Module added to course with ID {course_id}",
                        "instance": f"/courses/modules/{course_id}",
                    },
                    "code_status": 200,
                }
            else:
                return error_generator(
                    COURSE_NOT_FOUND,
                    f"Course with ID {course_id} not found",
                    404,
                    "add_module_to_course",
                )
        except Exception as e:
            self.logger.error(
                f"[Course Service Error] Error adding module to course: {e}"
            )
            return error_generator(
                INTERNAL_SERVER_ERROR,
                f"An error occurred while adding the module to the course: {str(e)}",
                500,
                "add_module_to_course",
            )

    def get_paginated_courses(self, offset, max_per_page):
        try:
            courses = self.course_repository.get_paginated_courses(offset, max_per_page)
            if courses:
                # we make a fix to _id since isn't serializable
                courses = [Course.from_dict(course).to_dict() for course in courses]

                return {"response": courses, "code_status": 200}
            else:
                return error_generator(
                    COURSE_NOT_FOUND, f"No courses found", 404, "get_paginated_courses"
                )
        except Exception as e:
            self.logger.error(
                f"[Course Service Error] Error getting paginated courses: {e}"
            )
            return error_generator(
                INTERNAL_SERVER_ERROR,
                f"An error occurred while getting the paginated courses: {str(e)}",
                500,
                "get_paginated_courses",
            )

    def get_course_by_id(self, course_id):
        try:
            course = self.course_repository.get_course_by_id(course_id)
            if course:
                # we make a fix to _id since isn't serializable
                course = Course.from_dict(course).to_dict()

                return {"response": course, "code_status": 200}
            else:
                return error_generator(
                    COURSE_NOT_FOUND,
                    f"Course with ID {course_id} not found",
                    404,
                    "get_course_by_id",
                )
        except Exception as e:
            self.logger.error(f"[Course Service Error] Error getting course by ID: {e}")
            return error_generator(
                INTERNAL_SERVER_ERROR,
                f"An error occurred while getting the course by ID: {str(e)}",
                500,
                "get_course_by_id",
            )

    def get_courses_owned_by_user(self, user_id, offset=0, max_per_page=1000):
        try:
            courses = self.course_repository.get_courses_owned_by_user(
                user_id, offset, max_per_page
            )

            if not courses:
                return []

            return [Course.from_dict(course) for course in courses]

        except Exception as e:
            self.logger.error(f"[Service Error] Error getting courses: {e}")
            raise e

    def add_assistant_to_course(self, course_id, assistant_id, owner_id):
        # Check if the course exists
        course = self.course_repository.get_course_by_id(course_id)

        if not course:
            return error_generator(
                "Course not found", COURSE_NOT_FOUND, 404, "add_assistant_to_course"
            )

        # Check if the user is the owner of the course
        course = Course.from_dict(course)

        if course.creator_id != owner_id:
            return error_generator(
                "User is not the owner of the course",
                USER_NOT_ALLOWED_TO_ADD_ASSISTANT,
                403,
                "add_assistant_to_course",
            )

        # Check if the assistant is already in the course
        if assistant_id in course.assistants:
            return error_generator(
                "Assistant already in course",
                USER_IS_ALREADY_AN_ASSISTANT,
                400,
                "add_assistant_to_course",
            )

        # now lets add it to the course
        success = self.course_repository.add_assistant_to_course(course_id, assistant_id)

        if not success:
            return error_generator(
                COURSE_NOT_FOUND,
                f"Course with ID {course_id} not found",
                404,
                "/courses/add_assistant"
            )

        return {
            "response": {
                "type": "about:blank",
                "title": ASSISTANT_ADDED,
                "status": 200,
                "detail": f"Assistant with ID {assistant_id} added to course with ID {course_id}",
                "instance": f"/courses/assistants/{course_id}",
            },
            "code_status": 200,
        }

    def remove_assistant_from_course(self, course_id, assistant_id, owner_id):
        # Check if the course exists
        try:
            course = self.course_repository.get_course_by_id(course_id)

            if not course:
                return error_generator(
                    "Course not found",
                    COURSE_NOT_FOUND,
                    404,
                    "remove_assistant_from_course",
                )

            # Check if the user is the owner of the course
            course = Course.from_dict(course)

            if course.creator_id != owner_id:
                return error_generator(
                    "User is not the owner of the course",
                    USER_NOT_ALLOWED_TO_ADD_ASSISTANT,
                    403,
                    "remove_assistant_from_course",
                )

            # Check if the assistant is already in the course
            if assistant_id not in course.assistants:
                return error_generator(
                    "Assistant not in course",
                    USER_NOT_AN_ASSISTANT,
                    400,
                    "remove_assistant_from_course",
                )

            # now lets remove it from the course
            self.course_repository.remove_assistant_from_course(course_id, assistant_id)

            return {
                "response": {
                    "type": "about:blank",
                    "title": ASSISTANT_REMOVED,
                    "status": 200,
                    "detail": f"Assistant with ID {assistant_id} removed from course with ID {course_id}",
                    "instance": f"/courses/assistants/{course_id}",
                },
                "code_status": 200,
            }
        except Exception as e:
            return error_generator(
                INTERNAL_SERVER_ERROR,
                f"An error occurred while remove assistant: {str(e)}",
                500,
                "remove_assistant",
            )


    def get_students_in_course(self, course_id):
        # Check if the course exists
        course = self.course_repository.get_course_by_id(course_id)

        if not course:
            return error_generator(
                "Course not found", COURSE_NOT_FOUND, 404, "get_students_in_course"
            )

        students = self.course_repository.get_students_in_course(course_id)

        return {
            "response": students,
            "code_status": 200,
        }

    def remove_student_from_course(self, course_id, student_id):
        self.course_repository.remove_student_from_course(course_id, student_id)

    def is_user_owner_of_course(self, course_id, user_id):
        return self.course_repository.is_user_owner(course_id, user_id)

    def get_courses_by_student_id(self, student_id):
        return self.course_repository.get_courses_by_student_id(student_id)
