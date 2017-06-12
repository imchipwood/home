# https://pypi.python.org/pypi/pushbullet.py
from pushbullet import Pushbullet


class PushbulletImageNotify(Pushbullet):
	def __init__(self, apikey, filepath):
		Pushbullet.__init__(self, apikey)
		import os
		filename = os.path.basename(filepath)
		with open(filepath, 'rb') as pic:
			filedata = self.upload_file(pic, filename)
		result = self.push_file(**filedata)
		return


class PushbulletTextNotify(Pushbullet):
	def __init__(self, apikey, titletext, messagetext):
		Pushbullet.__init__(self, apikey)
		result = self.push_note(titletext, messagetext)
		return
