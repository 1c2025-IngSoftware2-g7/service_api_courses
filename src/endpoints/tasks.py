from flask import Blueprint, request, jsonify

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
        uuid_student = request.form.get('uuid_student')
        file = request.files['file']

        if not uuid_student or not file:
            error = error_generator(MISSING_FIELDS, "uuid_student and file are required", 400, "/tasks/submission/<uuid_task>")
            return error["response"], error["code_status"]

        task = service_tasks.submit_task(uuid_task, uuid_student, file)
        return jsonify(task.to_dict()), 200
    except Exception as e:
        return error_generator("Error", str(e), 500, "/tasks/submission/<uuid_task>")
