import json
import os

from telegram import User


class UserModel:
    def __init__(self, user_id, data_dir: str):
        self.folder = f"{data_dir}/{user_id}"
        self.user_info_file = f"{self.folder}/user_info.json"

    def create_folder(self):
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)

    def save_user_info(self, user: User):
        fields = {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "language_code": user.language_code,
            "is_bot": user.is_bot,
            "is_premium": user.is_premium,
        }

        self.create_folder()
        with open(self.user_info_file, "w") as file:
            file.write(json.dumps(fields))
