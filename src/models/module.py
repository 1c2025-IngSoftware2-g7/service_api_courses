from datetime import datetime

from bson import ObjectId


class Module:
    def __init__(self, title, description, url, type, id: str = None):
        self.id = ObjectId() if id is None else ObjectId(id)
        self.title = title
        self.description = description
        self.url = url
        self.type = type  # mp4? pdf?
        self.date_created = datetime.now()

    def to_dict(self):
        return {
            "_id": str(self.id),
            "title": self.title,
            "description": self.description,
            "url": self.url,
            "type": self.type,
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
            url=data.get("url"),
            type=data.get("type"),
        )
