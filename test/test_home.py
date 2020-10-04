import timeit
from threading import Thread

from library.home import execute

MAX_THREAD_TIMEOUT = 5.0


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
