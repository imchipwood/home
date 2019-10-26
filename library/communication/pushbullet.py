# https://pypi.python.org/pypi/pushbullet.py
import os
from pushbullet import Pushbullet


class PushbulletImageNotify(Pushbullet):
	def __init__(self, api_key, file_path):
		super().__init__(api_key)
		file_name = os.path.basename(file_path)
		with open(file_path, 'rb') as pic:
			file_data = self.upload_file(pic, file_name)
		self.result = self.push_file(**file_data)
		

class PushbulletTextNotify(Pushbullet):
	def __init__(self, api_key, title_text, message_text):
		super().__init__(api_key)
		self.result = self.push_note(title_text, message_text)
