import logging
from os import environ
import time
import schedule
import models

FLAG_LATENCY = int(environ.get("FLAG_LATENCY", 60))

class Channel():
    def __init__(self, channel):
        self.id = channel["id"]
        self.name = channel["name"]
        self.shards = channel["shards"]
        self.sidecar = channel["sidecar"]
        self.processing = channel["processing"]

    @staticmethod
    def make():
        channel = models.channel.claim()
        if channel is not None:
            logging.info(f"Worker node claimed {channel["name"]}")
            return Channel(channel)
        else:
            return None
    
    def watch(self):
        while True:
            channel = models.channel.get(self.id) or {"processing": False}
            self.processing = channel["processing"]
            time.sleep(FLAG_LATENCY)

    def start(self, node_array):
        node_array.start()
        while True:
            if self.processing != True:
                time.sleep(5)
                continue
            
            schedule.run_pending()
            tasks = self.receive(10)
            if tasks:
                node_array.enqueue(tasks)
            else:
                time.sleep(2)
    
    def receive(self, limit):
        return models.task.receive(self, limit)

