from datetime import datetime
from error.error import error_generator
from src.headers import MISSING_FIELDS, COURSE_NOT_FOUND
from models.task import Task, TaskStatus, TaskType
from repository.tasks_repository import TasksRepository


class TaskService:
    def __init__(self, tasks_repository: TasksRepository, course_service, logger):
        self.repository = tasks_repository
        self.course_service = course_service
        self.logger = logger

    def create_task(self, data: dict):
        required_fields = ["title", "due_date", "course_id"]
        for field in required_fields:
            if field not in data:
                return error_generator(
                    MISSING_FIELDS,
                    f"Field {field} is required",
                    400,
                    "create_task"
                )

        # Validar que el curso exista
        course = self.course_service.get_course_by_id(data["course_id"])
        if not course or course["code_status"] != 200:
            return error_generator(
                COURSE_NOT_FOUND,
                "Course not found",
                404,
                "create_task"
            )

        try:
            # Crear la tarea
            task = Task(
                title=data["title"],
                description=data.get("description", ""),
                instructions=data.get("instructions", ""),
                due_date=data["due_date"],
                course_id=data["course_id"],
                status=TaskStatus.INACTIVE,
                task_type=TaskType(data.get("task_type", "task")),
                file_url=data.get("file_url")
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
                "create_task"
            )
    

    def update_task(self, task_id: str, data: dict):
        try:
            # Verificar que la tarea exista
            query = {"_id": task_id}

            # Obtener tareas
            existing_task = self.repository.get_tasks_by_query(query)[0]
            # Verificar que la tarea exista
            #existing_task = self.repository.get_task_by_id(task_id)
            if not existing_task:
                return error_generator(
                    "Task not found",
                    "The specified task does not exist",
                    404,
                    "update_task"
                )

            # Validar que hay datos para actualizar
            if not data:
                return error_generator(
                    MISSING_FIELDS,
                    "No fields provided for update",
                    400,
                    "update_task"
                )

            # Campos permitidos para actualización
            allowed_fields = {
                'title', 'description', 'instructions',
                'due_date', 'task_type', 'file_url', 'status'
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
                    "update_task"
                )

            # Agregar marca de tiempo de actualización
            update_data['updated_at'] = datetime.now()
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
                    "update_task"
                )
        except Exception as e:
            self.logger.error(f"Error updating task: {str(e)}")
            return error_generator(
                "Internal server error",
                "An error occurred while updating the task",
                500,
                "update_task"
            )


    def delete_task(self, task_id: str):
        #try:
            # Verificar que la tarea exista
            query = {"_id": task_id}

            # Obtener tareas
            existing_task = self.repository.get_tasks_by_query(query)[0]
            #existing_task = self.repository.get_task_by_id(task_id)
            if not existing_task:
                return error_generator(
                    "Task not found",
                    "The specified task does not exist",
                    404,
                    "delete_task"
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
                    "delete_task"
                )
        # except Exception as e:
        #     self.logger.error(f"Error deleting task: {str(e)}")
        #     return error_generator(
        #         "Internal server error",
        #         "An error occurred while deleting the task",
        #         500,
        #         "delete_task"
        #     )


    def get_tasks_by_course(self, course_id: str, status: str = None):
        try:
            # Validar que el curso exista
            course = self.course_service.get_course_by_id(course_id)
            if not course or course["code_status"] != 200:
                return error_generator(
                    COURSE_NOT_FOUND,
                    "Course not found",
                    404,
                    "get_tasks_by_course"
                )

            # Construir query de búsqueda
            query = {"course_id": course_id}
            if status:
                query["status"] = status

            # Obtener tareas
            tasks = self.repository.get_tasks_by_query(query)

            return {
                "response": [task.to_dict() for task in tasks],
                "code_status": 200
            }
        except Exception as e:
            self.logger.error(f"Error getting tasks by course: {str(e)}")
            return error_generator(
                "Internal server error",
                "An error occurred while getting tasks",
                500,
                "get_tasks_by_course"
            )


    def get_task_by_id(self, task_id: str):
        try:

            # Construir query de búsqueda
            query = {"_id": task_id}

            # Obtener tareas
            task = self.repository.get_tasks_by_query(query)[0]
            #task = self.repository.get_task_by_id(task_id)
            if not task:
                return error_generator(
                    "Task not found",
                    "The specified task does not exist",
                    404,
                    "get_task_by_id"
                )

            return {
                "response": task.to_dict(),
                "code_status": 200
            }
        except Exception as e:
            self.logger.error(f"Error getting task: {str(e)}")
            return error_generator(
                "Internal server error",
                "An error occurred while getting the task",
                500,
                "get_task_by_id"
            )
