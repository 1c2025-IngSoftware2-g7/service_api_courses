from error.error import error_generator
from headers import (
    COURSE_IS_FULL,
    COURSE_NOT_FOUND,
    INTERNAL_SERVER_ERROR,
    UNAUTHORIZED,
    USER_ENROLLED,
)
from models.course import Course
from src.repository.courses_repository import CoursesRepository
from src.repository.users_data_repository import UsersDataRepository


class EnrollmentService:
    def __init__(
        self,
        course_repository: CoursesRepository,
        user_repository: UsersDataRepository,
        logger,
    ):
        self.course_repository = course_repository
        self.user_repository = user_repository
        self.logger = logger

    def enroll_student_in_course(self, course_id, student_id):
        try:
            # We check if the course inscription is still open
            inscription_available = (
                self.course_service.check_if_course_inscription_is_available(course_id)
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
            # We check if the user has the correlatives signatures approved
            courses_correlatives = self.course_repository.get_course_correlatives(
                course_id
            )
            student_approved_courses = (
                self.user_repository.get_student_approved_courses(student_id)
            )

            if not self.user_available_to_enroll(
                courses_correlatives, student_approved_courses
            ):
                self.logger.debug(
                    f"[SERVICE] Enroll: student with ID {student_id} does not have the correlatives signatures approved"
                )
                return error_generator(
                    UNAUTHORIZED,
                    f"Student with ID {student_id} does not have the correlatives signatures approved",
                    403,
                    "enroll_student",
                )

            enrolled = self.course_repository.enroll_student_in_course(
                course_id, student_id
            )
            if enrolled:
                self.logger.debug(
                    f"[DEBUG] Enroll: student with ID {student_id} enrolled in course with ID {course_id}"
                )
                return {
                    "response": {
                        "type": "about:blank",
                        "title": USER_ENROLLED,
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

                self.logger.debug(f"[DEBUG] courses searched: {courses}")
                return {"response": courses, "code_status": 200}
            else:
                return error_generator(
                    COURSE_NOT_FOUND,
                    f"No courses found for student with ID {student_id}",
                    404,
                    "get_enrolled_courses",
                )
        except Exception as e:
            return error_generator(
                INTERNAL_SERVER_ERROR,
                f"An error occurred while getting the enrolled courses: {str(e)}",
                500,
                "get_enrolled_courses",
            )

    def user_available_to_enroll(
        self, courses_correlatives: list[str], student_approved_courses: list[str]
    ) -> bool:
        """
        Check if the user has the correlatives signatures approved.
        """
        if not courses_correlatives:
            # If there are no correlatives, the user can enroll
            return True

        # for other scenarios, we check if the user has all the correlatives approved
        for course in courses_correlatives:
            if course not in student_approved_courses:
                return False

        return True
