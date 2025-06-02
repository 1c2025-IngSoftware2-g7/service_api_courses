from datetime import datetime, timedelta, timezone
from typing import Optional
from google.cloud import storage
import os

from error.error import error_generator
from models.submission import Feedback
from headers import MISSING_FIELDS, COURSE_NOT_FOUND, USER_NOT_ALLOWED_TO_CREATE
from models.task import Task, TaskStatus, TaskType
from repository.tasks_repository import TasksRepository
from utils import parse_date_to_timestamp_ms, parse_to_timestamp_ms_now


class TaskService:
    def __init__(
        self,
        tasks_repository: TasksRepository,
        course_service,
        user_service,
        repository_courses,
        logger,
    ):
        self.repository = tasks_repository
        self.service_users = user_service
        self.repository_courses = repository_courses
        self.course_service = course_service
        self.logger = logger

    def create_task(self, data: dict, creator_user_uuid: str):

        required_fields = ["title", "due_date", "course_id"]
        for field in required_fields:
            if field not in data:
                return error_generator(
                    f"[TASKS][SERVICE] {MISSING_FIELDS}",
                    f"Field {field} is required",
                    400,
                    "create_task",
                )

        course_id = data["course_id"]

        perm_required = "Tasks" if data.get("task_type", "task") == "task" else "Exams"

        has_permissions = self.service_users.check_assistants_permissions(
            course_id, creator_user_uuid, perm_required
        )

        is_owner_course = self.repository_courses.is_user_owner(
            course_id, creator_user_uuid
        )

        # Here we need to check if its either the owner of the course or an assistant
        self.logger.debug(
            f"[MODULE SERVICE TASK] has_permissions as assistant? : {has_permissions} <<<<<======="
        )
        self.logger.debug(
            f"[MODULE SERVICE TAKS] is_owner_course? : {is_owner_course} <<<<<======="
        )

        if not has_permissions and not is_owner_course:
            return error_generator(
                USER_NOT_ALLOWED_TO_CREATE,
                "User is not allowed to create module",
                403,
                "add_module_to_course",
            )

        # Validar que el curso exista
        course = self.course_service.get_course_by_id(course_id)
        if not course or course["code_status"] != 200:
            return error_generator(
                COURSE_NOT_FOUND, "Course not found", 404, "create_task"
            )

        try:
            due_date_raw = data["due_date"]
            due_date_timestamp = None

            if isinstance(due_date_raw, int):
                due_date_timestamp = due_date_raw
            elif isinstance(due_date_raw, str):
                try:
                    due_date_dt = datetime.strptime(due_date_raw, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    try:
                        due_date_dt = datetime.strptime(due_date_raw, "%Y-%m-%d")
                    except ValueError:
                        return error_generator(
                            f"[TASKS][SERVICE] {MISSING_FIELDS}",
                            "Invalid due_date format. Use 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'",
                            400,
                            "create_task",
                        )
                if due_date_dt.tzinfo is None:
                    due_date_dt = due_date_dt.replace(tzinfo=timezone.utc)
                else:
                    due_date_dt = due_date_dt.astimezone(timezone.utc)

                due_date_timestamp = int(due_date_dt.timestamp() * 1000)
            else:
                return error_generator(
                    f"[TASKS][SERVICE] {MISSING_FIELDS}",
                    "due_date must be int (timestamp ms) or string",
                    400,
                    "create_task",
                )

            task = Task(
                title=data["title"],
                description=data.get("description", ""),
                instructions=data.get("instructions", ""),
                due_date=due_date_timestamp,
                course_id=data["course_id"],
                module_id=data.get("module_id", ""),
                status=TaskStatus.INACTIVE,
                task_type=TaskType(data.get("task_type", "task")),
                attachments=data.get("attachments", []),
            )

            task_id = self.repository.create_task(task)

            return {
                "response": {
                    "type": "about:blank",
                    "title": "Task created",
                    "status": 201,
                    "detail": f"Task created with ID {task_id}",
                    "instance": f"/courses/tasks/{task_id}",
                },
                "code_status": 201,
            }
        except Exception as e:
            self.logger.error(f"[TASKS][SERVICE] Error creating task: {str(e)}")
            return error_generator(
                "[TASKS][SERVICE] Internal server error",
                "An error occurred while creating the task",
                500,
                "create_task",
            )

    def update_task(self, task_id: str, data: dict, creator_user_uuid: str):
        try:
            # Verificar que la tarea exista
            query = {"_id": task_id}

            # Obtener tareas
            existing_task = self.repository.get_tasks_by_query(query)[0]
            # Verificar que la tarea exista
            # existing_task = self.repository.get_task_by_id(task_id)
            if not existing_task:
                return error_generator(
                    "[TASKS][SERVICE] Task not found",
                    "The specified task does not exist",
                    404,
                    "update_task",
                )

            course_id = existing_task.course_id
            # This will give us the required flag to modify the item
            perm_required_to_update_data = (
                "Exams" if existing_task.task_type == TaskType.EXAM else "Tasks"
            )

            has_permissions = self.service_users.check_assistants_permissions(
                course_id, creator_user_uuid, perm_required_to_update_data
            )
            is_owner_course = self.repository_courses.is_user_owner(
                course_id, creator_user_uuid
            )

            # Here we need to check if its either the owner of the course or an assistant
            self.logger.debug(
                f"[MODULE SERVICE TASK] has_permissions as assistant? : {has_permissions} <<<<<======="
            )
            self.logger.debug(
                f"[MODULE SERVICE TAKS] is_owner_course? : {is_owner_course} <<<<<======="
            )

            if not has_permissions and not is_owner_course:
                return error_generator(
                    USER_NOT_ALLOWED_TO_CREATE,
                    "User is not allowed to create module",
                    403,
                    "add_module_to_course",
                )

            # Validar que hay datos para actualizar
            if not data:
                return error_generator(
                    f"[TASKS][SERVICE] {MISSING_FIELDS}",
                    "No fields provided for update",
                    400,
                    "update_task",
                )

            # Campos permitidos para actualización
            allowed_fields = {
                "title",
                "description",
                "instructions",
                "due_date",
                "task_type",
                "attachments",
                "status",
            }

            # Filtrar solo campos permitidos y que sean diferentes al valor actual
            update_data = {}
            for field in allowed_fields:
                if field in data:
                    new_value = data[field]

                    # Manejo especial para due_date si viene como string
                    if field == "due_date":
                        if isinstance(new_value, str):
                            try:
                                new_value = parse_date_to_timestamp_ms(new_value)
                            except ValueError:
                                return error_generator(
                                    f"[TASKS][SERVICE] {MISSING_FIELDS}",
                                    "Invalid due_date format. Use 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'",
                                    400,
                                    "update_task",
                                )
                        elif not isinstance(new_value, int):
                            return error_generator(
                                f"[TASKS][SERVICE] {MISSING_FIELDS}",
                                "due_date must be an integer (timestamp in ms) or a valid date string",
                                400,
                                "update_task",
                            )

                    # Solo guardar si realmente cambió
                    if new_value != getattr(existing_task, field):
                        update_data[field] = new_value

            if not update_data:
                return error_generator(
                    "[TASKS][SERVICE] No changes detected",
                    "No valid fields provided for update or values are the same",
                    400,
                    "update_task",
                )

            # Timestamp de actualización en ms
            update_data["updated_at"] = int(
                datetime.now(timezone.utc).timestamp() * 1000
            )

            updated = self.repository.update_task(task_id, update_data)

            if updated:
                return {
                    "response": {
                        "type": "about:blank",
                        "title": "Task updated",
                        "status": 200,
                        "detail": f"Task with ID {task_id} updated successfully",
                        "instance": f"/courses/tasks/{task_id}",
                    },
                    "code_status": 200,
                }
            else:
                return error_generator(
                    "[TASKS][SERVICE] Task not modified",
                    "The task could not be updated",
                    400,
                    "update_task",
                )
        except Exception as e:
            self.logger.error(f"Error updating task: {str(e)}")
            return error_generator(
                "[TASKS][SERVICE] Internal server error",
                "An error occurred while updating the task",
                500,
                "update_task",
            )

    def delete_task(self, task_id: str, creator_user_uuid: str):
        try:
            # Verificar que la tarea exista
            query = {"_id": task_id}

            # Obtener tareas
            existing_task = self.repository.get_tasks_by_query(query)[0]
            # existing_task = self.repository.get_task_by_id(task_id)
            if not existing_task:
                return error_generator(
                    "[TASKS][SERVICE] Task not found",
                    "The specified task does not exist",
                    404,
                    "delete_task",
                )

            course_id = existing_task.course_id
            # This will give us the required flag to modify the item
            perm_required_to_update_data = (
                "Exams" if existing_task.task_type == TaskType.EXAM else "Tasks"
            )

            has_permissions = self.service_users.check_assistants_permissions(
                course_id, creator_user_uuid, perm_required_to_update_data
            )
            is_owner_course = self.repository_courses.is_user_owner(
                course_id, creator_user_uuid
            )

            # Here we need to check if its either the owner of the course or an assistant
            self.logger.debug(
                f"[MODULE SERVICE TASK] has_permissions as assistant? : {has_permissions} <<<<<======="
            )
            self.logger.debug(
                f"[MODULE SERVICE TAKS] is_owner_course? : {is_owner_course} <<<<<======="
            )

            if not has_permissions and not is_owner_course:
                return error_generator(
                    USER_NOT_ALLOWED_TO_CREATE,
                    "User is not allowed to create module",
                    403,
                    "add_module_to_course",
                )

            # Eliminar la tarea
            deleted = self.repository.delete_task(task_id)

            if deleted:
                return {
                    "response": {
                        "type": "about:blank",
                        "title": "Task deleted",
                        "status": 200,
                        "detail": f"Task with ID {task_id} deleted successfully",
                        "instance": f"/courses/tasks/{task_id}",
                    },
                    "code_status": 200,
                }
            else:
                return error_generator(
                    "[TASKS][SERVICE] Task not deleted",
                    "The task could not be deleted",
                    400,
                    "delete_task",
                )
        except Exception as e:
            self.logger.error(f"Error deleting task: {str(e)}")
            return error_generator(
                "[TASKS][SERVICE] Internal server error",
                "An error occurred while deleting the task",
                500,
                "delete_task",
            )

    def get_tasks_by_course(
        self, course_id: str, status: str = None, module_id: str = None
    ):
        try:
            # Validar que el curso exista
            course = self.course_service.get_course_by_id(course_id)
            if not course or course["code_status"] != 200:
                return error_generator(
                    f"[TASKS][SERVICE] {COURSE_NOT_FOUND}",
                    "Course not found",
                    404,
                    "get_tasks_by_course",
                )

            # Construir query de búsqueda
            query = {"course_id": course_id}
            if status:
                # Validar que el status sea uno de los permitidos
                if status.lower() not in [s.value for s in TaskStatus]:
                    return error_generator(
                        "[TASKS][SERVICE] Invalid status",
                        f"Status must be one of: {[s.value for s in TaskStatus]}",
                        400,
                        "get_tasks_by_course",
                    )
                query["status"] = status.lower()

            if module_id:
                query["module_id"] = module_id

            # Obtener tareas
            tasks = self.repository.get_tasks_by_query(query)

            return {"response": [task.to_dict() for task in tasks], "code_status": 200}
        except Exception as e:
            self.logger.error(
                f"[TASKS][SERVICE] Error getting tasks by course: {str(e)}"
            )
            return error_generator(
                "[TASKS][SERVICE] Internal server error",
                "An error occurred while getting tasks",
                500,
                "get_tasks_by_course",
            )

    def get_task_by_id(self, task_id: str):
        try:

            # Construir query de búsqueda
            query = {"_id": task_id}

            # Obtener tareas
            task = self.repository.get_tasks_by_query(query)[0]
            # task = self.repository.get_task_by_id(task_id)
            if not task:
                return error_generator(
                    "Task not found",
                    "The specified task does not exist",
                    404,
                    "get_task_by_id",
                )

            return {"response": task.to_dict(), "code_status": 200}
        except Exception as e:
            self.logger.error(f"[TASKS][SERVICE] Error getting task: {str(e)}")
            return error_generator(
                "[TASKS][SERVICE] Internal server error",
                "An error occurred while getting the task",
                500,
                "get_task_by_id",
            )

    def submit_task(self, task_id, student_id, attachments):
        return self.repository.add_task_submission(task_id, student_id, attachments)

    def upload_task(self, uuid, num_task, file):
        file_link = self._upload_element(uuid, num_task, file)
        return file_link

    def _upload_element(self, uuid, num, file):
        if file.filename == "":
            return FileNotFoundError(
                "[TASKS][SERVICE] No selected file: Missing file.filename in the request"
            )

        url = self._save_file(uuid, num, file)
        self.logger.info(f"[TASKS][SERVICE] File saved in Google Cloud Storage ")

        return url

    def _save_file(self, uuid, num, file):
        """Save the file to GCP."""
        bucket = self._get_gcp_bucket()
        ext = os.path.splitext(file.filename)[
            1
        ]  # Extract extension (.pdf, .jpg, .png, etc.)
        filename = f"{uuid}{num}{ext}"
        blob = bucket.blob(filename)
        blob.upload_from_file(file, content_type=file.content_type)
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=15),
            method="GET",
        )
        return url

    def _get_gcp_bucket(self):
        # Reconstruct JSON file from environment variable:
        credentials_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
        json_path = "/tmp/gcs-key.json"
        with open(json_path, "w") as f:
            f.write(credentials_json)

        # Initialize GCS:
        storage_client = storage.Client.from_service_account_json(json_path)
        bucket = storage_client.bucket(os.getenv("GCS_BUCKET_NAME"))
        return bucket

    def get_tasks_by_teacher(
        self, teacher_id, status=None, due_date=None, page=1, limit=10
    ):
        try:
            courses = self.course_service.get_courses_owned_by_user(teacher_id)

            if not courses:
                self.logger.info(
                    f"[TAKS][SERVICES] Teacher {teacher_id} has not courses."
                )
                return []

            course_ids = [c._id for c in courses]

            tasks = self.repository.get_tasks_by_course_ids(
                course_ids=course_ids,
                status=status,
                due_date=due_date,
                page=page,
                limit=limit,
            )

            return tasks

        except Exception as e:
            self.logger.error(
                f"[TASKS][SERVICE] Error getting tasks for teacher {teacher_id}: {str(e)}"
            )
            raise e

    def get_tasks_by_student(
        self, student_id, status=None, course_id=None, due_date=None, page=1, limit=10
    ):
        try:
            # Obtain courses you are enrolled in
            courses = self.course_service.get_courses_by_student_id(student_id)
            if not courses:
                return []

            course_ids = [c._id for c in courses]

            if course_id and course_id in course_ids:
                course_ids = [course_id]  # filter by course

            tasks = self.repository.get_tasks_by_course_ids(
                course_ids=course_ids,
                status=status,
                due_date=due_date,
                page=page,
                limit=limit,
            )

            final_tasks = []
            for task in tasks:
                task.status = self._calculate_status(task, student_id)
                task.submissions = self._get_submission(task, student_id)
                final_tasks.append(task)

            return final_tasks
        except Exception as e:
            self.logger.error(
                f"[TASKS][SERVICE] Error getting tasks for student {student_id}: {str(e)}"
            )
            raise e

    def _calculate_status(self, task: Task, student_id: str) -> str:
        """
        Determines the status of a task for a given student.

        The status is calculated based on whether the student has submitted the task
        and whether the due date has passed.

        Returns:
            - "completed" if the student has submitted the task.
            - "overdue" if the due date has passed and the student has not submitted.
            - "pending" if the due date has not passed and there is no submission.
        """
        submissions = task.submissions

        if student_id in submissions:
            return TaskStatus.COMPLETED

        due_date_ts = task.due_date

        if due_date_ts and isinstance(due_date_ts, int):
            now_ts = parse_to_timestamp_ms_now()
            if now_ts > due_date_ts:
                return TaskStatus.OVERDUE

        return TaskStatus.PENDING

    def _get_submission(self, task, student_id):
        submission = task.submissions.get(student_id)
        if submission:
            return {student_id: submission}
        return {}

    def add_or_update_feedback(
        self,
        task_id: str,
        student_id: str,
        corrector_id: Optional[str] = None,
        grade: Optional[float] = None,
        comment: Optional[str] = None
    ):
        try:
            # Obtener la tarea actual
            task_query = {"_id": task_id}
            tasks = self.repository.get_tasks_by_query(task_query)
            if not tasks:
                return error_generator(
                    "Task not found",
                    "The specified task does not exist",
                    404,
                    "add_or_update_feedback"
                )

            task = tasks[0]

            # Verificar que existe una submission del estudiante
            if student_id not in task.submissions:
                return error_generator(
                    "Submission not found",
                    "The student has not submitted this task",
                    404,
                    "add_or_update_feedback"
                )

            # Obtener la submission
            submission = task.submissions[student_id]
            existing_corrector_id = next(
                iter(submission.feedbacks.keys()), None)

            # Caso 1: Desasignar corrector (corrector_id es None)
            if corrector_id is None:
                if submission.feedbacks:
                    # Mantener el feedback pero con corrector_id como None
                    feedback = next(iter(submission.feedbacks.values()))
                    feedback.corrector_id = None
                    feedback.created_at = parse_to_timestamp_ms_now()

                    update_data = {
                        f"submissions.{student_id}.feedbacks.{None}": feedback.to_dict()
                    }

                    # Eliminar el feedback anterior
                    self.repository.update_task(task_id, {
                        f"submissions.{student_id}.feedbacks.$unset": {list(submission.feedbacks.keys())[0]: ""}
                    })

                    updated = self.repository.update_task(task_id, update_data)

                    if updated:
                        return {
                            "response": {
                                "type": "about:blank",
                                "title": "Corrector unassigned",
                                "status": 200,
                                "detail": "Corrector unassigned but feedback preserved",
                                "instance": f"/courses/tasks/submission/{task_id}"
                            },
                            "code_status": 200
                        }
                else:
                    return error_generator(
                        "No feedback found",
                        "There is no feedback to unassign",
                        400,
                        "add_or_update_feedback"
                    )

            # Caso 2: Asignar/Actualizar corrector
            # Validación: Si ya hay un corrector diferente
            if existing_corrector_id and existing_corrector_id != corrector_id:
                return error_generator(
                    "Invalid corrector change",
                    "Cannot change the assigned corrector. You can only update the current corrector or unassign.",
                    400,
                    "add_or_update_feedback"
                )

            # Crear o actualizar el feedback
            if corrector_id in submission.feedbacks:
                # Actualizar feedback existente
                feedback = submission.feedbacks[corrector_id]
                if grade is not None:
                    feedback.grade = grade
                if comment is not None:
                    feedback.comment = comment
                feedback.created_at = parse_to_timestamp_ms_now()
            else:
                # Crear nuevo feedback
                feedback = Feedback(
                    corrector_id=corrector_id,
                    grade=grade,
                    comment=comment
                )

            # Preparar datos para actualización
            update_data = {
                f"submissions.{student_id}.feedbacks.{corrector_id}": feedback.to_dict()
            }

            updated = self.repository.update_task(task_id, update_data)

            if updated:
                return {
                    "response": {
                        "type": "about:blank",
                        "title": "Feedback updated",
                        "status": 200,
                        "detail": f"Feedback for student {student_id} updated successfully",
                        "instance": f"/courses/tasks/submission/{task_id}"
                    },
                    "code_status": 200
                }
            else:
                return error_generator(
                    "Update failed",
                    "Failed to update feedback",
                    500,
                    "add_or_update_feedback"
                )

        except Exception as e:
            self.logger.error(
                f"[TASK SERVICE] Error in add_or_update_feedback: {str(e)}")
            return error_generator(
                "Internal Server Error",
                str(e),
                500,
                "add_or_update_feedback"
            )
