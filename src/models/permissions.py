class AssistantPermissions:
    def __init__(self, from_dict=None):

        self.permissions = (
            from_dict
            if from_dict
            else {
                "ModulesAndResources": False,
                "Exams": False,
                "Tasks": False,
                "Feedbacks": False,
            }
        )
        """self.permissions = {
            "ModulesAndResources": False,
            "Exams": False,
            "Tasks": False,
            "Feedbacks": False,
        }"""

    def contains_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def set_permission(self, permission: str, value: bool):
        if permission in self.permissions:
            self.permissions[permission] = value
        else:
            raise ValueError(f"Invalid permission: {permission}")

    def get_permission(self, permission: str) -> bool:
        return self.permissions.get(permission, False)

    def __to_dict__(self):
        return self.permissions
