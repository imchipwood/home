import os
from pushbullet import Pushbullet


class PushbulletImageNotify(Pushbullet):
	def __init__(self, apikey, filepath):
		Pushbullet.__init__(self, apikey)
		filename = os.path.basename(filepath)
		with open(filepath, 'rb') as pic:
			filedata = self.upload_file(pic, filename)
		result = self.push_file(**filedata)
		return