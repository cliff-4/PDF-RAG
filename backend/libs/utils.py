import os
import shutil
import time
import urllib.request
import urllib.parse
import json


def get_config(*args) -> str:
    with open("config.json", "r") as f:
        config = json.load(f)
    for a in args:
        config = config[a]
    return config


BACKEND_BASE_URL = get_config("ai", "embed", "base_url")


def benchmark(label: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            res = func(*args, **kwargs)
            print(label, f"({time.perf_counter()-start:.1f}s)")
            return res

        return wrapper

    return decorator


@benchmark("Cleared resources")
def empty_folder(folder: str):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
            print(f"Deleted '{file_path}'")
        except Exception as e:
            print("Failed to delete %s. Reason: %s" % (file_path, e))


def pdf_to_url(path: str, page_number: int):
    file_url = urllib.parse.urljoin(
        BACKEND_BASE_URL, "fileserver/", urllib.request.pathname2url(path)
    )
    res = f"{file_url}#page={page_number}"
    print(f"{path} and {page_number} -> {res}")
    return res
