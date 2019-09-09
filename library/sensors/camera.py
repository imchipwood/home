"""
PiCamera "Sensor"
Author: Charles "Chip" Wood
        imchipwood@gmail.com
        github.com/imchipwood
"""

import logging
import time
import os
from library import setup_logging

try:
    from picamera import PiCamera
except:
    logging.warning("Failed to import picamera - using mock")
    from library.mock.mock_picamera import PiCamera


class Camera(PiCamera):
    def __init__(self, config, debug=False):
        """
        @param config: configuration object for PiCamera
        @type config: library.config.camera.CameraConfig
        @param debug: debug flag
        @type debug: bool
        """
        super(Camera, self).__init__()

        self.debug = debug
        self.config = config

        self.logger = setup_logging(
            logging.getLogger(__name__),
            logging_level=self.debug,
            log_path=self.config.log
        )
        self.setup()

    @property
    def capture_delay(self):
        """
        @return: capture delay in seconds
        @rtype: float
        """
        return self.config.delay

    @property
    def capture_path(self):
        """
        @return: where to save image to
        @rtype: str
        """
        return self.config.capture_path

    def setup(self):
        """
        Set up the PiCamera based on settings found in config file
        """
        self.logger.debug("Initializing camera settings from config")
        self.rotation = self.config.rotation
        self.brightness = self.config.brightness
        self.contrast = self.config.contrast
        self.resolution = self.config.resolution

    def capture(self, output=None, format=None, use_video_port=False, resize=None, splitter_port=0, delay=None, **options):
        """
        slight modification on built-in capture function to allow not specifying an output and updating camera ISO
        on the fly based on time of day

        @remark: More info here: http://picamera.readthedocs.io/en/release-1.10/api_camera.html

        @param output: Optional, string path to save image to. Defaults to cameraFile attribute if none provided
        @param format: Optional, format to save image in (jpeg, png, gif, etc.)
        @param use_video_port: Optional, boolean, defaults False. Set to true to use video port instead of camera port if you need rapid capture
        @param resize: Optional, tuple of (width, height) to resize image. defaults to None (no resize)
        @param splitter_port: Optional, boolean, default 0, ignored when use_video_port=False. Defines port of video splitter that image encoder will be attached to
        @param delay: Optional, integer, default None, use to delay the camera picture taking by 'delay' seconds
        @param options: no documentation provided by picamera docs
        """
        # Use capture path from config if one wasn't provided
        if not output:
            output = self.capture_path

        if not os.path.exists(os.path.dirname(output)):
            # Ensure the output directory actually exists
            os.makedirs(os.path.dirname(output))
        elif os.path.exists(output):
            # Delete old file if necessary
            os.remove(output)
        self.logger.debug("Saving image to %s", output)

        # update ISO
        self.logger.debug("Stopping preview")
        self.stop_preview()
        self.logger.debug("Setting ISO")
        self.iso = self.config.iso

        # Handle capture delay
        target_delay = 0
        if delay is not None:
            target_delay = delay
        elif self.capture_delay:
            target_delay = self.capture_delay
        if target_delay > 0:
            self.logger.debug("Delaying %f seconds before capture", target_delay)
            time.sleep(target_delay)

        self.logger.debug("Capturing image...")
        super(Camera, self).capture(
            output=output,
            format=format,
            use_video_port=use_video_port,
            resize=resize,
            splitter_port=splitter_port,
            **options
        )
        os.chmod(output, 0o777)
        self.logger.debug("Capture complete")

    def cleanup(self):
        """
        Gracefully exit
        """
        try:
            self.logger.debug("Disabling camera")
            self.stop_preview()
            self.close()
            self.logger.debug("Camera disabled")
        except:
            self.logger.exception("Exception while shutting down camera")
