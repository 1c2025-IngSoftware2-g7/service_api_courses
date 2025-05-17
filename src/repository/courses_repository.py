import os
from bson import ObjectId
from models.course import Course
from datetime import datetime


class CoursesRepository:
    def __init__(self, collection, logger):
        self.collection = collection
        self.logger = logger

    def create_course(self, course_dict):
        course_dict["students"] = []
        course_dict["modules"] = []
        result = self.collection.insert_one(course_dict)

        self.logger.debug(
            f"[REPOSITORY] CREATE: New course created with ID: {result.inserted_id}"
        )
        return str(result.inserted_id)

    def update_course(self, course_id, course_dict):
        result = self.collection.update_one(
            {"_id": ObjectId(course_id)}, {"$set": course_dict}
        )
        self.logger.debug(f"[REPOSITORY] UPDATE: Course with ID: {course_id} updated")
        return result.modified_count > 0

    def delete_course(self, course_id):
        result = self.collection.delete_one({"_id": ObjectId(course_id)})
        self.logger.debug(f"[REPOSITORY] DELETE: Course with ID: {course_id} deleted")
        return result.deleted_count > 0

    def get_course_by_id(self, course_id):
        object_id = ObjectId(course_id)
        self.logger.debug(
            f"[REPOSITORY] course_id: {course_id} - object_id: {object_id}"
        )
        course = self.collection.find_one({"_id": object_id})

        self.logger.debug(f"[REPOSITORY] course searched on repository: {course}")

        # we convert the course to a Course instance
        if course:
            return course
        else:
            return None

    def search_course_by_partial_information(self, string_to_find):
        # We need to search in the course name and description and creator name, we skip if the string is empty or none
        # We need to use regex to find the string in the name and description

        regex = {"$regex": string_to_find, "$options": "i"}
        courses = self.collection.find(
            {
                "$or": [
                    {"name": regex},
                    {"description": regex},
                    {"course_start_date": regex},
                    {"course_end_date": regex},
                    {"creator_name": regex},
                ]
            }
        )

        self.logger.debug(f"[REPOSITORY] courses searched on repository: {courses}")
        return list(courses)

    def get_list_of_students_for_course(self, course_id):
        course = self.get_course_by_id(course_id)
        if course:
            return course.get("students", [])
        else:
            return None

    def enroll_student_in_course(self, course_id, student_id):
        result = self.collection.update_one(
            {"_id": ObjectId(course_id)}, {"$addToSet": {"students": student_id}}
        )
        self.logger.debug(
            f"[REPOSITORY] Enroll student {student_id} in course {course_id}"
        )
        return result.modified_count > 0

    def remove_student_from_course(self, course_id, student_id):
        result = self.collection.update_one(
            {"_id": course_id}, {"$pull": {"students": student_id}}
        )
        return result.modified_count > 0

    """ This method is used to find all courses that a student is enrolled in. """

    def find_by_student_id(self, student_id):
        courses = self.collection.find({"students": student_id})
        return list(courses)

    """ This method is used to find all courses that a student is enrolled in. """

    def get_course_owner(self, course_id):
        course = self.get_course_by_id(course_id)
        if course:
            return course.get("creator_id")
        else:
            return None

    """ This method is used to know if a player is already enrolled in a course. """

    def is_student_enrolled_in_course(self, course_id, student_id):
        course = self.get_course_by_id(course_id)
        if course:
            return student_id in course.get("students", [])
        else:
            return False

    def get_all_courses(self):
        courses = self.collection.find()
        return list(courses)

    def get_enrolled_courses(self, student_id):
        courses = self.collection.find({"students": student_id})
        return list(courses)

    def check_if_course_has_place_to_enroll(self, course_id):
        course = self.get_course_by_id(course_id)
        if course:
            return len(course.get("students", [])) < course.get("max_students", 0)
        else:
            return False

    def get_paginated_courses(self, offset, max_per_page):
        courses = self.collection.find().skip(offset).limit(max_per_page)
        return list(courses)

    def check_if_course_inscription_is_available(self, course_id):
        course = self.get_course_by_id(course_id)
        if course:
            # In case enroll_date_end is None, we assume the course is open for enrollment
            # So in that case, the enrollment is available, else, we check if the enroll_date_end is greater than now
            if course.get("enroll_date_end") is None:
                self.logger.debug(
                    f"[REPOSITORY] Course {course_id} has no end date for enrollment, so it is available"
                )
                return True
            else:
                self.logger.debug(
                    f"[REPOSITORY] Course {course_id} has an end date for enrollment, so we check if it is available"
                )
                return (
                    course.get("enroll_date_start")
                    <= datetime.now()
                    <= course.get("enroll_date_end")
                )
        else:
            return False

    def get_courses_owned_by_user(self, user_id, offset, max_per_page):
        # An owner of the course is either the creator or its assistant
        """courses = (
            self.collection.find({"creator_id": user_id})
            .skip(offset)
            .limit(max_per_page)
        )"""
        courses = (
            self.collection.find(
                {"$or": [{"creator_id": user_id}, {"assistants": user_id}]}
            )
            .skip(offset)
            .limit(max_per_page)
        )

        return list(courses)

    def add_assistant_to_course(self, course_id, assistant_id):
        result = self.collection.update_one(
            {"_id": ObjectId(course_id)}, {"$addToSet": {"assistants": assistant_id}}
        )
        self.logger.debug(
            f"[REPOSITORY] Add assistant {assistant_id} to course {course_id}"
        )
        return result.modified_count > 0

    def is_user_allowed_to_create_module(self, course_id, user_id):
        # A user is allowed to create a module if he is the owner of the course or if he is an assistant

        course = self.get_course_by_id(course_id)

        if course:
            # Check if the user is the owner of the course
            if course.get("creator_id") == user_id:
                return True

            # Check if the user is an assistant
            if user_id in course.get("assistants", []):
                return True

            return False
        else:
            return False

    def remove_assistant_from_course(self, course_id, assistant_id):
        result = self.collection.update_one(
            {"_id": ObjectId(course_id)}, {"$pull": {"assistants": assistant_id}}
        )
        self.logger.debug(
            f"[REPOSITORY] Remove assistant {assistant_id} from course {course_id}"
        )
        return result.modified_count > 0

    def get_module_by_id(self, course_id, module_id):
        course = self.get_course_by_id(course_id)
        if course:
            for module in course.get("resources", []):
                if module.get("_id") == module_id:
                    return module

        return None

    def modify_module_in_course(self, module_modified_as_dict, course_id, module_id):
        self.collection.update_one(
            {"_id": ObjectId(course_id), "resources._id": module_id},
            {"$set": {"resources.$": module_modified_as_dict}},
        )

    def delete_module_from_course(self, course_id, module_id):
        self.collection.update_one(
            {"_id": ObjectId(course_id)},
            {"$pull": {"resources": {"_id": module_id}}},
        )

    def get_course_correlatives(self, course_id):
        course = self.get_course_by_id(course_id)
        if course:
            return course.get("correlatives_required_id", [])
        else:
            return None

    def remove_student_from_course(self, course_id, student_id):
        result = self.collection.update_one(
            {"_id": ObjectId(course_id)}, {"$pull": {"students": student_id}}
        )
        self.logger.debug(
            f"[DEBUG] Remove student {student_id} from course {course_id}"
        )
        return result.modified_count > 0

    def get_course_correlatives_by_id(self, course_id):
        course = self.get_course_by_id(course_id)
        if course:
            return course.get("correlatives_required_id", [])
        else:
            return None

    def get_students_in_course(self, course_id):
        course = self.get_course_by_id(course_id)
        if course:
            return course.get("students", [])
        else:
            return None
