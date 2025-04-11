import os


class CoursesRepository:
    def __init__(self, collection):
        self.collection = collection
        
    def create_course(self, course_dict): 
        course_dict["students"] = []
        course_dict["modules"] = []
        result = self.collection.insert_one(course_dict)
        return str(result.inserted_id)
    
    def update_course(self, course_id, course_dict):
        result = self.collection.update_one({"_id": course_id}, {"$set": course_dict})
        return result.modified_count > 0
    
    def delete_course(self, course_id):
        result = self.collection.delete_one({"_id": course_id})
        return result.deleted_count > 0
    
    def get_course_by_id(self, course_id):
        course = self.collection.find_one({"_id": course_id})
        if course:
            return course
        else:
            return None
    
    def search_course_by_partial_name(self, partial_name):
        courses = self.collection.find({"course_name": {"$regex": partial_name, "$options": "i"}})
        return list(courses)
    
    def get_list_of_students_for_course(self, course_id):
        course = self.get_course_by_id(course_id)
        if course:
            return course.get("students", [])
        else:
            return None
        
    def enroll_student_in_course(self, course_id, student_id):
        result = self.collection.update_one(
            {"_id": course_id},
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
    
    def get_course_owner(self, course_id):
        course = self.get_course_by_id(course_id)
        if course:
            return course.get("creator_id")
        else:
            return None