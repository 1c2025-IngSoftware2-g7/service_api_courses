from flask import Blueprint, request
from services import service_modules, logger
from error.error import error_generator
from src.headers import MISSING_FIELDS


modules_bp = Blueprint("modules", __name__, url_prefix="/courses")


@modules_bp.get("/<string:course_id>/modules")
def get_modules_from_course(course_id=None):
    """
    Get all modules from a course.
    """

    if not course_id:
        error = error_generator(
            MISSING_FIELDS, "Course ID is required", 400, "get_modules_from_course"
        )
        return error["response"], error["code_status"]

    logger.debug(f"[APP] Getting modules from course with ID: {course_id}")

    # Call the service to get the modules
    result = service_modules.get_modules_from_course(course_id)

    return result["response"], result["code_status"]


@modules_bp.get("/<string:course_id>/modules/<string:module_id>")
def get_module_from_course(course_id=None, module_id=None):
    """
    Get a module from a course.
    """

    if not course_id:
        error = error_generator(
            MISSING_FIELDS, "Course ID is required", 400, "get_module_from_course"
        )
        return error["response"], error["code_status"]

    if not module_id:
        error = error_generator(
            MISSING_FIELDS, "Module ID is required", 400, "get_module_from_course"
        )
        return error["response"], error["code_status"]

    logger.debug(
        f"[APP] Getting module with ID: {module_id} from course with ID: {course_id}"
    )

    # Call the service to get the module
    result = service_modules.get_module_from_course(course_id, module_id)

    return result["response"], result["code_status"]


# This method is for adding a module to a course
@modules_bp.post("/<string:course_id>/modules")
def add_module(course_id=None):
    """
    Add a module to a course.
    Module comes as a json with
    title = title
    description = description
    id_creator = id of the attempt creator
    """

    if not course_id:
        error = error_generator(
            MISSING_FIELDS, "Course ID is required", 400, "add_module"
        )
        return error["response"], error["code_status"]

    # Get data from request
    data = request.json

    owner_id = data.get("id_creator", None)

    logger.debug(f"[APP] Adding module to course with ID: {course_id} and data: {data}")

    # Call the service to add the module
    result = service_modules.add_module_to_course(course_id, data, owner_id)

    return result["response"], result["code_status"]


# Lets add a modification id
@modules_bp.put("/<string:course_id>/modules/<string:module_id>")
def modify_module(course_id=None, module_id=None):
    """
    Modify a module in a course.
    Module comes as a json with
    title = title
    description = description
    url = url
    type = type
    """

    if not course_id:
        error = error_generator(
            MISSING_FIELDS, "Course ID is required", 400, "modify_module"
        )
        return error["response"], error["code_status"]

    if not module_id:
        error = error_generator(
            MISSING_FIELDS, "Module ID is required", 400, "modify_module"
        )
        return error["response"], error["code_status"]

    # Get data from request
    data = request.json

    owner_id = data.get("modifier_id", None)

    if not owner_id:
        error = error_generator(
            MISSING_FIELDS, "Owner ID is required (modifier_id)", 400, "modify_module"
        )
        return error["response"], error["code_status"]

    """
    Modify a module in a course.
    Module comes as a json with
    title = title
    description = description
    position = position 
    """

    logger.debug(
        f"[APP] Modifying module with ID: {module_id} in course with ID: {course_id} and data: {data}"
    )
    # Call the service to modify the module
    result = service_modules.modify_module_in_course(
        course_id, module_id, owner_id, data
    )

    return result["response"], result["code_status"]


@modules_bp.delete("/<string:course_id>/modules/<string:module_id>/<string:owner_id>")
def delete_module_from_course(course_id=None, module_id=None, owner_id=None):
    """
    Delete a module from a course.
    Module comes as a json with
    title = title
    description = description
    url = url
    type = type
    """

    if not course_id:
        error = error_generator(
            MISSING_FIELDS, "Course ID is required", 400, "delete_module"
        )
        return error["response"], error["code_status"]

    if not module_id:
        error = error_generator(
            MISSING_FIELDS, "Module ID is required", 400, "delete_module"
        )
        return error["response"], error["code_status"]

    if not owner_id:
        error = error_generator(
            MISSING_FIELDS, "Owner ID is required", 400, "delete_module"
        )
        return error["response"], error["code_status"]

    logger.debug(
        f"[APP] Deleting module with ID: {module_id} in course with ID: {course_id}"
    )
    # Call the service to delete the module
    result = service_modules.delete_module_from_course(course_id, module_id, owner_id)

    return result["response"], result["code_status"]


