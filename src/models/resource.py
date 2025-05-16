from datetime import datetime

from bson import ObjectId

''' Module 
    Title
    Description
    order: (Index position?)
    resources: []
    
    
    Resource
        source: url/text or whatever
'''
class Resource:
    def __init__(self, source: str, id: str = None):
        self.id = ObjectId() if id is None else ObjectId(id)
        self.source = source
        self.date_created = datetime.now()

    def to_dict(self):
        return {
            "_id": str(self.id),
            "source": self.source,
            "date_created": self.date_created,
        }

    def __setattr__(self, name, value):
        if name == "id" and value is not None:
            value = ObjectId(value)
        super().__setattr__(name, value)

    @staticmethod
    def from_dict(data):
        return Resource(
            id=data.get("_id"),
            source=data.get("source"),
            type=data.get("type"),
        )
