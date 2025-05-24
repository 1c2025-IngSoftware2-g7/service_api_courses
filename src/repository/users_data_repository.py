from bson import ObjectId
from headers import MISSING_FIELDS


class UsersDataRepository:
    def __init__(self, collection_users, user_approved_courses_collection, logger):
        self.collection = collection_users
        self.user_approved_courses_collection = user_approved_courses_collection
        self.logger = logger

    # This function will set a favourite course for a certain user
    def set_favourite_course(self, course_id, student_id):
        self.logger.debug(
            f"[REPOSITORY] Setting course with ID: {course_id} as favourite for student with ID: {student_id}"
        )

        user_exists_on_collection = self.collection.find_one({"student_id": student_id})

        if not user_exists_on_collection:
            # If it isnt' we add it.
            self.collection.insert_one(
                {"student_id": student_id, "favourite_courses": [course_id]},
            )
        else:
            # If it is, we update the field
            self.collection.update_one(
                {"student_id": student_id},
                {"$addToSet": {"favourite_courses": course_id}},
            )

        self.logger.debug(
            f"[REPOSITORY] Course with ID: {course_id} set as favourite for student with ID: {student_id}"
        )

        return True

    def remove_course_from_favourites(self, course_id, student_id):
        """
        Remove a course from the favourites list.
        """
        self.logger.debug(
            f"[REPOSITORY] Removing course with ID: {course_id} from favourites for student with ID: {student_id}"
        )

        user = self.collection.find_one({"student_id": student_id})

        if not user:
            self.logger.debug(
                f"[REPOSITORY] User with ID: {student_id} not found in the database"
            )
            return False

        if course_id not in user["favourite_courses"]:
            self.logger.debug(
                f"[REPOSITORY] Course with ID: {course_id} is not in the favourites list for student with ID: {student_id}"
            )
            return False

        self.collection.update_one(
            {"student_id": student_id},
            {"$pull": {"favourite_courses": course_id}},
        )

        self.logger.debug(
            f"[REPOSITORY] Course with ID: {course_id} removed from favourites for student with ID: {student_id}"
        )

        return True

    def course_already_favourite(self, course_id, student_id):
        """
        Check if a course is already favourite for a student.
        """
        self.logger.debug(
            f"[REPOSITORY] Checking if course with ID: {course_id} is favourite for student with ID: {student_id}"
        )

        user = self.collection.find_one({"student_id": student_id})

        if not user:
            self.logger.debug(
                f"[REPOSITORY] User with ID: {student_id} not found in the database"
            )
            return False

        if course_id in user["favourite_courses"]:
            return True

        return False

    def get_favourites_from_student_id(self, student_id):
        """
        Get the favourite courses for a student.
        """
        self.logger.debug(
            f"[REPOSITORY] Getting favourite courses for student with ID: {student_id}"
        )

        user = self.collection.find_one({"student_id": student_id})

        return user["favourite_courses"] if user else None

    def check_student_enrollment(self, student_id, course_id, list_students_in_course):
        """
        Check if a student is enrolled in a course.
        returns true if the user is enrolled in the course
        """
        self.logger.debug(
            f"[REPOSITORY] Checking if student with ID: {student_id} is enrolled in course with ID: {course_id}"
        )

        self.logger.debug(
            f"[REPOSITORY] List of students in course: {list_students_in_course}"
        )

        if student_id in list_students_in_course:
            self.logger.debug(
                f"[REPOSITORY] Student with ID: {student_id} is already enrolled in course with ID: {course_id}"
            )
            return True

        self.logger.debug(
            f"[REPOSITORY] Student with ID: {student_id} is not enrolled in course with ID: {course_id}"
        )
        return False

    def approve_student(self, course_id, student_id):
        """
        Approve a student in a course.
        """
        self.logger.debug(
            f"[REPOSITORY] Approving student with ID: {student_id} in course with ID: {course_id}"
        )

        user = self.user_approved_courses_collection.find_one(
            {"student_id": student_id}
        )

        if not user:
            # If it isn't we add it.
            self.user_approved_courses_collection.insert_one(
                {"student_id": student_id, "approved_courses": [course_id]},
            )
        else:
            # If it is, we update the field
            self.user_approved_courses_collection.update_one(
                {"student_id": student_id},
                {"$addToSet": {"approved_courses": course_id}},
            )

        self.logger.debug(
            f"[REPOSITORY] Student with ID: {student_id} approved in course with ID: {course_id}"
        )

        return True

    def get_student_approved_courses(self, student_id):
        """
        Get the approved courses for a student.
        """
        self.logger.debug(
            f"[REPOSITORY] Getting approved courses for student with ID: {student_id}"
        )

        user = self.user_approved_courses_collection.find_one(
            {"student_id": student_id}
        )

        return user["approved_courses"] if user else []

    def get_approved_signatures(self, student_id):
        """
        Get the approved signatures for a student.
        """
        self.logger.debug(
            f"[REPOSITORY] Getting approved signatures for student with ID: {student_id}"
        )

        user = self.user_approved_courses_collection.find_one(
            {"student_id": student_id}
        )

        if not user:
            return None

        return list(user["approved_courses"]) if user else None

    def check_assistant_already_in_course(self, course_id, assistant_id):
        """
        Check if an assistant is in a course.
        A user is an assistant if first contains the value "assistant" and it contains as key the course_id.

        """

        self.logger.debug(
            f"[REPOSITORY] Checking if assistant with ID: {assistant_id} is in course with ID: {course_id}"
        )

        user = self.collection.find_one({"student_id": assistant_id})

        if not user:
            self.logger.debug(
                f"[REPOSITORY] User with ID: {assistant_id} not found in the database, so doesn't exist"
            )
            return False

        if "assistant" not in user:
            self.logger.debug(
                f"[REPOSITORY] Assistant with ID: {assistant_id} is not in course with ID: {course_id}"
            )
            return False

        if user["assistant"].get(course_id) is None:
            self.logger.debug(
                f"[REPOSITORY] Assistant with ID: {assistant_id} is not in course with ID: {course_id}"
            )
            return False

        return True

    def add_assistant_to_course(self, course_id, assistant_id, perms_as_dict):
        """
        Add an assistant to a course.
        """
        # There are two scenarios here, the user may exists on the collectio and not have the array "assistant"
        # Or he alreaady have an assistant array and we need to add the course_id to it.

        self.logger.debug(
            f"[REPOSITORY] Adding assistant with ID: {assistant_id} to course with ID: {course_id}"
        )

        user_already_exists = self.collection.find_one({"student_id": assistant_id})

        if not user_already_exists:
            self.collection.insert_one(
                {"student_id": assistant_id, "assistant": {course_id: perms_as_dict}}
            )
        else:
            self.collection.update_one(
                {"student_id": assistant_id},
                {"$set": {f"assistant.{course_id}": perms_as_dict}},
            )

    def get_assistant_permissions_for_course(self, course_id, assistant_id):
        """
        Get the assistant permissions for a course.
        """
        self.logger.debug(
            f"[REPOSITORY] Getting assistant permissions for course with ID: {course_id} and assistant with ID: {assistant_id}"
        )

        user = self.collection.find_one({"student_id": assistant_id})

        if not user:
            self.logger.debug(
                f"[REPOSITORY] User with ID: {assistant_id} not found in the database"
            )
            return None

        if "assistant" not in user or course_id not in user["assistant"]:
            self.logger.debug(
                f"[REPOSITORY] Assistant with ID: {assistant_id} is not in course with ID: {course_id}"
            )
            return None

        return user["assistant"][course_id]

    def update_assistant_permissions(self, course_id, assistant_id, perms_as_dict):
        """
        Update the assistant permissions for a course.
        """
        self.logger.debug(
            f"[REPOSITORY] Updating assistant permissions for course with ID: {course_id} and assistant with ID: {assistant_id}"
        )

        user = self.collection.find_one({"student_id": assistant_id})

        if not user:
            self.logger.debug(
                f"[REPOSITORY] User with ID: {assistant_id} not found in the database"
            )
            return False

        if "assistant" not in user or course_id not in user["assistant"]:
            self.logger.debug(
                f"[REPOSITORY] Assistant with ID: {assistant_id} is not in course with ID: {course_id}"
            )
            return False

        update_result = self.collection.update_one(
            {"student_id": assistant_id},
            {"$set": {f"assistant.{course_id}": perms_as_dict}},
        )

        self.logger.debug(
            f"[REPOSITORY] Assistant permissions for course with ID: {course_id} and assistant with ID: {assistant_id} updated"
        )

        return update_result.modified_count > 0

    def remove_assistant_from_course_with_id(self, course_id, assistant_id):
        """
        Remove an assistant from a course.
        """
        self.logger.debug(
            f"[REPOSITORY] Removing assistant with ID: {assistant_id} from course with ID: {course_id}"
        )

        update_result = self.collection.update_one(
            {"student_id": assistant_id}, {"$unset": {f"assistant.{course_id}": ""}}
        )

        return update_result.modified_count > 0

    def check_assistants_permissions(self, course_id, assistant_id, permissions):
        """
        Check if the assistant has the required permissions.
        """
        self.logger.debug(
            f"[REPOSITORY] Checking if assistant with ID: {assistant_id} has permissions for course with ID: {course_id}"
        )

        user = self.collection.find_one({"student_id": assistant_id})

        if not user:
            self.logger.debug(
                f"[REPOSITORY] User with ID: {assistant_id} not found in the database"
            )
            return False

        if "assistant" not in user or course_id not in user["assistant"]:
            self.logger.debug(
                f"[REPOSITORY] Assistant with ID: {assistant_id} is not in course with ID: {course_id}"
            )
            return False

        assistant_permissions = user["assistant"][course_id].get(permissions, False)

        # Best case scenario, this returns true
        return assistant_permissions
