from bson import ObjectId
from headers import MISSING_FIELDS


class UsersDataRepository:
    def __init__(self, collection_users, logger):
        self.collection = collection_users
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
