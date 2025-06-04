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
@swag_from(
    {
        "tags": ["Tasks"],
        "summary": "Create a new task or exam",
        "parameters": [
            {
                "name": "body",
                "in": "body",
                "required": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "instructions": {"type": "string"},
                        "due_date": {"type": "integer"},
                        "course_id": {"type": "string"},
                        "module_id": {"type": "string"},
                        "status": {
                            "type": "string",
                            "enum": ["inactive", "open", "closed"],
                        },
                        "task_type": {"type": "string", "enum": ["task", "exam"]},
                        "attachments": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "url": {"type": "string"},
                                    "mimetype": {"type": "string"},
                                },
                            },
                        },
                    },
                    "required": ["title", "course_id", "due_date"],
                },
            }
        ],
        "responses": {
            201: {"description": "Task created successfully"},
            400: {"description": "Missing required fields or malformed request"},
            500: {"description": "Internal server error"},
        },
    }
)
def create_task():
    """
    Create a new task/exam
    """
    data = request.json

    headers = request.headers
    creator_user_uuid = get_header_value_for_key(headers, "X-User-UUID")

    if not creator_user_uuid:
        error = error_generator(
            MISSING_FIELDS, "User UUID is required", 400, "get_modules_from_course"
        )
        return error["response"], error["code_status"]

    if not data:
        error = error_generator(
            f"[TASKS][CONTROLLER] {MISSING_FIELDS}",
            "User UUID is required",
            400,
            "get_modules_from_course",
        )
        return error["response"], error["code_status"]

    logger.debug(f"[TASKS][CONTROLLER] Creating task with data: {data}")
    result = service_tasks.create_task(data, creator_user_uuid)

    return result["response"], result["code_status"]


@tasks_bp.put("/<string:task_id>")
@swag_from(
    {
        "tags": ["Tasks"],
        "summary": "Update a task or exam",
        "parameters": [
            {"name": "task_id", "in": "path", "type": "string", "required": True},
            {
                "name": "body",
                "in": "body",
                "required": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "instructions": {"type": "string"},
                        "due_date": {"type": "integer"},
                        "status": {"type": "string"},
                        "task_type": {"type": "string"},
                        "attachments": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "url": {"type": "string"},
                                    "mimetype": {"type": "string"},
                                },
                            },
                        },
                    },
                },
            },
        ],
        "responses": {
            200: {"description": "Task updated successfully"},
            400: {"description": "Missing or invalid fields"},
            404: {"description": "Task not found"},
            500: {"description": "Internal server error"},
        },
    }
)
def update_task(task_id=None):
    """
    Update an existing task/exam
    """
    if not task_id:
        error = error_generator(
            f"[TASKS][CONTROLLER] {MISSING_FIELDS}",
            "Task ID is required",
            400,
            "update_task",
        )
        return error["response"], error["code_status"]

    data = request.json
    if not data:
        error = error_generator(
            f"[TASKS][CONTROLLER] {MISSING_FIELDS}",
            "Request body is required",
            400,
            "update_task",
        )
        return error["response"], error["code_status"]

    headers = request.headers
    creator_user_uuid = get_header_value_for_key(headers, "X-User-UUID")

    if not creator_user_uuid:
        error = error_generator(
            MISSING_FIELDS, "User UUID is required", 400, "get_modules_from_course"
        )
        return error["response"], error["code_status"]

    logger.debug(f"[TASKS][CONTROLLER] Updating task {task_id} with data: {data}")
    result = service_tasks.update_task(task_id, data, creator_user_uuid)

    return result["response"], result["code_status"]


@tasks_bp.delete("/<string:task_id>")
@swag_from(
    {
        "tags": ["Tasks"],
        "summary": "Delete a task or exam",
        "parameters": [
            {"name": "task_id", "in": "path", "type": "string", "required": True}
        ],
        "responses": {
            200: {"description": "Task deleted successfully"},
            400: {"description": "Task ID required"},
            404: {"description": "Task not found"},
            500: {"description": "Internal server error"},
        },
    }
)
def delete_task(task_id=None):
    """
    Delete a task/exam
    """
    if not task_id:
        error = error_generator(
            f"[TASKS][CONTROLLER] {MISSING_FIELDS}",
            "Task ID is required",
            400,
            "delete_task",
        )
        return error["response"], error["code_status"]

    headers = request.headers
    creator_user_uuid = get_header_value_for_key(headers, "X-User-UUID")

    if not creator_user_uuid:
        error = error_generator(
            MISSING_FIELDS, "User UUID is required", 400, "get_modules_from_course"
        )
        return error["response"], error["code_status"]

    logger.debug(f"[TASKS][CONTROLLER] Deleting task {task_id}")
    result = service_tasks.delete_task(task_id, creator_user_uuid)

    return result["response"], result["code_status"]


