import timeit
from threading import Thread

import pytest

from library import IS_ARM
from library.home import execute

MAX_THREAD_TIMEOUT = 5.0

if not IS_ARM:
    pytestmark = pytest.mark.skip("Not running on raspberry pi, can't use camera")


def test_execute():
    config_path = "pytest_nomqttpushbullet.json"
    stop_threads = False
    thread = Thread(target=execute, args=(config_path, lambda: stop_threads, True))
    thread.start()

    stop_threads = True
    thread.join(timeout=0.1)

    start = timeit.default_timer()
    while thread.is_alive() and timeit.default_timer() - start < MAX_THREAD_TIMEOUT:
        pass

    assert not thread.is_alive()
