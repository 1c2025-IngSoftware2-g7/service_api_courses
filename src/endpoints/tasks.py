# src/endpoints/.py
from flask import Blueprint, request
from src.error.error import error_generator
from src.headers import MISSING_FIELDS
from services import service_tasks, logger

tasks_bp = Blueprint("tasks", __name__, url_prefix="/courses/tasks")


@tasks_bp.post("/")
def create_task():
    """
    Create a new task/exam
    """
    data = request.json

    if not data:
        error = error_generator(
            MISSING_FIELDS, "Request body is required", 400, "create_task"
        )
        return error["response"], error["code_status"]

    logger.debug(f"Creating task with data: {data}")
    result = service_tasks.create_task(data)

    return result["response"], result["code_status"]


@tasks_bp.put("/<string:task_id>")
def update_task(task_id=None):
    """
    Update an existing task/exam
    """
    if not task_id:
        error = error_generator(
            MISSING_FIELDS, "Task ID is required", 400, "update_task"
        )
        return error["response"], error["code_status"]

    data = request.json
    if not data:
        error = error_generator(
            MISSING_FIELDS, "Request body is required", 400, "update_task"
        )
        return error["response"], error["code_status"]

    logger.debug(f"Updating task {task_id} with data: {data}")
    result = service_tasks.update_task(task_id, data)

    return result["response"], result["code_status"]


@tasks_bp.delete("/<string:task_id>")
def delete_task(task_id=None):
    """
    Delete a task/exam
    """
    if not task_id:
        error = error_generator(
            MISSING_FIELDS, "Task ID is required", 400, "delete_task"
        )
        return error["response"], error["code_status"]

    logger.debug(f"Deleting task {task_id}")
    result = service_tasks.delete_task(task_id)

    return result["response"], result["code_status"]


@tasks_bp.get("/course/<string:course_id>")
def get_tasks_by_course(course_id=None):
    """
    Get all tasks for a specific course
    Optional: Filter by status (passed as query parameter)
    """
    if not course_id:
        error = error_generator(
            MISSING_FIELDS, "Course ID is required", 400, "get_tasks_by_course"
        )
        return error["response"], error["code_status"]

    status = request.args.get("status", None)
    logger.debug(
        f"Getting tasks for course {course_id} with status filter: {status}")

    result = service_tasks.get_tasks_by_course(course_id, status)
    return result["response"], result["code_status"]


@tasks_bp.get("/<string:task_id>")
def get_task_by_id(task_id=None):
    """
    Get a specific task by ID
    """
    if not task_id:
        error = error_generator(
            MISSING_FIELDS, "Task ID is required", 400, "get_task_by_id"
        )
        return error["response"], error["code_status"]

    logger.debug(f"Getting task with ID: {task_id}")
    result = service_tasks.get_task_by_id(task_id)
    return result["response"], result["code_status"]
