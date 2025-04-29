'''import pytest
from unittest.mock import MagicMock


from services.course_service import CourseService


@pytest.fixture
def course_service():
    mock_repository = MagicMock()
    mock_logger = MagicMock()
    service = CourseService(mock_repository, mock_logger)

    return service


def test_get_all_courses(course_service):
    # Arrange
    mock_courses = [
        {"name": "Course 1", "description": "Description 1"},
        {"name": "Course 2", "description": "Description 2"},
        {"name": "Course 3", "description": "Description 3"},
        {"name": "Course 4", "description": "Description 4"},
        {"name": "Course 5", "description": "Description 5"},
    ]
    course_service.course_repository.get_all_courses.return_value = mock_courses

    # Act
    result = course_service.get_all_courses()

    # Assert
    # lets assert that the result is as expected
    for i in range(len(result)):
        assert result["response"][i]["name"] == mock_courses[i]["name"]
        assert result["response"][i]["description"] == mock_courses[i]["description"]

    course_service.course_repository.get_all_courses.assert_called_once()


def test_get_course_owner(course_service):
    # Arrange
    mock_course_id = 55
    course_service.course_repository.get_course_owner.return_value = mock_course_id

    # Act
    result = course_service.course_repository.get_course_owner(mock_course_id)

    # Assert
    assert result == mock_course_id

    course_service.course_repository.get_course_owner.assert_called_once_with(
        mock_course_id
    )


def test_update_course(course_service):
    # Arrange
    mock_course_id = 55
    mock_course_data = {"name": "Updated Course", "description": "Updated Description"}
    mock_owner_id = 123
    course_service.course_repository.update_course.return_value = True

    # Act
    result = course_service.course_repository.update_course(
        mock_course_id, mock_course_data, mock_owner_id
    )

    # Assert
    assert result == True

    course_service.course_repository.update_course.assert_called_once_with(
        mock_course_id, mock_course_data, mock_owner_id
    )


def test_delete_course(course_service):
    # Arrange
    mock_course_id = 55
    course_service.course_repository.delete_course.return_value = True

    # Act
    result = course_service.course_repository.delete_course(mock_course_id)

    # Assert
    assert result == True

    course_service.course_repository.delete_course.assert_called_once_with(
        mock_course_id
    )


def test_search_course_by_query(course_service):
    # Arrange
    mock_query = "masterclass"
    mock_courses = [
        {"name": "Taller 1", "description": "jejo"},
        {"name": "Analisis 2", "description": "masterclass"},
    ]

    expected_course = {"name": "Analisis 2", "description": "masterclass"}
    course_service.course_repository.search_course_by_partial_information.return_value = (
        expected_course
    )

    # Act
    result = course_service.course_repository.search_course_by_partial_information(
        mock_query
    )

    # Assert
    assert result == expected_course

    course_service.course_repository.search_course_by_partial_information.assert_called_once_with(
        mock_query
    )
'''