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


class Module:
    def __init__(
        self, title, description, position, resources: list = None, id: str = None
    ):
        self.id = ObjectId() if id is None else ObjectId(id)
        self.title = title
        self.description = description
        self.resources = resources if resources else []
        self.position = position
        self.date_created = datetime.now()

    def to_dict(self):
        return {
            "_id": str(self.id),
            "title": self.title,
            "description": self.description,
            "resources": self.resources,
            "position": self.position,
            "date_created": self.date_created,
        }

    def __setattr__(self, name, value):
        if name == "id" and value is not None:
            value = ObjectId(value)
        super().__setattr__(name, value)

    @staticmethod
    def from_dict(data):
        return Module(
            id=data.get("_id"),
            title=data.get("title"),
            description=data.get("description"),
            resources=data.get("resources", []),
            position=data.get("position"),
            type=data.get("type"),
        )
