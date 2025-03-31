import logging
import queue
import itertools
import joy
import jobs
from tasks import Task
from . import Thread

class Queue():
    def __init__(self, name):
        self.name = name
        self.queue = queue.PriorityQueue()

    @staticmethod
    def make(data):
        return Queue(
            name = data["name"],
        )

    def put(self, task):
        self.queue.put(task)

    def get(self):
        return self.queue.get()

    def task_done(self):
        return self.queue.task_done()


class Node():
    def __init__(self, channel, name, queue, thread, shard):
        self.channel = channel
        self.name = name
        self.shard = shard
        self.queue = queue
        self.thread = thread

    @staticmethod
    def make(data):
        queue = data["queue"]
        
        thread = Thread.make({
            "queue": queue,
            "dispatch": getattr(jobs, data["channel"]).dispatch
        })

        return Node(
            name = data["name"],
            channel = data["channel"],
            shard = data.get("shard"),
            queue = queue,
            thread = thread,
        )

    def start(self):
        self.thread.start()

    def enqueue(self, task):
        self.queue.put(task)



class NodeArray():
    def __init__(self, nodes):
        self.nodes = nodes
    
    def start(self):
        for node in self.nodes:
            node.start()

class ShardedNodeArray(NodeArray):
    @staticmethod
    def make(data):
        array = ShardedNodeArray(nodes = data["nodes"])
        array.table = {}
        for node in array.nodes:
            array.table[str(node.shard)] = node
        return array

    def enqueue(self, tasks):
        for data in tasks:
            task = Task.make(data)
            node = self.table[str(task.shard)]
            node.enqueue(task)

class RoundRobinNodeArray(NodeArray):
    @staticmethod
    def make(data):
        return RoundRobinNodeArray(nodes = data["nodes"])

    def enqueue(self, tasks):
        for data in tasks:
            task = Task.make(data)
            node = self.nodes[0]
            node.enqueue(task)