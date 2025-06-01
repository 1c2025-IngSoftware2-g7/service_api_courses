from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest
from flasgger import swag_from

from error.error import error_generator
from headers import MISSING_FIELDS
from services import service_tasks, logger
from utils import parse_date_to_timestamp_ms

tasks_bp = Blueprint("tasks", __name__, url_prefix="/courses/tasks")


@tasks_bp.post("/")
@swag_from({
    'tags': ['Tasks'],
    'summary': 'Create a new task or exam',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'title': {'type': 'string'},
                    'description': {'type': 'string'},
                    'instructions': {'type': 'string'},
                    'due_date': {'type': 'integer'},
                    'course_id': {'type': 'string'},
                    'module_id': {'type': 'string'},
                    'status': {'type': 'string', 'enum': ['inactive', 'open', 'closed']},
                    'task_type': {'type': 'string', 'enum': ['task', 'exam']},
                    'file_url': {'type': 'string'}
                },
                'required': ['title', 'course_id', 'due_date']
            }
        }
    ],
    'responses': {
        201: {'description': 'Task created successfully'},
        400: {'description': 'Missing required fields or malformed request'},
        500: {'description': 'Internal server error'}
    }
})
def create_task():
    """
    Create a new task/exam
    """
    data = request.json

    if not data:
        error = error_generator(
            f"[TASKS][CONTROLLER] {MISSING_FIELDS}", "Request body is required", 400, ""
        )
        return error["response"], error["code_status"]

    logger.debug(f"[TASKS][CONTROLLER] Creating task with data: {data}")
    result = service_tasks.create_task(data)

    return result["response"], result["code_status"]