@tasks_bp.get("/course/<string:course_id>")
@swag_from(
    {
        "tags": ["Tasks"],
        "summary": "Get tasks for a course",
        "parameters": [
            {"name": "course_id", "in": "path", "type": "string", "required": True},
            {"name": "status", "in": "query", "type": "string", "required": False},
            {"name": "module_id", "in": "query", "type": "string", "required": False},
        ],
        "responses": {
            200: {"description": "Tasks retrieved successfully"},
            400: {"description": "Missing course ID"},
            404: {"description": "Course not found"},
            500: {"description": "Internal server error"},
        },
    }
)
def get_tasks_by_course(course_id=None):
    """
    Get all tasks for a specific course
    Optional: Filter by status (passed as query parameter)
    """
    if not course_id:
        error = error_generator(
            f"[TASKS][CONTROLLER] {MISSING_FIELDS}",
            "Course ID is required",
            400,
            "get_tasks_by_course",
        )
        return error["response"], error["code_status"]

    status = request.args.get("status", None)
    module_id = request.args.get("module_id", None)
    logger.debug(
        f"[TASKS][CONTROLLER] Getting tasks for course {course_id} with status filter: {status}. And module_id filter: {module_id}"
    )

    result = service_tasks.get_tasks_by_course(course_id, status, module_id)
    return result["response"], result["code_status"]


@tasks_bp.get("/<string:task_id>")
@swag_from(
    {
        "tags": ["Tasks"],
        "summary": "Get task by ID",
        "parameters": [
            {"name": "task_id", "in": "path", "type": "string", "required": True}
        ],
        "responses": {
            200: {"description": "Task retrieved successfully"},
            400: {"description": "Missing task ID"},
            404: {"description": "Task not found"},
            500: {"description": "Internal server error"},
        },
    }
)
def get_task_by_id(task_id=None):
    """
    Get a specific task by ID
    """
    if not task_id:
        error = error_generator(
            f"[TASKS][CONTROLLER] {MISSING_FIELDS}",
            "Task ID is required",
            400,
            "get_task_by_id",
        )
        return error["response"], error["code_status"]

    logger.debug(f"[TASKS][CONTROLLER] Getting task with ID: {task_id}")
    result = service_tasks.get_task_by_id(task_id)
    return result["response"], result["code_status"]


@tasks_bp.post("/submission/<uuid_task>")
@swag_from(
    {
        "tags": ["Tasks"],
        "summary": "Submit a task or exam",
        "parameters": [
            {"name": "uuid_task", "in": "path", "type": "string", "required": True},
            {
                "name": "body",
                "in": "body",
                "required": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "uuid_student": {"type": "string"},
                        "attachments": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "url": {"type": "string"},
                                    "mimetype": {"type": "string"},
                                },
                            },
                        },
                    },
                    "required": ["uuid_student", "attachments"],
                },
            },
        ],
        "responses": {
            200: {"description": "Task submitted successfully"},
            400: {"description": "Missing required fields"},
            500: {"description": "Internal server error"},
        },
    }
)
def submit_task(uuid_task):
    """
    Student: Submit a task/exam response
    """
    try:
        data = request.json
        if "uuid_student" not in data:
            raise BadRequest("The uuid_student field is missing from the request.")
        if "attachments" not in data:
            raise BadRequest("The attachments is missing from the request.")

        uuid_student = data.get("uuid_student")
        attachments = data.get("attachments")

        task = service_tasks.submit_task(uuid_task, uuid_student, attachments)
        return jsonify(task.to_dict()), 200

    except BadRequest as e:
        # Captures malformed request errors
        error = error_generator(
            "[TASKS][CONTROLLER] Bad Request",
            str(e),
            400,
            f"tasks/submission/{uuid_task}",
        )
        return error["response"], error["code_status"]

    except Exception as e:
        # Catch-all for unexpected errors
        error = error_generator(
            "[TASKS][CONTROLLER] Internal Server Error",
            str(e),
            500,
            f"tasks/submission/{uuid_task}",
        )
        return error["response"], error["code_status"]


