from pymongo import ReturnDocument
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
            self.logger.debug(
                f"[TASKS][REPOSITORY] Task created with id: {result.inserted_id}"
            )
            return str(result.inserted_id)
        except Exception as e:
            self.logger.error(f"[TASKS][REPOSITORY] Error creating task: {str(e)}")
            raise e

    def get_task_by_id(self, task_id: str):
        try:
            task = self.collection.find_one({"_id": task_id})
            return Task.from_dict(task) if task else None
        except Exception as e:
            self.logger.error(
                f"[TASKS][REPOSITORY] Error getting task {task_id}: {str(e)}"
            )
            raise e

    def delete_task(self, task_id: str):
        try:
            result = self.collection.delete_one({"_id": task_id})
            return result.deleted_count > 0
        except Exception as e:
            self.logger.error(
                f"[TASKS][REPOSITORY] Error deleting task {task_id}: {str(e)}"
            )
            raise e

    def get_tasks_by_query(self, query: dict):
        try:
            tasks = self.collection.find(query)
            return [Task.from_dict(task) for task in tasks if task is not None]
        except Exception as e:
            self.logger.error(
                f"[TASKS][REPOSITORY] Error getting tasks by query: {str(e)}"
            )
            raise e

    def get_task_with_submission_for_student(self, task_id, student_id):
        query = {"_id": task_id}
        task = self.get_tasks_by_query(query)[0]
        if not task:
            return None

        # Filter submissions to have only the student_id
        filtered_submissions = {}
        if student_id in task.submissions:
            filtered_submissions[student_id] = task.submissions[student_id]

        task.submissions = filtered_submissions

        return task

    def add_task_submission(self, task_id, student_id, attachments: list[dict]):

        submission = Submission(attachments=attachments, feedbacks=None)

        update_result = self.collection.update_one(
            {"_id": task_id},
            {"$set": {f"submissions.{student_id}": submission.to_dict()}},
        )

        if update_result.matched_count == 0:
            raise ValueError("Task not found")

        self.logger.info(
            f"[TASKS][REPOSITORY] Submission recorded for student {student_id} on task {task_id}"
        )

        task = self.get_task_with_submission_for_student(task_id, student_id)
        return task

    def get_tasks_by_course_ids(
        self, course_ids, status=None, due_date=None, start_date=None, end_date=None, page=1, limit=10
    ):
        query = {"course_id": {"$in": course_ids}}

        if status:
            query["status"] = status

        # If exact due_date was passed:
        if due_date:
            query["due_date"] = due_date
        # If a date range was passed:
        elif start_date and end_date:
            date_range = {}
            if start_date:
                date_range["$gte"] = start_date  # timestamp in ms
            if end_date:
                date_range["$lte"] = end_date
            query["due_date"] = date_range

        skip = (page - 1) * limit

        tasks = list(self.collection.find(query).skip(skip).limit(limit))

        return [Task.from_dict(t) for t in tasks]

    def update_task(self, task_id: str, update_data: dict):
        try:
            updated_task = self.collection.find_one_and_update(
                {"_id": task_id},
                update_data,
                return_document=ReturnDocument.AFTER
            )
            return Task.from_dict(updated_task)
        except Exception as e:
            self.logger.error(
                f"[TASKS][REPOSITORY] Error updating task {task_id}: {str(e)}"
            )
            raise e

    def get_tasks_done_by_student(self, student_id: str, course_id: str = None):
        """
        Get all tasks done by a student for a certain course.
        A task is completed if status == completed
        The query start as 
        First filter by course_id
        then search submittions with status completed
        """
    
        query = {
            "course_id": course_id,
            "status": "completed",
            # Now search on submissions (dictionary) contains the # student_id as key
            "submissions": { "$exists": True, "$ne": {} },
            "submissions." + student_id: { "$exists": True }
        }
        
        task = self.collection.find(query)
        
        return [Task.from_dict(t) for t in task if t is not None]
        
    def clean_task(self, task_id):
        self.collection.update_one(
            {
                "_id": str(task_id),
            },
            {
                "$set": {
                    "status": "inactive",
                    "submissions": {}
                }
            }
        )