@tasks_bp.put("/<string:task_id>")
@swag_from({
    'tags': ['Tasks'],
    'summary': 'Update a task or exam',
    'parameters': [
        {
            'name': 'task_id',
            'in': 'path',
            'type': 'string',
            'required': True
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'title': {'type': 'string'},
                    'description': {'type': 'string'},
                    'instructions': {'type': 'string'},
                    'due_date': {'type': 'integer'},
                    'status': {'type': 'string'},
                    'task_type': {'type': 'string'},
                    'file_url': {'type': 'string'}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Task updated successfully'},
        400: {'description': 'Missing or invalid fields'},
        404: {'description': 'Task not found'},
        500: {'description': 'Internal server error'}
    }
})
def update_task(task_id=None):
    """
    Update an existing task/exam
    """
    if not task_id:
        error = error_generator(
            f"[TASKS][CONTROLLER] {MISSING_FIELDS}", "Task ID is required", 400, "update_task"
        )
        return error["response"], error["code_status"]

    data = request.json
    if not data:
        error = error_generator(
            f"[TASKS][CONTROLLER] {MISSING_FIELDS}", "Request body is required", 400, "update_task"
        )
        return error["response"], error["code_status"]

    logger.debug(f"[TASKS][CONTROLLER] Updating task {task_id} with data: {data}")
    result = service_tasks.update_task(task_id, data)

    return result["response"], result["code_status"]


@tasks_bp.delete("/<string:task_id>")
@swag_from({
    'tags': ['Tasks'],
    'summary': 'Delete a task or exam',
    'parameters': [
        {
            'name': 'task_id',
            'in': 'path',
            'type': 'string',
            'required': True
        }
    ],
    'responses': {
        200: {'description': 'Task deleted successfully'},
        400: {'description': 'Task ID required'},
        404: {'description': 'Task not found'},
        500: {'description': 'Internal server error'}
    }
})
def delete_task(task_id=None):
    """
    Delete a task/exam
    """
    if not task_id:
        error = error_generator(
            f"[TASKS][CONTROLLER] {MISSING_FIELDS}", "Task ID is required", 400, "delete_task"
        )
        return error["response"], error["code_status"]

    logger.debug(f"[TASKS][CONTROLLER] Deleting task {task_id}")
    result = service_tasks.delete_task(task_id)

    return result["response"], result["code_status"]


@tasks_bp.get("/course/<string:course_id>")
@swag_from({
    'tags': ['Tasks'],
    'summary': 'Get tasks for a course',
    'parameters': [
        {
            'name': 'course_id',
            'in': 'path',
            'type': 'string',
            'required': True
        },
        {
            'name': 'status',
            'in': 'query',
            'type': 'string',
            'required': False
        },
        {
            'name': 'module_id',
            'in': 'query',
            'type': 'string',
            'required': False
        }
    ],
    'responses': {
        200: {'description': 'Tasks retrieved successfully'},
        400: {'description': 'Missing course ID'},
        404: {'description': 'Course not found'},
        500: {'description': 'Internal server error'}
    }
})
def get_tasks_by_course(course_id=None):
    """
    Get all tasks for a specific course
    Optional: Filter by status (passed as query parameter)
    """
    if not course_id:
        error = error_generator(
            f"[TASKS][CONTROLLER] {MISSING_FIELDS}", "Course ID is required", 400, "get_tasks_by_course"
        )
        return error["response"], error["code_status"]

    status = request.args.get("status", None)
    module_id = request.args.get("module_id", None)
    logger.debug(
        f"[TASKS][CONTROLLER] Getting tasks for course {course_id} with status filter: {status}. And module_id filter: {module_id}")

    result = service_tasks.get_tasks_by_course(course_id, status, module_id)
    return result["response"], result["code_status"]


@tasks_bp.get("/<string:task_id>")
@swag_from({
    'tags': ['Tasks'],
    'summary': 'Get task by ID',
    'parameters': [
        {
            'name': 'task_id',
            'in': 'path',
            'type': 'string',
            'required': True
        }
    ],
    'responses': {
        200: {'description': 'Task retrieved successfully'},
        400: {'description': 'Missing task ID'},
        404: {'description': 'Task not found'},
        500: {'description': 'Internal server error'}
    }
})
def get_task_by_id(task_id=None):
    """
    Get a specific task by ID
    """
    if not task_id:
        error = error_generator(
            f"[TASKS][CONTROLLER] {MISSING_FIELDS}", "Task ID is required", 400, "get_task_by_id"
        )
        return error["response"], error["code_status"]

    logger.debug(f"[TASKS][CONTROLLER] Getting task with ID: {task_id}")
    result = service_tasks.get_task_by_id(task_id)
    return result["response"], result["code_status"]


@tasks_bp.post('/submission/<uuid_task>')
@swag_from({
    'tags': ['Tasks'],
    'summary': 'Submit a task or exam',
    'parameters': [
        {'name': 'uuid_task', 'in': 'path', 'type': 'string', 'required': True},
        {'name': 'body', 'in': 'body', 'required': True,
         'schema': {
             'type': 'object',
             'properties': {
                 'uuid_student': {'type': 'string'},
                 'attachment_links': {'type': 'array', 'items': {'type': 'string'}}
             },
             'required': ['uuid_student', 'attachment_links']
         }}
    ],
    'responses': {
        200: {'description': 'Task submitted successfully'},
        400: {'description': 'Missing required fields'},
        500: {'description': 'Internal server error'}
    }
})
def submit_task(uuid_task):
    """
    Student: Submit a task/exam response
    """
    try:
        data = request.json
        if 'uuid_student' not in data:
            raise BadRequest("The uuid_student field is missing from the request.")
        if 'attachment_links' not in data:
            raise BadRequest("The attachment_links is missing from the request.")

        uuid_student = data.get('uuid_student')
        attachment_links = data.get('attachment_links')

        task = service_tasks.submit_task(uuid_task, uuid_student, attachment_links)
        return jsonify(task.to_dict()), 200

    except BadRequest as e:
        # Captures malformed request errors
        error = error_generator("[TASKS][CONTROLLER] Bad Request", str(e), 400, f"tasks/submission/{uuid_task}")
        return error["response"], error["code_status"]

    except Exception as e:
        # Catch-all for unexpected errors
        error = error_generator("[TASKS][CONTROLLER] Internal Server Error", str(e), 500, f"tasks/submission/{uuid_task}")
        return error["response"], error["code_status"]

@tasks_bp.post('/upload')
@swag_from({
    'tags': ['Tasks'],
    'summary': 'Upload a task file',
    'parameters': [
        {'name': 'uuid', 'in': 'formData', 'type': 'string', 'required': True},
        {'name': 'task_number', 'in': 'formData', 'type': 'string', 'required': True},
        {'name': 'attachment', 'in': 'formData', 'type': 'file', 'required': True}
    ],
    'consumes': ['multipart/form-data'],
    'responses': {
        200: {'description': 'File uploaded successfully'},
        400: {'description': 'Missing fields in form data'},
        422: {'description': 'Invalid or empty file'},
        500: {'description': 'Internal server error'}
    }
})
def upload_task():
    """
    Student or teacher upload task or exman
    Body is form-data with uuid, attachment and task_number
    """
    try:
        if 'uuid' not in request.form and 'task_number' not in request.form:
            raise BadRequest("The uuid field is missing from the form.")
        if 'attachment' not in request.files:
            raise BadRequest("The attachment is missing from the request.")

        uuid = request.form.get('uuid')
        task_number = request.form.get('task_number')
        attachment = request.files.get('attachment')

        if not attachment or attachment.filename == '':
            raise FileNotFoundError("The attachment is empty or has no name.")

        task_link = service_tasks.upload_task(uuid, task_number, attachment)
        return jsonify({"url": task_link}), 200

    except BadRequest as e:
        # Captures malformed request errors
        error = error_generator("Bad Request", str(e), 400, f"tasks/upload")
        return error["response"], error["code_status"]

    except FileNotFoundError as e:
        # Logical validation of empty or invalid values
        error = error_generator("[TASKS][CONTROLLER] Validation Error", str(e), 422, f"tasks/upload")
        return error["response"], error["code_status"]

    except Exception as e:
        # Catch-all for unexpected errors
        error = error_generator("[TASKS][CONTROLLER] Internal Server Error", str(e), 500, f"tasks/upload")
        return error["response"], error["code_status"]

@tasks_bp.get("/teachers/<string:teacher_id>")
@swag_from({
    'tags': ['Tasks'],
    'summary': 'Get tasks by teacher',
    'parameters': [
        {'name': 'teacher_id', 'in': 'path', 'type': 'string', 'required': True},
        {'name': 'status', 'in': 'query', 'type': 'string'},
        {'name': 'date', 'in': 'query', 'type': 'string'},
        {'name': 'page', 'in': 'query', 'type': 'integer'},
        {'name': 'limit', 'in': 'query', 'type': 'integer'}
    ],
    'responses': {
        200: {'description': 'Tasks retrieved successfully'},
        400: {'description': 'Invalid parameters'},
        500: {'description': 'Internal server error'}
    }
})
def get_tasks_by_teacher(teacher_id):
    try:
        status = request.args.get("status")
        due_date = request.args.get("date")
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 1000))

        date_range = None
        if due_date:
            try:
                date = datetime.strptime(due_date, "%Y-%m-%d").date()
                start_dt = datetime.combine(date, datetime.min.time(), tzinfo=timezone.utc)
                end_dt = datetime.combine(date, datetime.max.time(), tzinfo=timezone.utc)

                start_ts = parse_date_to_timestamp_ms(start_dt)
                end_ts = parse_date_to_timestamp_ms(end_dt)

                date_range = {"$gte": start_ts, "$lte": end_ts}
            except ValueError:
                error = error_generator(
                    "[TASKS][CONTROLLER] Invalid date format.",
                    "Use YYYY-MM-DD",
                    400,
                    "teachers/<string:teacher_id>"
                )
                return error["response"], error["code_status"]

        tasks = service_tasks.get_tasks_by_teacher(
            teacher_id=teacher_id,
            status=status,
            due_date=date_range,
            page=page,
            limit=limit
        )

        return jsonify([t.to_dict() for t in tasks]), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@tasks_bp.get("/students/<string:student_id>")
