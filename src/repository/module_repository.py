from bson import ObjectId
from src.models.module import Module
from src.models.resource import Resource


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
            self.logger.debug(
                f"[MODULE REPOSITORY] Course with ID: {course_id} not found"
            )
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

        """result = self.collection_modules.update_one(
            {"course_id": ObjectId(course_id)},
            {"$addToSet": {"modules": module_as_dict}},
        )"""

        self.logger.debug(
            f"[MODULE REPOSITORY] Add module {module} to course {course_id}"
        )
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
            self.logger.debug(
                f"[MODULE REPOSITORY] Module {module_id} not found in course {course_id}"
            )
            return False

        # Extract current position of the module to be modified
        current_module = next(
            (mod for mod in course_doc["modules"] if mod["_id"] == module_id_obj), None
        )
        if not current_module:
            self.logger.debug(
                f"[MODULE REPOSITORY] Module with ID {module_id} not found in course document."
            )
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
                    (
                        mod
                        for mod in swap_course_doc["modules"]
                        if mod["position"] == new_position
                    ),
                    None,
                )

                if swap_module and swap_module["_id"] != module_id_obj:
                    # Perform atomic swap using array filters
                    result = self.collection_modules.update_one(
                        {"course_id": course_id_obj},
                        {
                            "$set": {
                                "modules.$[mod1].position": new_position,
                                "modules.$[mod2].position": current_position,
                            }
                        },
                        array_filters=[
                            {"mod1._id": module_id_obj},
                            {"mod2._id": swap_module["_id"]},
                        ],
                    )
                    self.logger.debug(
                        f"[MODULE REPOSITORY] Swapped positions between modules {module_id} and {swap_module['_id']}"
                    )
                    return result.modified_count > 0

        # Step 3: No swap, just update fields (excluding position)
        update_fields = {
            f"modules.$.{k}": v
            for k, v in new_course_data_as_dict.items()
            if k != "position"
        }

        if update_fields:
            result = self.collection_modules.update_one(
                {"course_id": course_id_obj, "modules._id": module_id_obj},
                {"$set": update_fields},
            )
            self.logger.debug(
                f"[MODULE REPOSITORY] Updated module {module_id} in course {course_id}: {update_fields}"
            )
            return result.modified_count > 0

        self.logger.debug(f"[MODULE REPOSITORY] No updates made to module {module_id}.")
        return False

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

        self.logger.debug(
            f"[MODULE REPOSITORY] Module searched on repository: {information_from_collection}"
        )

        if information_from_collection:
            for module in information_from_collection["modules"]:
                module_as_dict = Module.from_dict(module).to_dict()
                self.logger.debug(f"[MODULE REPOSITORY] Module check: {module_as_dict}")
                if module_as_dict["_id"] == module_id:
                    self.logger.debug(
                        f"[MODULE REPOSITORY] Module found: {module_as_dict}"
                    )
                    return module_as_dict

        self.logger.debug(
            f"[MODULE REPOSITORY] Module with ID {module_id} not found in course with ID {course_id}"
        )

        return None

    def get_resources_from_module(self, course_id, module_id):
        """
        Get all resources from a specific module in a course.
        """
        pipeline = [
            {"$match": {"course_id": ObjectId(course_id)}},
            {"$unwind": "$modules"},
            {"$match": {"modules._id": module_id}},
            {"$project": {"resources": "$modules.resources"}},
        ]

        result = list(self.collection_modules.aggregate(pipeline))

        if result:
            # Flat everything under the resources key
            # Then get the resources list and return it
            resources = result[0].get("resources", [])

            return [Resource.from_dict(res).to_dict() for res in resources]

        self.logger.debug(
            f"[MODULE REPOSITORY] Module with ID {module_id} not found in course with ID {course_id}"
        )
        return None

    def get_resource_from_module(self, course_id, module_id, resource_id):
        """
        Get a resource by its ID from a module in a course.
        """
        pipeline = [
            {"$match": {"course_id": ObjectId(course_id)}},
            {"$unwind": "$modules"},
            {"$match": {"modules._id": module_id}},
            {"$unwind": "$modules.resources"},
            {"$match": {"modules.resources._id": resource_id}},
            {"$project": {"resource": "$modules.resources"}},
        ]

        result = list(self.collection_modules.aggregate(pipeline))

        if result:
            resource = result[0].get("resource", {})
            return Resource.from_dict(resource).to_dict()

        self.logger.debug(
            f"[MODULE REPOSITORY] Resource with ID {resource_id} not found in module with ID {module_id} in course with ID {course_id}"
        )
        return None

    def add_resource_to_module(self, course_id, module_id, resource_dict):
        """
        Add a resource to a module.
        """

        result = self.collection_modules.update_one(
            {"course_id": ObjectId(course_id), "modules._id": module_id},
            {"$addToSet": {"modules.$.resources": resource_dict}},
        )

        if result.modified_count > 0:
            self.logger.debug(
                f"[MODULE REPOSITORY] Resource {resource_dict} added to module {module_id}"
            )
            return result.modified_count > 0
        else:
            self.logger.debug(
                f"[MODULE REPOSITORY] Failed to add resource {resource_dict} to module {module_id}"
            )
            return False

    def delete_resource_from_module(self, course_id, module_id, resource_id):
        """
        Delete a resource from a module.
        """

        # We need to get the position of the resource, delete it and update the positions of the rest
        resource_to_remove = self.get_resource_from_module(
            course_id, module_id, resource_id
        )
        position_removed_resource = resource_to_remove["position"]

        result = self.collection_modules.update_one(
            {"course_id": ObjectId(course_id), "modules._id": module_id},
            {"$pull": {"modules.$.resources": {"_id": resource_id}}},
        )

        if result.modified_count > 0:
            # We need to decrement the position of those resources that are after the deleted one
            self.collection_modules.update_many(
                {
                    "course_id": ObjectId(course_id),
                    "modules._id": module_id,
                    "modules.resources.position": {"$gt": position_removed_resource},
                },
                {"$inc": {"modules.$[elem].resources.$[res].position": -1}},
                array_filters=[
                    {"elem._id": module_id},
                    {"res.position": {"$gt": position_removed_resource}},
                ],
            )

            self.logger.debug(
                f"[MODULE REPOSITORY] Resource {resource_id} deleted from module {module_id}"
            )
            return result.modified_count > 0
        else:
            self.logger.debug(
                f"[MODULE REPOSITORY] Failed to delete resource {resource_id} from module {module_id}"
            )
            return False
