from datetime import datetime


class Module:
    def __init__(self, title, description, url, type):
        self.title = title
        self.description = description
        self.url = url
        self.type = type  # mp4? pdf?
        self.date_created = datetime.now()

    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "url": self.url,
            "type": self.type,
            "date_created": self.date_created,
        }

    @staticmethod
    def from_dict(data):
        return Module(
            title=data.get("title"),
            description=data.get("description"),
            url=data.get("url"),
            type=data.get("type"),
        )
