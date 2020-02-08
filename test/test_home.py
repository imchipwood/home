from time import time
from threading import Thread

from library.home import execute


def test_execute():
    config_path = "pytest_nomqttpushbullet.json"
    stop_threads = False
    thread = Thread(target=execute, args=(config_path, lambda: stop_threads, True))
    thread.start()
    stop_threads = True
    thread.join(timeout=0.1)
    start = time()
    while time() - start < 5 and thread.isAlive():
        pass
    # thread.terminate()
    assert not thread.isAlive()
