from error.error import error_generator
from headers import (
    COURSE_ADDED_TO_FAVOURITES,
    COURSE_ALREADY_IN_FAVOURITES,
    COURSE_NOT_FOUND,
    COURSE_REMOVED_FROM_FAVOURITES,
    MISSING_FIELDS,
)


class UsersDataService:
    def __init__(self, repository_users, service_courses, logger):
        self.repository = repository_users
        self.service_courses = service_courses
        self.logger = logger

    def set_favourite_course_for_student(self, course_id, student_id):
        """
        Set a course as favourite for a student.
        """
        self.logger.debug(
            f"[REPOSITORY] Setting course with ID: {course_id} as favourite for student with ID: {student_id}"
        )

        # Check if the course exists
        course_exists = self.service_courses.get_course(course_id)

        if course_exists["code_status"] != 200:
            return error_generator(
                COURSE_NOT_FOUND, "Course ID not found", 404, "set_favourite_course"
            )

        course_already_fav = self.repository.course_already_favourite(
            course_id, student_id
        )

        if course_already_fav:
            return error_generator(
                COURSE_ALREADY_IN_FAVOURITES,
                "Course already in favourites",
                400,
                "set_favourite_course",
            )

        self.repository.set_favourite_course(course_id, student_id)

        self.logger.debug(
            f"[REPOSITORY] Course with ID: {course_id} set as favourite for student with ID: {student_id}"
        )

        return {
            "response": {
                "type": "about:blank",
                "title": COURSE_ADDED_TO_FAVOURITES,
                "status": 200,
                "detail": f"Student with ID {student_id} now has as favourite the course {course_id}",
                "instance": f"/courses/enroll/{course_id}",
            },
            "code_status": 200,
        }

    def remove_course_from_favourites(self, course_id, student_id):
        """
        Remove a course from the favourites list.
        """
        self.logger.debug(
            f"[REPOSITORY] Removing course with ID: {course_id} from favourites for student with ID: {student_id}"
        )

        # Check if the course exists
        course_exists = self.service_courses.get_course(course_id)

        if course_exists["code_status"] != 200:
            return error_generator(
                COURSE_NOT_FOUND,
                "Course ID not found",
                404,
                "remove_course_from_favourites",
            )

        # Check if the course is already in the favourites list
        course_already_fav = self.repository.course_already_favourite(
            course_id, student_id
        )

        if not course_already_fav:
            return error_generator(
                COURSE_ALREADY_IN_FAVOURITES,
                "Course not in favourites",
                400,
                "remove_course_from_favourites",
            )

        self.repository.remove_course_from_favourites(course_id, student_id)

        self.logger.debug(
            f"[REPOSITORY] Course with ID: {course_id} removed from favourites for student with ID: {student_id}"
        )

        return {
            "response": {
                "type": "about:blank",
                "title": COURSE_REMOVED_FROM_FAVOURITES,
                "status": 200,
                "detail": f"Student with ID {student_id} has removed the course id: {course_id} as favourites",
                "instance": f"/courses/enroll/{course_id}",
            },
            "code_status": 200,
        }

    def get_favourites_from_student_id(self, student_id):
        """
        Get the favourites list for a student.
        """
        self.logger.debug(
            f"[REPOSITORY] Getting favourites for student with ID: {student_id}"
        )

        # Get the favourites list
        favourites = self.repository.get_favourites_from_student_id(student_id)

        if not favourites:
            return error_generator(
                MISSING_FIELDS,
                "No favourites found",
                404,
                "get_favourites_from_student_id",
            )

        return {"response": favourites, "code_status": 200}
