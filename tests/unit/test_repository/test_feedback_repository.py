import pytest
from unittest.mock import MagicMock
from src.repository.feedback_repository import FeedBackRepository
from src.models.feedback import FeedbackCourse, FeedbackStudent

@pytest.fixture
def mock_courses_feedback_collection():
    return MagicMock()

@pytest.fixture
def mock_students_feedback_collection():
    return MagicMock()

@pytest.fixture
def mock_logger():
    return MagicMock()

@pytest.fixture
def repo(mock_courses_feedback_collection, mock_students_feedback_collection, mock_logger):
    return FeedBackRepository(
        mock_courses_feedback_collection,
        mock_students_feedback_collection,
        mock_logger,
    )

def test_insert_course_feedback(repo, mock_courses_feedback_collection, mock_logger):
    feedback = MagicMock(spec=FeedbackCourse)
    feedback.course_id = "course123"
    feedback.to_dict.return_value = {"course_id": "course123", "rating": 5}

    mock_courses_feedback_collection.insert_one.return_value.inserted_id = "feedback_id"

    repo.insert_course_feedback(feedback)

    mock_courses_feedback_collection.insert_one.assert_called_once_with(feedback.to_dict())
    mock_logger.debug.assert_any_call(f"feedback_obj: {feedback.to_dict()}")
    mock_logger.debug.assert_any_call("[REPOSITORY] Inserted feedback with ID: feedback_id")
    mock_logger.debug.assert_any_call("[REPOSITORY] Inserted feedback for course with ID: course123")

def test_get_course_feedback(repo, mock_courses_feedback_collection, mock_logger):
    feedbacks = [{"course_id": "course123", "comment": "Great!"}]
    mock_courses_feedback_collection.find.return_value = feedbacks

    result = repo.get_course_feedback("course123")

    mock_courses_feedback_collection.find.assert_called_once_with({"course_id": "course123"})
    mock_logger.debug.assert_any_call("[REPOSITORY] Retrieved feedback for course with ID: course123")
    mock_logger.debug.assert_any_call(f"[REPOSITORY] Feedback result: {feedbacks}")
    assert result == feedbacks

def test_insert_student_feedback(repo, mock_students_feedback_collection, mock_logger):
    feedback = MagicMock(spec=FeedbackStudent)
    feedback.student_id = "student123"
    feedback.to_dict.return_value = {"student_id": "student123", "rating": 4}

    repo.insert_student_feedback(feedback)

    mock_students_feedback_collection.insert_one.assert_called_once_with(feedback.to_dict())
    mock_logger.debug.assert_called_with("[REPOSITORY] Inserted feedback for student with ID: student123")

def test_get_student_feedback(repo, mock_students_feedback_collection):
    feedbacks = [{"student_id": "student123", "course_id": "course123", "comment": "Good job"}]
    mock_students_feedback_collection.find.return_value = feedbacks

    result = repo.get_student_feedback("student123", "course123")

    mock_students_feedback_collection.find.assert_called_once_with(
        {"student_id": "student123", "course_id": "course123"}
    )
    assert result == feedbacks
