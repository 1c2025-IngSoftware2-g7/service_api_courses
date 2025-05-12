from error.error import error_generator
from headers import (
    COURSE_ADDED_TO_FAVOURITES,
    COURSE_ALREADY_IN_FAVOURITES,
    COURSE_NOT_FOUND,
    COURSE_REMOVED_FROM_FAVOURITES,
    MISSING_FIELDS,
)
from src.models.course import Course
from src.repository.courses_repository import CoursesRepository
from src.repository.users_data_repository import UsersDataRepository


class UsersDataService:
    def __init__(self, repository_users: UsersDataRepository, service_courses: CoursesRepository, logger):
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

    def get_favourites_from_student_id(self, student_id, offset, max_per_page):
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

        # lets apply the pagionation
        start = offset * max_per_page
        end = start + max_per_page
        paginated_favourites = favourites[start:end]

        # Now i have the favourites as an list, now i should get the course data from the courses
        favourites_as_course_dict = []

        for course in paginated_favourites:
            course_data = self.service_courses.get_course_by_id(course)
            if course_data["code_status"] != 200:
                return error_generator(
                    COURSE_NOT_FOUND,
                    "Error converting a favourite course to a course, the data doesn't exists",
                    404,
                    "get_favourites_from_student_id",
                )
            favourites_as_course_dict.append(course_data["response"])

        return {"response": favourites_as_course_dict, "code_status": 200}

    def search_favourite_courses(self, student_id, query, offset, max_per_page):
        """
        Search for favourite courses.
        """
        self.logger.debug(
            f"[REPOSITORY] Searching favourite courses for student with ID: {student_id}"
        )

        # Check if the student has any favourites, we force 1 page (starts from zero) and 999 max per page
        favourites = self.get_favourites_from_student_id(student_id, 0, 1337)

        if not favourites:
            return error_generator(
                MISSING_FIELDS,
                "No favourites found",
                404,
                "search_favourite_courses",
            )

        # Filter the favourites list based on the query
        # To be helpful, lets convert it to a Instance of Courses then return as dict
        filtered_favourites = [
            Course.from_dict(course) for course in favourites["response"]
        ]
        self.logger.debug(f"[REPOSITORY] Favourites list: {filtered_favourites}")
        filtered_favourites = [
            course.to_dict()
            for course in filtered_favourites
            if query.lower() in course.name.lower()
            or query.lower() in course.description.lower()
            or query.lower() in course.creator_name.lower()
        ]
        """filtered_favourites = [
            course
            for course in favourites
            if query.lower() in course[4].lower() or
            query.lower() in course[5].lower() or
            query.lower() in course[9].lower()
        ]"""

        # lets apply the pagionation
        start = offset * max_per_page
        end = start + max_per_page
        paginated_favourites = filtered_favourites[start:end]

        return {"response": paginated_favourites, "code_status": 200}

    def approve_student_in_courses(self, student_id):
        try:
            # Check if the student is already enrolled in the course
            student_enrolled = self.repository.check_student_enrollment(
                student_id
            )

            if not student_enrolled:
                return error_generator(
                    MISSING_FIELDS,
                    "Student not enrolled in any course",
                    400,
                    "approve_student_in_courses",
                )

            # Approve the student in the course
            self.repository.approve_student(student_id)

            return {
                "response": {
                    "type": "about:blank",
                    "title": "Student Approved",
                    "status": 200,
                    "detail": f"Student with ID {student_id} has been approved in all courses",
                    "instance": f"/courses/approve/{student_id}",
                },
                "code_status": 200,
            }
        except Exception as e:
            self.logger.error(
                f"[REPOSITORY] Error approving student in courses: {e}"
            )
            return error_generator(
                MISSING_FIELDS,
                "Error approving student in courses",
                500,
                "approve_student_in_courses",
            )