@tasks_bp.post("/upload")
@swag_from(
    {
        "tags": ["Tasks"],
        "summary": "Upload a task file",
        "parameters": [
            {"name": "uuid", "in": "formData", "type": "string", "required": True},
            {
                "name": "task_number",
                "in": "formData",
                "type": "string",
                "required": True,
            },
            {"name": "attachment", "in": "formData", "type": "file", "required": True},
        ],
        "consumes": ["multipart/form-data"],
        "responses": {
            200: {"description": "File uploaded successfully"},
            400: {"description": "Missing fields in form data"},
            422: {"description": "Invalid or empty file"},
            500: {"description": "Internal server error"},
        },
    }
)
def upload_task():
    """
    Student or teacher upload task or exman
    Body is form-data with uuid, attachment and task_number
    """
    try:
        if "uuid" not in request.form and "task_number" not in request.form:
            raise BadRequest("The uuid field is missing from the form.")
        if "attachment" not in request.files:
            raise BadRequest("The attachment is missing from the request.")

        uuid = request.form.get("uuid")
        task_number = request.form.get("task_number")
        attachment = request.files.get("attachment")

        if not attachment or attachment.filename == "":
            raise FileNotFoundError("The attachment is empty or has no name.")

        task_link = service_tasks.upload_task(uuid, task_number, attachment)
        return jsonify({"url": task_link}), 200

    except BadRequest as e:
        # Captures malformed request errors
        error = error_generator("Bad Request", str(e), 400, f"tasks/upload")
        return error["response"], error["code_status"]

    except FileNotFoundError as e:
        # Logical validation of empty or invalid values
        error = error_generator(
            "[TASKS][CONTROLLER] Validation Error", str(e), 422, f"tasks/upload"
        )
        return error["response"], error["code_status"]

    except Exception as e:
        # Catch-all for unexpected errors
        error = error_generator(
            "[TASKS][CONTROLLER] Internal Server Error", str(e), 500, f"tasks/upload"
        )
        return error["response"], error["code_status"]


@tasks_bp.get("/teachers/<string:teacher_id>")
@swag_from(
    {
        "tags": ["Tasks"],
        "summary": "Get tasks by teacher",
        "parameters": [
            {"name": "teacher_id", "in": "path", "type": "string", "required": True},
            {"name": "status", "in": "query", "type": "string"},
            {"name": "date", "in": "query", "type": "string"},
            {"name": "page", "in": "query", "type": "integer"},
            {"name": "limit", "in": "query", "type": "integer"},
        ],
        "responses": {
            200: {"description": "Tasks retrieved successfully"},
            400: {"description": "Invalid parameters"},
            500: {"description": "Internal server error"},
        },
    }
)
def get_tasks_by_teacher(teacher_id):
    try:
        status = request.args.get("status")
        due_date = request.args.get("date")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 1000))

        logger.debug(f"due_date raw: {due_date}, start_date raw: {start_date}, end_date raw: {end_date}")

        if due_date is not None:
            logger.debug("Parsing due_date")
            due_date = parse_date_to_timestamp_ms(due_date)
            
        if start_date is not None and end_date is not None:
            logger.debug("Parsing start_date and end_date")
            start_date = parse_date_to_timestamp_ms(start_date)
            end_date = parse_date_to_timestamp_ms(end_date)
        else:
            start_date = None
            end_date = None

        tasks = service_tasks.get_tasks_by_teacher(
            teacher_id=teacher_id,
            status=status,
            due_date=due_date,
            start_date=start_date,
            end_date=end_date,
            page=page,
            limit=limit,
        )

        return jsonify([t.to_dict() for t in tasks]), 200

    except ValueError as e:
        error = error_generator(
            "[TASKS][CONTROLLER] Invalid date format.",
            f"Use ISO 8601 format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS. {e}",
            400,
            "students/<string:student_id>",
        )
        return error["response"], error["code_status"]

    except Exception as e:
        error = error_generator("[TASKS][CONTROLLER] Error", str(e), 500, "students/<string:student_id>")
        return error["response"], error["code_status"]


