import logging
import schedule
from tasks import Task

def run(config):
    task = Task.make(config)
    task.add()

def run_sidecar(config):    
    for definition in config:
        minutes = definition["minutes"]
        task = definition["task"]
        schedule.every(minutes).minutes.do(run, task)
