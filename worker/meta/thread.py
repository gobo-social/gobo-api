import logging
import threading
import itertools
import gc

# TODO: Consider recovery and dead-letter states.
def fail_task(queue, task, error):
    try:
        if task is None:
            # This should never happen, so it's alarming if it does.
            logging.error("exception in task processing, but no task defined")
            return
        
        logging.error(f"failure in {queue.name} {task.name}")
        logging.error(error, exc_info=True)
        task.failure()
        task.remove()
    

    # This is the failsafe designed to catch any issues with the above, more
    # sophisticated error handling and keeps the thread alive for next task.
    # It's like a 500-class HTTP error, so it should ideally not get here.
    # Because the first priority is to keep the thread alive, this handler
    # needs to be guaranteed to always resolve without another exception.
    except Exception as abject:
        logging.error("abject thread failure")
        logging.error(abject, exc_info=True)



# Will return True every N invocations, can be used indefinitely.
shouldCollect = itertools.cycle([False] * 49 + [True])

def thread_core(queue, dispatch):
    while True:
        task = queue.get()
        try:
            task.start(queue)
            result = dispatch(task)
            task.finish(queue)
            task.next(result)
            task.remove()
        except Exception as e:
            fail_task(queue, task, e)
        finally:
            queue.task_done()
            del task
            if next(shouldCollect):
                gc.collect()
 

# We weave Python's thread and queue features to spread our workload while
# keeping track of pending tasks, sorted by priority.
class Thread():
    def __init__(self, queue, dispatch):  
        self.thread = threading.Thread(
            target = thread_core,
            args = (queue, dispatch)
        )
        
    @staticmethod
    def make(data):
        return Thread(
            queue = data["queue"],
            dispatch = data["dispatch"],
        )

    def start(self):
        self.thread.start()