@swag_from({
    'tags': ['Tasks'],
    'summary': 'Get tasks for a student',
    'parameters': [
        {'name': 'student_id', 'in': 'path', 'type': 'string', 'required': True},
        {'name': 'status', 'in': 'query', 'type': 'string'},
        {'name': 'course_id', 'in': 'query', 'type': 'string'},
        {'name': 'date', 'in': 'query', 'type': 'string'},
        {'name': 'page', 'in': 'query', 'type': 'integer'},
        {'name': 'limit', 'in': 'query', 'type': 'integer'}
    ],
    'responses': {
        200: {'description': 'Tasks retrieved successfully'},
        400: {'description': 'Invalid parameters'},
        500: {'description': 'Internal server error'}
    }
})
def get_tasks_for_student(student_id):
    try:
        status = request.args.get("status")
        course_id = request.args.get("course_id")
        due_date = request.args.get("date")
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 1000))

        due_date_ts = None
        if due_date:
            try:
                dt = datetime.fromisoformat(due_date)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                due_date_ts = parse_date_to_timestamp_ms(dt)
            except Exception:
                error = error_generator(
                    "[TASKS][CONTROLLER] Invalid date format.",
                    "Use ISO 8601 format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS",
                    400,
                    "students/<string:student_id>"
                )
                return error["response"], error["code_status"]

        tasks = service_tasks.get_tasks_by_student(
            student_id=student_id,
            status=status,
            course_id=course_id,
            due_date=due_date_ts,
            page=page,
            limit=limit
        )

        return jsonify([t.to_dict() for t in tasks]), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
