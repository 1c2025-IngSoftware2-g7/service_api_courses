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


@tasks_bp.post('/submission/<uuid_task>')
def submit_task(uuid_task):
    """
    Student: Submit a task/exam response
    """
    try:
        if 'uuid_student' not in request.form:
            raise BadRequest("The uuid_student field is missing from the form.")
        if 'file' not in request.files:
            raise BadRequest("The file is missing from the request.")

        uuid_student = request.form.get('uuid_student')
        file = request.files.get('file')

        if not file or file.filename == '':
            raise FileNotFoundError("The file is empty or has no name.")

        task = service_tasks.submit_task(uuid_task, uuid_student, file)
        return jsonify(task.to_dict()), 200

    except BadRequest as e:
        # Captures malformed request errors
        error = error_generator("Bad Request", str(e), 400, f"tasks/submission/{uuid_task}")
        return error["response"], error["code_status"]

    except FileNotFoundError as e:
        # Logical validation of empty or invalid values
        error = error_generator("Validation Error", str(e), 422, f"tasks/submission/{uuid_task}")
        return error["response"], error["code_status"]

    except Exception as e:
        # Catch-all for unexpected errors
        error = error_generator("Internal Server Error", str(e), 500, f"tasks/submission/{uuid_task}")
        return error["response"], error["code_status"]
