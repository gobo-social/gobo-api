import logging
import joy
import models
from . import run_failure_command, shard_task


class Task():
    def __init__(self, id, channel, shard, name, priority, details, tries, flow, failure):
        self.id = id
        self.channel = channel
        self.shard = shard
        self.name = name
        self.priority = priority
        self.details = details
        self.tries = tries
        self.flow = flow
        self.fail_function = failure
        self.reset_tracking()
        self.is_halted = False
        if self.shard is None:
            self.shard = shard_task(self)
        

    def __repr__(self): 
        details = {}
        for key, value in self.details.items():
            details[key] = value

        return str({
            "id": self.id,
            "name": self.name,
            "priority": self.priority,
            "tries": self.tries,
            "created": self.created,
            "updated": self.updated,
        })
    
    def __str__(self): 
        return self.__repr__()
    
    def __lt__(self, task):
        return self.priority < task.priority
    
    def to_dict(self):
        return {
            "id": self.id,
            "channel": self.channel,
            "shard": self.shard,
            "name": self.name,
            "priority": self.priority,
            "details": self.details,
            "tries": self.tries,
            "flow": self.flow,
            "failure": self.fail_function,
            "created": self.created,
            "updated": self.updated,
        }

    # TODO: This helper is nice for building new tasks, but we need to sit down
    #       and think about pass by reference issues with [] and {} being falsey.
    @staticmethod
    def make(data):
        return Task(
            id = data.get("id") or joy.crypto.address(),
            channel = data.get("channel") or "default",
            shard = data.get("shard", None),
            name = data["name"],
            priority = data.get("priority") or 10,
            details = data.get("details") or {},
            tries = data.get("tries") or 0,
            flow = data.get("flow") or [],
            failure = data.get("failure", None),
        )
    
    @staticmethod
    def send(channel, name, details = None, priority = 10):
        task = Task.make({
            "channel": channel,
            "name": name,
            "details": details,
            "priority": priority,
        })
        task.add()

    @staticmethod
    def send_flow(flow, priority = None, failure = None):
        task = Task.make({
            "name": "start flow",
            "priority": priority,
            "flow": flow,
            "failure": failure,
        })
        task.next()

    @staticmethod
    def send_copy(task, new_details = {}, priority = None):
        task = Task.make({
            "channel": task.channel,
            "name": task.name,
            "details": new_details.update(task.details),
            "priority": priority or task.priority,
            # TODO: add flow here?
        })
        task.add()

    def start(self, queue):
        created = joy.time.convert("iso", "date", self.created)
        logging.info(f"starting {queue.name} {self.name} {self.id} latency: {joy.time.latency(created)}")
        self.start_time = joy.time.nowdate()

    def finish(self, queue):
        duration = joy.time.nowdate() - self.start_time
        logging.info(f"finished {queue.name} {self.name} {self.id} duration: {duration}")
            

    def update(self, data):
        for key, value in data.items():
            self.details[key] = value
        self.updated = joy.time.now()

    def add(self):
        return models.task.add(self.to_dict())

    def remove(self):
        models.task.remove(self.id)

    def upsert(self):
        return models.task.upsert(self.to_dict())

    def reset_tracking(self):
        now = joy.time.now()
        self.visible = True
        self.created = now
        self.updated = now

    def halt(self):
        self.is_halted = True

    def failure(self):
        if self.fail_function is not None:
            run_failure_command(self.fail_function, self)

    def next(self, result = None):
        if self.is_halted == True:
            return
        if not self.flow:
            return
        
        result = result or {}
        next = self.flow.pop(0)
        details = self.details.copy()

        details.update(result)
        details.update(next.get("details") or {})

        newTask = Task.make({
            "channel": next.get("channel"),
            "name": next["name"],
            "priority": next.get("priority") or self.priority,
            "details": details,
            "flow": self.flow,
            "failure": next.get("failure") or self.fail_function,
        })
      
        newTask.add()
