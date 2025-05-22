from bson import ObjectId
from src.models.module import Module


class ModuleRepository:
    def __init__(self, collection_modules_and_resources, collection_courses, logger):
        self.collection_modules = collection_modules_and_resources
        self.collection_courses = collection_courses
        self.logger = logger

    def get_modules_from_course(self, course_id):
        """
        Get all modules from a course.
        """

        # Lets find all modules for the course
        course = self.collection_modules.find_one({"course_id": ObjectId(course_id)})
        
        if not course:
            self.logger.debug(f"[MODULE REPOSITORY] Course with ID: {course_id} not found")
            return []
        
        modules = course.get("modules", [])
    
        self.logger.debug(
            f"[MODULE REPOSITORY] Retrieved modules for course with ID: {course_id}"
        )
        
        self.logger.debug(f"[TYPE] {type(modules)} {type(self.collection_modules)}")

        return list(modules)

    def add_module_to_course(self, course_id, module: Module):

        module_as_dict = module.to_dict()
        
        # Lets check if the course exists
        course = self.collection_modules.find_one({"course_id": ObjectId(course_id)})
        
        if course:
            # If course exist, we update the module list
            self.collection_modules.update_one(
                {"course_id": ObjectId(course_id)},
                {"$addToSet": {"modules": module_as_dict}},
            )
        else:
            # If course doesn't exist, we create it
            self.collection_modules.insert_one(
                {
                    "course_id": ObjectId(course_id),
                    "modules": [module_as_dict],
                }
            )
        
        # We also update the course with the new module
        self.collection_courses.update_one(
            {"_id": ObjectId(course_id)},
            {"$addToSet": {"modules": module_as_dict["_id"]}},
        )

        '''result = self.collection_modules.update_one(
            {"course_id": ObjectId(course_id)},
            {"$addToSet": {"modules": module_as_dict}},
        )'''

        self.logger.debug(f"[MODULE REPOSITORY] Add module {module} to course {course_id}")
        return module_as_dict["_id"]

    def modify_module_in_course(self, new_course_data_as_dict, course_id, module_id):
        """
        Modify a module in a course, including swapping its position with another module if needed.
        """
        course_id_obj = ObjectId(course_id)
        module_id_obj = module_id

        # Step 1: Find the course that contains the target module
        course_doc = self.collection_modules.find_one(
            {"course_id": course_id_obj, "modules._id": module_id_obj}
        )

        if not course_doc:
            self.logger.debug(f"[MODULE REPOSITORY] Module {module_id} not found in course {course_id}")
            return False

        # Extract current position of the module to be modified
        current_module = next((mod for mod in course_doc["modules"] if mod["_id"] == module_id_obj), None)
        if not current_module:
            self.logger.debug(f"[MODULE REPOSITORY] Module with ID {module_id} not found in course document.")
            return False

        current_position = current_module["position"]
        new_position = new_course_data_as_dict.get("position", current_position)

        # Step 2: Check if a swap is necessary
        if current_position != new_position:
            # Try to find a module at the desired position
            swap_course_doc = self.collection_modules.find_one(
                {"course_id": course_id_obj, "modules.position": new_position}
            )

            if swap_course_doc:
                swap_module = next(
                    (mod for mod in swap_course_doc["modules"] if mod["position"] == new_position),
                    None
                )

                if swap_module and swap_module["_id"] != module_id_obj:
                    # Perform atomic swap using array filters
                    result = self.collection_modules.update_one(
                        {"course_id": course_id_obj},
                        {
                            "$set": {
                                "modules.$[mod1].position": new_position,
                                "modules.$[mod2].position": current_position
                            }
                        },
                        array_filters=[
                            {"mod1._id": module_id_obj},
                            {"mod2._id": swap_module["_id"]}
                        ]
                    )
                    self.logger.debug(f"[MODULE REPOSITORY] Swapped positions between modules {module_id} and {swap_module['_id']}")
                    return result.modified_count > 0

        # Step 3: No swap, just update fields (excluding position)
        update_fields = {
            f"modules.$.{k}": v for k, v in new_course_data_as_dict.items() if k != "position"
        }

        if update_fields:
            result = self.collection_modules.update_one(
                {"course_id": course_id_obj, "modules._id": module_id_obj},
                {"$set": update_fields}
            )
            self.logger.debug(f"[MODULE REPOSITORY] Updated module {module_id} in course {course_id}: {update_fields}")
            return result.modified_count > 0

        self.logger.debug(f"[MODULE REPOSITORY] No updates made to module {module_id}.")
        return False


    '''def modify_module_in_course(
        self, new_course_data_as_dict, course_id, module_id
    ):
        """
        Modify a module in a course.
        """
        
        ## If we're getting send a new module with different position, we also need to update the position of the other module
        ## Doing a swap, so we get the module to change, the swapped one (if exists) and make the swap.
        
        intended_module_to_change = self.collection_modules.find_one(
            {"course_id": ObjectId(course_id), "modules._id": module_id}
        )
        
        swapped_module_to_change = self.collection_modules.find_one(
            {"course_id": ObjectId(course_id), "modules.position": new_course_data_as_dict["position"]}
        )
        
        
        self.logger.debug(f"[MODULE REPOSITORY] Intended module to change: {intended_module_to_change}")
        self.logger.debug(f"[MODULE REPOSITORY] Swapped module to change: {swapped_module_to_change}")
        # If both are the same module, we don't need to do anything, but if they aren't we need to swap the positions
        # Both modules are the same if they have the same ObjectId as _id.
        
        swap_done = False
        
        # Does the swapped module exist?
        if swapped_module_to_change:
            # Are they the same module?
            # We need to swap the positions for both
            swap_done = True

            (target_position, target_id) = (None, None)
            for module in swapped_module_to_change['modules']:
                if module["_id"] == module_id:
                    target_position = module["position"]
                    target_id = module["_id"]
                    break
        
            if not target_position or not target_id:
                self.logger.debug(f"[MODULE REPOSITORY] Module with ID {module_id} not found in swapped module")
                return False
            
            
            result = self.collection_modules.update_one(
                {"course_id": ObjectId(course_id)},
                {
                    "$set": {
                        "modules.$[mod1].position": target_position,
                        "modules.$[mod2].position": new_course_data_as_dict["position"]
                    }
                },
                array_filters=[
                    {"mod1._id": module_id},
                    {"mod2._id": target_id}
                ]
            )
            self.logger.debug(f"Swapped modules: {result.modified_count} updated")
            return result.modified_count > 0
        else:
            # There is no swap, so we update everything, except the position
            # We need to remove the position from the new_course_data_as_dict
            # We get the position from the intended module to change
            
            self.logger.debug(f"[MODULE REPOSITORY] No swap done, updating module {module_id} in course {course_id}")
            self.logger.debug(f"[MODULE REPOSITORY] New course data: {new_course_data_as_dict}")
            self.collection_modules.update_one(
                {"course_id": ObjectId(course_id), "modules._id": module_id},
                {"$set": {f"modules.$.{k}": v for k, v in new_course_data_as_dict.items()}}
            )
                
        self.logger.debug(
            f"[MODULE REPOSITORY] Modified module {module_id} in course {course_id}"
        )
        self.logger.debug(f"[MODULE REPOSITORY] Swapping done? {swap_done}")'''
        
    def delete_module_from_course(self, course_id, module_id):
        """
        Delete a module from a course.
        Also, we need to decrement the position for all of those modules that are after the deleted one.
        """
        
        # This works because we do the validations check in the service
        module_to_remove = self.get_module_by_id(course_id, module_id)
        
        pos_to_remove = module_to_remove["position"]
        
        result = self.collection_modules.update_one(
            {"course_id": ObjectId(course_id)},
            {"$pull": {"modules": {"_id": module_id}}},
        )
        
        if result.modified_count > 0:
            # We need to decrement the position of those modules that are after the deleted one
            self.collection_modules.update_many(
                {
                    "course_id": ObjectId(course_id),
                    "modules.position": {"$gt": pos_to_remove},
                },
                {"$inc": {"modules.$[elem].position": -1}},
                array_filters=[{"elem.position": {"$gt": pos_to_remove}}],
            )

        self.logger.debug(
            f"[MODULE REPOSITORY] Deleted module {module_id} from course {course_id}"
        )

        return result.modified_count > 0
    
    def get_module_by_id(self, course_id, module_id):
        """
        Get a module by its ID from a course.
        """
        information_from_collection = self.collection_modules.find_one(
            {"course_id": ObjectId(course_id), "modules._id": module_id}
        )
        
        self.logger.debug(f"[MODULE REPOSITORY] Module searched on repository: {information_from_collection}")
        
        if information_from_collection:
            for module in information_from_collection['modules']:
                module_as_dict = Module.from_dict(module).to_dict()
                self.logger.debug(f"[MODULE REPOSITORY] Module check: {module_as_dict}")
                if module_as_dict["_id"] == module_id:
                    self.logger.debug(f"[MODULE REPOSITORY] Module found: {module_as_dict}")
                    return module_as_dict
            
        self.logger.debug(
            f"[MODULE REPOSITORY] Module with ID {module_id} not found in course with ID {course_id}"
        )
        
        return None
        