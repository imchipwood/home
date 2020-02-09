import os

from pushbullet.filetype import get_file_type

from library import TEST_CONFIG_DIR
from library.communication.pushbullet import PushbulletNotify
from library.config import ConfigurationHandler, SENSORCLASSES
from library.config.pushbullet import PushbulletConfig

CONFIG_PATH = "pytest.json"
CONFIGURATION_HANDLER = ConfigurationHandler(CONFIG_PATH, debug=True)


def mock_push_note(title_text, message_text):
    print(f"PUSH_NOTE: {title_text}: {message_text}")
    return {"type": "note", "title": title_text, "body": message_text}


def mock_push_file(file_name, file_url, file_type, body=None, title=None, device=None, chat=None, email=None,
                   channel=None):
    print(f"PUSH_FILE: {file_name}: {file_type}")
    return {"type": "file", "file_type": file_type, "file_url": file_url, "file_name": file_name}


def mock_upload_file(f, file_name, file_type=None):
    if not file_type:
        file_type = get_file_type(f, file_name)
    print(f"UPLOAD_FILE: {file_name}: {file_type}")
    return {"file_type": file_type, "file_url": "http://some.fake/url", "file_name": file_name}


class Test_PushbulletCommunication:
    def test_pushbullet(self, monkeypatch):
        config = CONFIGURATION_HANDLER.get_sensor_config(SENSORCLASSES.PUSHBULLET)  # type: PushbulletConfig
        pb = PushbulletNotify(config.api_key)

        monkeypatch.setattr(pb, "push_note", mock_push_note)
        monkeypatch.setattr(pb, "push_file", mock_push_file)
        monkeypatch.setattr(pb, "upload_file", mock_upload_file)

        file_path = os.path.join(TEST_CONFIG_DIR, "pytest_mqtt.json")
        pb.send_file(file_path)
        pb.send_text("test title", "test message")
