import os
from bson import ObjectId
from models.course import Course

class CoursesRepository:
    def __init__(self, collection, logger):
        self.collection = collection
        self.logger = logger
        
    def create_course(self, course_dict): 
        course_dict["students"] = []
        course_dict["modules"] = []
        result = self.collection.insert_one(course_dict)
        return str(result.inserted_id)
    
    def update_course(self, course_id, course_dict):
        result = self.collection.update_one({"_id": ObjectId(course_id)}, {"$set": course_dict})
        return result.modified_count > 0
    
    def delete_course(self, course_id):
        result = self.collection.delete_one({"_id": ObjectId(course_id)})
        return result.deleted_count > 0
    
    def get_course_by_id(self, course_id):
        object_id = ObjectId(course_id)
        self.logger.debug(f"[DEBUG] course_id: {course_id} - object_id: {object_id}")
        course = self.collection.find_one({"_id": object_id})
        
        self.logger.debug(f"[DEBUG] course searched on repository: {course}")
        
        # we convert the course to a Course instance
        if course:
            return course
        else:
            return None
    
    def search_course_by_partial_information(self, string_to_find):
        # We need to search in the course name and description
        # We need to use regex to find the string in the name and description
        regex = {"$regex": string_to_find, "$options": "i"}
        courses = self.collection.find({
            "$or": [
                {"name": regex},
                {"description": regex}
            ]
        })
        
        self.logger.debug(f"[DEBUG] courses searched on repository: {courses}")
        return list(courses)
    
    
    def get_list_of_students_for_course(self, course_id):
        course = self.get_course_by_id(course_id)
        if course:
            return course.get("students", [])
        else:
            return None
        
    def enroll_student_in_course(self, course_id, student_id):
        result = self.collection.update_one(
            {"_id": ObjectId(course_id)},
            {"$addToSet": {"students": student_id}}
        )
        return result.modified_count > 0
    
    def remove_student_from_course(self, course_id, student_id):
        result = self.collection.update_one(
            {"_id": course_id},
            {"$pull": {"students": student_id}}
        )
        return result.modified_count > 0
    
    """ This method is used to find all courses that a student is enrolled in. """
    def find_by_student_id(self, student_id):
        courses = self.collection.find({"students": student_id})
        return list(courses)
    
    """ This method is used to find all courses that a student is enrolled in. """
    def get_course_owner(self, course_id):
        course = self.get_course_by_id(course_id)
        if course:
            return course.get("creator_id")
        else:
            return None
    
    """ This method is used to know if a player is already enrolled in a course. """
    def is_student_enrolled_in_course(self, course_id, student_id):
        course = self.get_course_by_id(course_id)
        if course:
            return student_id in course.get("students", [])
        else:
            return False
        
    def get_all_courses(self):
        courses = self.collection.find()
        return list(courses)
    
    def get_enrolled_courses(self, student_id):
        courses = self.collection.find({"students": student_id})
        return list(courses)
    
    def course_still_have_slots(self, course_id):
        course = self.get_course_by_id(course_id)
        if course:
            return len(course.get("students", [])) < course.get("max_students", 0)
        else:
            return False
        
    def add_module_to_course(self, course_id, module):
        result = self.collection.update_one(
            {"_id": ObjectId(course_id)},
            {"$addToSet": {"resources": module}}
        )
        return result.modified_count > 0