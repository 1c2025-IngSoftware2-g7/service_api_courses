from datetime import datetime, timedelta, time
from google.cloud import storage
import os

from error.error import error_generator
from src.headers import MISSING_FIELDS, COURSE_NOT_FOUND, USER_NOT_ALLOWED_TO_CREATE
from models.task import Task, TaskStatus, TaskType
from repository.tasks_repository import TasksRepository


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
                    MISSING_FIELDS, f"Field {field} is required", 400, "create_task"
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
            # due_date string to datetime with hs
            due_date = data["due_date"]
            if isinstance(due_date, str):
                try:
                    due_date = datetime.strptime(due_date, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    try:
                        # If it fails, try only the date (add 00:00:00)
                        due_date = datetime.strptime(due_date, "%Y-%m-%d")
                    except ValueError:
                        return error_generator(
                            MISSING_FIELDS,
                            "Invalid due_date format. Use 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'",
                            400,
                            "create_task",
                        )

            # Crear la tarea
            task = Task(
                title=data["title"],
                description=data.get("description", ""),
                instructions=data.get("instructions", ""),
                due_date=due_date,
                course_id=data["course_id"],
                status=TaskStatus.INACTIVE,
                task_type=TaskType(data.get("task_type", "task")),
                file_url=data.get("file_url"),
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
            self.logger.error(f"Error creating task: {str(e)}")
            return error_generator(
                "Internal server error",
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
                    "Task not found",
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
                    MISSING_FIELDS, "No fields provided for update", 400, "update_task"
                )

            # Campos permitidos para actualización
            allowed_fields = {
                "title",
                "description",
                "instructions",
                "due_date",
                "task_type",
                "file_url",
                "status",
            }

            # Filtrar solo campos permitidos y que sean diferentes al valor actual
            update_data = {}
            for field in allowed_fields:
                if field in data and data[field] != getattr(existing_task, field):
                    update_data[field] = data[field]

            # Verificar que haya al menos un campo válido para actualizar
            if not update_data:
                return error_generator(
                    "No changes detected",
                    "No valid fields provided for update or values are the same",
                    400,
                    "update_task",
                )

            # Agregar marca de tiempo de actualización
            update_data["updated_at"] = datetime.now()
            # Realizar la actualización en la base de datos
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
                    "Task not modified",
                    "The task could not be updated",
                    400,
                    "update_task",
                )
        except Exception as e:
            self.logger.error(f"Error updating task: {str(e)}")
            return error_generator(
                "Internal server error",
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
                    "Task not found",
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
                    "Task not deleted",
                    "The task could not be deleted",
                    400,
                    "delete_task",
                )
        except Exception as e:
            self.logger.error(f"Error deleting task: {str(e)}")
            return error_generator(
                "Internal server error",
                "An error occurred while deleting the task",
                500,
                "delete_task",
            )

    def get_tasks_by_course(self, course_id: str, status: str = None):
        try:
            # Validar que el curso exista
            course = self.course_service.get_course_by_id(course_id)
            if not course or course["code_status"] != 200:
                return error_generator(
                    COURSE_NOT_FOUND, "Course not found", 404, "get_tasks_by_course"
                )

            # Construir query de búsqueda
            query = {"course_id": course_id}
            if status:
                # Validar que el status sea uno de los permitidos
                if status.lower() not in [s.value for s in TaskStatus]:
                    return error_generator(
                        "Invalid status",
                        f"Status must be one of: {[s.value for s in TaskStatus]}",
                        400,
                        "get_tasks_by_course",
                    )
                query["status"] = status.lower()

            # Obtener tareas
            tasks = self.repository.get_tasks_by_query(query)

            return {"response": [task.to_dict() for task in tasks], "code_status": 200}
        except Exception as e:
            self.logger.error(f"Error getting tasks by course: {str(e)}")
            return error_generator(
                "Internal server error",
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
            self.logger.error(f"Error getting task: {str(e)}")
            return error_generator(
                "Internal server error",
                "An error occurred while getting the task",
                500,
                "get_task_by_id",
            )

    def submit_task(self, task_id, student_id, attachment_links):
        return self.repository.add_task_submission(
            task_id, student_id, attachment_links
        )

    def upload_task(self, uuid, num_task, file):
        file_link = self._upload_element(uuid, num_task, file)
        return file_link

    def _upload_element(self, uuid, num, file):
        if file.filename == "":
            return FileNotFoundError(
                "No selected file: Missing file.filename in the request"
            )

        url = self._save_file(uuid, num, file)
        self.logger.info(f"File saved in Google Cloud Storage ")

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
            self.logger.error(f"Error getting tasks for teacher {teacher_id}: {str(e)}")
            raise e
