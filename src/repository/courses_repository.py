import os


class CoursesRepository:
    def __init__(self, database):
        self.collection = database[os.getenv("COURSES_COLLECTION_NAME")]
        
    def create_course(self, course_dict): 
        course_dict["students"] = []
        result = self.collection.insert_one(course_dict)
        return str(result.inserted_id)
    
    def get_course_by_partial_name(self, partial_name):
        cursor = self.collection.find({"name": {"$regex": partial_name, "$options": "i"}})
        return [course for course in cursor]