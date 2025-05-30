from bson import ObjectId
from src.models.task import Task
from src.services.logger_config import get_logger

logger = get_logger("tasks-repository")


class TasksRepository:
    def __init__(self, collection, logger):
        self.collection = collection
        self.logger = logger


    def create_task(self, task: Task):
        try:
            result = self.collection.insert_one(task.to_dict())
            logger.debug(f"Task created with id: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            raise e

    def get_task_by_id(self, task_id: str):
        try:
            task = self.collection.find_one({"_id": ObjectId(task_id)})
            return Task.from_dict(task) if task else None
        except Exception as e:
            logger.error(f"Error getting task {task_id}: {str(e)}")
            raise e

    def update_task(self, task_id: str, update_data: dict):
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(task_id)},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            self.logger.error(f"Error updating task {task_id}: {str(e)}")
            raise e


    def delete_task(self, task_id: str):
        try:
            result = self.collection.delete_one({"_id": ObjectId(task_id)})
            return result.deleted_count > 0
        except Exception as e:
            self.logger.error(f"Error deleting task {task_id}: {str(e)}")
            raise e

