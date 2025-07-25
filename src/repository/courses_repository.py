import os
from bson import ObjectId
from models.course import Course
from datetime import datetime, timedelta


class CoursesRepository:
    def __init__(self, collection, task_repository, logger):
        self.collection = collection
        self.task_repository = task_repository
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

    def is_user_owner(self, course_id, user_id):
        course = self.get_course_by_id(course_id)
        if course:
            return course.get("creator_id", None) == user_id
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
        courses = (
            self.collection.find({"status": "open"}).skip(offset).limit(max_per_page)
        )
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

    """def is_user_allowed_to_create_module(self, course_id, user_id: str = None):
        # A user is allowed to create a module if he is the owner of the course or if he is an assistant

        course = self.get_course_by_id(course_id)
        course = Course.from_dict(course).to_dict()

        if course:
            # Check if the user is the owner of the course
            if course.get("creator_id", None) == user_id:
                return True

            # The check is done on the user part now

            return False
        else:
            return False"""

    def remove_assistant_from_course(self, course_id, assistant_id):
        result = self.collection.update_one(
            {"_id": ObjectId(course_id)}, {"$pull": {"assistants": assistant_id}}
        )
        self.logger.debug(
            f"[REPOSITORY] Remove assistant {assistant_id} from course {course_id}"
        )
        return result.modified_count > 0

    """def get_module_by_id(self, course_id, module_id):
        course = self.get_course_by_id(course_id)
        
        if course:
            course = Course.from_dict(course).to_dict()
            
            self.logger.debug(f"[REPOSITORY COURSES] course searched on repository: {course}")
                    
            for module_from_course in course.get("modules", []):
                if module_from_course == module_id:
                    return module_from_course
                    
                 = Module.from_dict(module).to_dict()
                
                self.logger.debug(f"[REPOSITORY COURSES] module searched on repository: {module_as_dict}")
                
                if module_as_dict.get("_id") == module_id:
                    return module_as_dict

        return None
    """

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

    def remove_module_from_course(self, course_id, module_id):
        # This method is used to remove a module from a course
        # Course has a list of modules with the id inside.
        result = self.collection.update_one(
            {"_id": ObjectId(course_id)}, {"$pull": {"modules": module_id}}
        )
        return result.modified_count > 0

    def get_courses_by_student_id(self, student_id):
        try:
            query = {"students": student_id}
            courses = list(self.collection.find(query))
            return [Course.from_dict(course) for course in courses]
        except Exception as e:
            self.logger.error(
                f"Error fetching courses for student {student_id}: {str(e)}"
            )
            raise e

    def open_course(self, course_id, course_start_date, course_end_date):
        try:
            start_date = datetime.strptime(course_start_date, "%Y-%m-%d")
            end_date = datetime.strptime(course_end_date, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError(f"Invalid date format: {e}")

        if start_date >= end_date:
            raise ValueError("The start date must be before the end date")

        yesterday = (datetime.today() - timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        if start_date <= yesterday:
            raise ValueError("The start date cannot be earlier than the current date.")

        result = self.collection.update_one(
            {
                "_id": ObjectId(course_id),
                "status": "closed",  # Solo si estaba cerrado antes
            },
            {
                "$set": {
                    "status": "open",
                    "course_start_date": course_start_date,
                    "course_end_date": course_end_date,
                    "students": [],
                }
            },
        )

        if result.modified_count < 0:
            return None

        self.logger.debug(f"[REPOSITORY] UPDATE: Course with ID: {course_id} open")

        tasks = self.task_repository.get_tasks_by_course_ids([course_id])
        for task in tasks:
            task_id = task._id
            self.logger.debug(f"[REPOSITORY] Clean task: {task_id}")
            result = self.task_repository.clean_task(task_id)

        updated_course = self.collection.find_one({"_id": ObjectId(course_id)})
        return updated_course

    def close_course(self, course_id):
        result = self.collection.update_one(
            {"_id": ObjectId(course_id), "status": "open"},
            {
                "$set": {
                    "status": "closed",
                }
            },
        )

        if result.modified_count < 0:
            return None

        self.logger.debug(f"[REPOSITORY] UPDATE: Course with ID: {course_id} closed")
        updated_course = self.collection.find_one({"_id": ObjectId(course_id)})
        return updated_course
