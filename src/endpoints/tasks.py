from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest

from error.error import error_generator
from headers import MISSING_FIELDS
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
            MISSING_FIELDS, "Request body is required", 400, ""
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


@tasks_bp.post('/submission/<uuid_task>')
def submit_task(uuid_task):
    """
    Student: Submit a task/exam response
    """
    try:
        data = request.json
        if 'uuid_student' not in data:
            raise BadRequest("The uuid_student field is missing from the form.")
        if 'attachment_links' not in data:
            raise BadRequest("The attachment_links is missing from the request.")

        uuid_student = data.get('uuid_student')
        attachment_links = data.get('attachment_links')

        task = service_tasks.submit_task(uuid_task, uuid_student, attachment_links)
        return jsonify(task.to_dict()), 200

    except BadRequest as e:
        # Captures malformed request errors
        error = error_generator("Bad Request", str(e), 400, f"tasks/submission/{uuid_task}")
        return error["response"], error["code_status"]

    except Exception as e:
        # Catch-all for unexpected errors
        error = error_generator("Internal Server Error", str(e), 500, f"tasks/submission/{uuid_task}")
        return error["response"], error["code_status"]

@tasks_bp.post('/upload')
def upload_task():
    """
    Student or teacher upload task or exman
    Body is form-data with uuid, attachment and task_number
    """
    try:
        if 'uuid' not in request.form and 'task_number' not in request.form:
            raise BadRequest("The uuid field is missing from the form.")
        if 'file' not in request.files:
            raise BadRequest("The file is missing from the request.")

        uuid = request.form.get('uuid')
        task_number = request.form.get('task_number')
        file = request.files.get('file')

        if not file or file.filename == '':
            raise FileNotFoundError("The file is empty or has no name.")

        task_link = service_tasks.upload_task(uuid, task_number, file)
        return jsonify({"url": task_link}), 200

    except BadRequest as e:
        # Captures malformed request errors
        error = error_generator("Bad Request", str(e), 400, f"tasks/upload")
        return error["response"], error["code_status"]

    except FileNotFoundError as e:
        # Logical validation of empty or invalid values
        error = error_generator("Validation Error", str(e), 422, f"tasks/upload")
        return error["response"], error["code_status"]

    except Exception as e:
        # Catch-all for unexpected errors
        error = error_generator("Internal Server Error", str(e), 500, f"tasks/upload")
        return error["response"], error["code_status"]