############################
# This is for the resources
############################

resources_bp = Blueprint("resources", __name__, url_prefix="/courses")


@resources_bp.get("/<string:course_id>/modules/<string:module_id>/resources")
def get_resources_from_module(course_id=None, module_id=None):
    """
    Get all resources from a module.
    """

    if not course_id:
        error = error_generator(
            MISSING_FIELDS, "Course ID is required", 400, "get_resources_from_module"
        )
        return error["response"], error["code_status"]

    if not module_id:
        error = error_generator(
            MISSING_FIELDS, "Module ID is required", 400, "get_resources_from_module"
        )
        return error["response"], error["code_status"]

    logger.debug(
        f"[APP] Getting resources from module with ID: {module_id} in course with ID: {course_id}"
    )

    # Call the service to get the resources
    result = service_modules.get_resources_from_module(course_id, module_id)

    return result["response"], result["code_status"]


@resources_bp.get(
    "/<string:course_id>/modules/<string:module_id>/resources/<string:resource_id>"
)
def get_resource_from_module(course_id=None, module_id=None, resource_id=None):
    """
    Get a resource from a module.
    """

    if not course_id:
        error = error_generator(
            MISSING_FIELDS, "Course ID is required", 400, "get_resource_from_module"
        )
        return error["response"], error["code_status"]

    if not module_id:
        error = error_generator(
            MISSING_FIELDS, "Module ID is required", 400, "get_resource_from_module"
        )
        return error["response"], error["code_status"]

    if not resource_id:
        error = error_generator(
            MISSING_FIELDS, "Resource ID is required", 400, "get_resource_from_module"
        )
        return error["response"], error["code_status"]

    logger.debug(
        f"[APP] Getting resource with ID: {resource_id} in module with ID: {module_id} in course with ID: {course_id}"
    )

    # Call the service to get the resource
    result = service_modules.get_resource_from_module(course_id, module_id, resource_id)

    return result["response"], result["code_status"]


@resources_bp.post("/<string:course_id>/modules/<string:module_id>/resources")
def add_resource(course_id=None, module_id=None):
    """
    Add a resource to a module.
    Resource comes as a json with
    source = url/text or whatever
    id_creator = id of the attempt creator
    """

    if not course_id:
        error = error_generator(
            MISSING_FIELDS, "Course ID is required", 400, "add_resource"
        )
        return error["response"], error["code_status"]

    if not module_id:
        error = error_generator(
            MISSING_FIELDS, "Module ID is required", 400, "add_resource"
        )
        return error["response"], error["code_status"]

    # Get data from request
    data = request.json

    owner_id = data.get("id_creator", None)

    if not owner_id:
        error = error_generator(
            MISSING_FIELDS, "Owner ID is required (id_creator)", 400, "add_resource"
        )
        return error["response"], error["code_status"]

    logger.debug(
        f"[APP] Adding resource to module with ID: {module_id} in course with ID: {course_id} and data: {data}"
    )

    # Call the service to add the resource
    result = service_modules.add_resource_to_module(
        course_id, module_id, data, owner_id
    )

    return result["response"], result["code_status"]


@resources_bp.delete(
    "/<string:course_id>/modules/<string:module_id>/resources/<string:resource_id>/<string:owner_id>"
)
def delete_resource_from_module(
    course_id=None, module_id=None, resource_id=None, owner_id=None
):
    """
    Delete a resource from a module.
    """

    if not course_id:
        error = error_generator(
            MISSING_FIELDS, "Course ID is required", 400, "delete_resource"
        )
        return error["response"], error["code_status"]

    if not module_id:
        error = error_generator(
            MISSING_FIELDS, "Module ID is required", 400, "delete_resource"
        )
        return error["response"], error["code_status"]

    if not resource_id:
        error = error_generator(
            MISSING_FIELDS, "Resource ID is required", 400, "delete_resource"
        )
        return error["response"], error["code_status"]

    if not owner_id:
        error = error_generator(
            MISSING_FIELDS, "Owner ID is required", 400, "delete_resource"
        )
        return error["response"], error["code_status"]

    logger.debug(
        f"[APP] Deleting resource with ID: {resource_id} in module with ID: {module_id} in course with ID: {course_id}"
    )

    # Call the service to delete the resource
    result = service_modules.delete_resource_from_module(
        course_id, module_id, resource_id, owner_id
    )

    return result["response"], result["code_status"]
