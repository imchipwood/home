# https://pypi.python.org/pypi/pushbullet.py
import os
from pushbullet import Pushbullet


class PushbulletNotify(Pushbullet):
    def __init__(self, api_key):
        super().__init__(api_key)
        self.result = None

    def send_file(self, file_path):
        file_name = os.path.basename(file_path)
        with open(file_path, 'rb') as pic:
            file_data = self.upload_file(pic, file_name)
        self.result = self.push_file(**file_data)

    def send_text(self, title_text, message_text):
        self.result = self.push_note(title_text, message_text)
