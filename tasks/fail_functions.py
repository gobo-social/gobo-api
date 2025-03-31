from models.cursor import LoopCursor

def rollback_cursor(task):
    cursor = task.details.get("cursor")
    if cursor is not None:
        loop = LoopCursor.from_json(cursor)
        loop.rollback()

def run_failure_command(name, task):
    if name == "rollback cursor":
        rollback_cursor(task)
    else:
        raise Exception(f"{name} does not match a known failure function")
