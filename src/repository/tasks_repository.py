from bson import ObjectId
from models.submission import Submission
from models.task import Task


class TasksRepository:
    def __init__(self, collection, logger):
        self.collection = collection
        self.logger = logger


    def create_task(self, task: Task):
        try:
            result = self.collection.insert_one(task.to_dict())
            self.logger.debug(f"Task created with id: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            self.logger.error(f"Error creating task: {str(e)}")
            raise e

    def get_task_by_id(self, task_id: str):
        try:
            task = self.collection.find_one({"_id": task_id})
            return Task.from_dict(task) if task else None
        except Exception as e:
            self.logger.error(f"Error getting task {task_id}: {str(e)}")
            raise e

    def update_task(self, task_id: str, update_data: dict):
        try:
            result = self.collection.update_one(
                {"_id": task_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            self.logger.error(f"Error updating task {task_id}: {str(e)}")
            raise e


    def delete_task(self, task_id: str):
        try:
            result = self.collection.delete_one({"_id": task_id})
            return result.deleted_count > 0
        except Exception as e:
            self.logger.error(f"Error deleting task {task_id}: {str(e)}")
            raise e


    def get_tasks_by_query(self, query: dict):
        try:
            tasks = self.collection.find(query)
            return [Task.from_dict(task) for task in tasks]
        except Exception as e:
            self.logger.error(f"Error getting tasks by query: {str(e)}")
            raise e
        
    def get_task_with_submission_for_student(self, task_id, student_id):
        task = self.get_task_by_id(task_id)
        if not task:
            return None

        # Filter submissions to have only the student_id
        filtered_submissions = {}
        if student_id in task.submissions:
            filtered_submissions[student_id] = task.submissions[student_id]

        task.submissions = filtered_submissions

        return task

    def add_task_submission(self, task_id, student_id, attachment_links: list[str]):
        if not isinstance(task_id, ObjectId):
            task_id = ObjectId(task_id)

        submission = Submission(attachment_links=attachment_links, feedback=None)

        update_result = self.collection.update_one(
            {"_id": task_id},
            {"$set": {f"submissions.{student_id}": submission.to_dict()}}
        )

        if update_result.matched_count == 0:
            raise ValueError("Task not found")

        self.logger.info(f"Submission recorded for student {student_id} on task {task_id}")

        task = self.get_task_with_submission_for_student(task_id, student_id)
        return task