@tasks_bp.get("/students/<string:student_id>")
@swag_from(
    {
        "tags": ["Tasks"],
        "summary": "Get tasks for a student",
        "parameters": [
            {"name": "student_id", "in": "path", "type": "string", "required": True},
            {"name": "status", "in": "query", "type": "string"},
            {"name": "course_id", "in": "query", "type": "string"},
            {"name": "date", "in": "query", "type": "string"},
            {"name": "page", "in": "query", "type": "integer"},
            {"name": "limit", "in": "query", "type": "integer"},
        ],
        "responses": {
            200: {"description": "Tasks retrieved successfully"},
            400: {"description": "Invalid parameters"},
            500: {"description": "Internal server error"},
        },
    }
)
def get_tasks_for_student(student_id):
    try:
        status = request.args.get("status")
        course_id = request.args.get("course_id")
        due_date = request.args.get("date")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 1000))

        logger.debug(f"due_date raw: {due_date}, start_date raw: {start_date}, end_date raw: {end_date}")

        if due_date is not None:
            logger.debug("Parsing due_date")
            due_date = parse_date_to_timestamp_ms(due_date)
            
        if start_date is not None and end_date is not None:
            logger.debug("Parsing start_date and end_date")
            start_date = parse_date_to_timestamp_ms(start_date)
            end_date = parse_date_to_timestamp_ms(end_date)
        else:
            start_date = None
            end_date = None

        tasks = service_tasks.get_tasks_by_student(
            student_id=student_id,
            status=status,
            course_id=course_id,
            due_date=due_date,
            start_date=start_date,
            end_date=end_date,
            page=page,
            limit=limit,
        )

        return jsonify([t.to_dict() for t in tasks]), 200
    
    except ValueError as e:
        error = error_generator(
            "[TASKS][CONTROLLER] Invalid date format.",
            f"Use ISO 8601 format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS. {e}",
            400,
            "students/<string:student_id>",
        )
        return error["response"], error["code_status"]

    except Exception as e:
        error = error_generator("[TASKS][CONTROLLER] Error", str(e), 500, "students/<string:student_id>")
        return error["response"], error["code_status"]


def get_header_value_for_key(headers, key):
    """
    Helper function to get a header value in lowercase.
    """
    for k, v in headers.items():
        if k.lower() == key.lower():
            return v

    return None


@tasks_bp.put("/submission/<string:task_id>")
@swag_from(
    {
        "tags": ["Tasks"],
        "summary": "Add or update feedback for a task submission",
        "parameters": [
            {"name": "task_id", "in": "path", "type": "string", "required": True},
            {
                "name": "body",
                "in": "body",
                "required": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "uuid_student": {"type": "string"},
                        "uuid_corrector": {"type": "string"},
                        "grade": {"type": "number", "format": "float"},
                        "comment": {"type": "string"},
                    },
                    "required": ["uuid_student"],
                },
            },
        ],
        "responses": {
            200: {"description": "Feedback added/updated successfully"},
            400: {"description": "Missing required fields"},
            403: {"description": "User not authorized to provide feedback"},
            404: {"description": "Task or submission not found"},
            500: {"description": "Internal server error"},
        },
    }
)
def add_or_update_feedback(task_id):
    try:
        data = request.json
        required_fields = ["uuid_student"]

        for field in required_fields:
            if field not in data:
                return error_generator(
                    MISSING_FIELDS,
                    f"Field {field} is required",
                    400,
                    "add_or_update_feedback",
                )

        student_id = data["uuid_student"]
        corrector_id = data.get("uuid_corrector")
        grade = data.get("grade")
        comment = data.get("comment")

        # Verificar permisos
        task = service_tasks.get_task_by_id(task_id)
        if task["code_status"] != 200:
            return task["response"], task["code_status"]

        # Actualizar o crear la retroalimentación
        result = service_tasks.add_or_update_feedback(
            task_id, student_id, corrector_id, grade, comment
        )

        return result["response"], result["code_status"]

    except Exception as e:
        logger.error(f"[TASKS][CONTROLLER] Error in add_or_update_feedback: {str(e)}")
        return error_generator(
            "Internal Server Error", str(e), 500, "add_or_update_feedback"
        )
