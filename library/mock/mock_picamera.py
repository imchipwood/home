class PiCamera:
    def __init__(self):
        self.rotation = 0
        self.brightness = 50
        self.contrast = 10
        self.resolution = [3280, 2464]
        self.iso = 200

    def close(self):
        return

    def stop_preview(self):
        return

    def start_preview(self):
        return

    def capture(self, output, format=None, use_video_port=False, resize=None, splitter_port=0, bayer=False, **options):
        with open(output, 'w') as oup:
            oup.write("HI\n")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return
