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
    def __init__(
        self,
        title: str,
        description: str,
        mimetype: str,
        source: str,
        position: int,
        id: str = None,
    ):
        self.id = ObjectId() if id is None else ObjectId(id)
        self.title = title
        self.description = description
        self.mimetype = mimetype
        self.source = source
        self.position = position

    def to_dict(self):
        return {
            "_id": str(self.id),
            "title": self.title,
            "description": self.description,
            "source": self.source,
            "mimetype": self.mimetype,
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
            title=data.get("title"),
            description=data.get("description"),
            mimetype=data.get("mimetype"),
            source=data.get("source"),
            position=data.get("position"),
        )
