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
