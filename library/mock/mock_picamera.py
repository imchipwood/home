
class PiCamera(object):
    def __init__(self, camera_num=0, stereo_mode='none', stereo_decimate=False, resolution=None, framerate=None, sensor_mode=0, led_pin=None, clock_mode='reset', framerate_range=None, **kwargs):
        super(PiCamera, self).__init__()
        self.rotation = 0
        self.brightness = 50
        self.contrast = 10
        self.resolution = [3280, 2464]
        self.iso = 200

    def close(self):
        return

    def stop_preview(self):
        return

    def capture(self, output, format=None, use_video_port=False, resize=None, splitter_port=0, bayer=False, **options):
        return
