from datetime import datetime

from bson import ObjectId

""" Module 
    Title
    Description
    order: (Index position?)
    resources: []
    
    
    Resource
        source: url/text or whatever
"""


class Resource:
    def __init__(self, source: str, position: int, id: str = None):
        self.id = ObjectId() if id is None else ObjectId(id)
        self.source = source
        self.position = position

    def to_dict(self):
        return {
            "_id": str(self.id),
            "source": self.source,
            "position": self.position,
        }

    def __setattr__(self, name, value):
        if name == "_id" and value is not None:
            value = ObjectId(value)

        super().__setattr__(name, value)

    @staticmethod
    def from_dict(data):
        return Resource(
            id=data.get("_id"),
            source=data.get("source"),
            position=data.get("position"),
        )
