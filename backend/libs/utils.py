import os
import shutil
import time
import urllib.request
import urllib.parse
import json
import logging
import asyncio

logger = logging.getLogger("uvicorn.error")


def get_config(*args) -> str:
    with open("config.json", "r") as f:
        config = json.load(f)
    for a in args:
        config = config[a]
    return config


BACKEND_BASE_URL = get_config("BACKEND_HOST")


def benchmark(label: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            res = func(*args, **kwargs)
            logger.debug(f"{label} ({time.time()-start:2.2f}s)")
            return res

        async def asyncwrapper(*args, **kwargs):
            start = time.time()
            res = await func(*args, **kwargs)
            logger.debug(f"{label} ({time.time()-start:2.2f}s)")
            return res

        if asyncio.iscoroutinefunction(func):
            return asyncwrapper
        else:
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
            logger.debug(f"Deleted '{file_path}'")
        except Exception as e:
            logger.debug("Failed to delete %s. Reason: %s" % (file_path, e))
    logger.debug("Emptied saved resources")


def pdf_to_url(path: str, page_number: int):
    file_url = urllib.parse.urljoin(
        f"{BACKEND_BASE_URL}/fileserver/", urllib.request.pathname2url(path)
    )
    res = f"{file_url}#page={page_number}"
    # logger.debug(f"{path} and {page_number} -> {res}")
    return res
