# https://pypi.python.org/pypi/pushbullet.py
import os

from pushbullet import Pushbullet


class PushBulletNotify(Pushbullet):
    def __init__(self, api_key):
        """
        Initialize PushBulletNotify object
        @param api_key: PushBullet API access key
        @type api_key: str
        """
        super().__init__(api_key)
        self.result = None

    def send_file(self, file_path: str):
        """
        Send file notification
        @param file_path: path to file
        @type file_path: str
        """
        print("PB SEND FILE")
        file_name = os.path.basename(file_path)
        with open(file_path, 'rb') as pic:
            file_data = self.upload_file(pic, file_name)
        self.result = self.push_file(**file_data)

    def send_text(self, title_text: str, message_text: str):
        """
        Send text notification
        @param title_text: title of message
        @type title_text: str
        @param message_text: body of message
        @type message_text: str
        """
        print("PB SEND TEXT")
        self.result = self.push_note(title_text, message_text)
