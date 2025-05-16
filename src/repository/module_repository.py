from bson import ObjectId


class ModuleRepository:
    def __init__(
        self, collection_modules_and_resources, logger
    ):
        self.collection_modules = collection_modules_and_resources
        self.logger = logger
        
    def get_modules_from_course(self, course_id):
        """
        Get all modules from a course.
        """
        modules = list(
            self.collection_modules.find({"course_id": course_id})
        )
        
        self.logger.debug(f"[REPOSITORY] Retrieved modules for course with ID: {course_id}")
        
        return modules
    
    def add_module_to_course(self, course_id, module):
        
        module_as_dict = module.to_dict()
        
        result = self.collection_modules.update_one(
            {"course_id": ObjectId(course_id)}, {"$addToSet": {"modules": module_as_dict}}
        )

        self.logger.debug(f"[REPOSITORY] Add module {module} to course {course_id}")
        return result.modified_count > 0