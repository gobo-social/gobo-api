import time
import models

# Make sure we wait until we have a stable connection to the database.
def safe_start():
    while True:
        try:
            result = models.task.get("foo")
            break
        except Exception as e:
            time.sleep(1)