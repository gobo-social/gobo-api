# Load configuration
from dotenv import load_dotenv
load_dotenv()


# Configure GOBO logging
from logging import config
import logging
config.dictConfig({
    "version": 1,
    "formatters": {"default": {
      "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    }},
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "default"
        },
        "main_trace": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "gobo.log",
            "formatter": "default",
            "maxBytes": 10000000, # 10 MB
            "backupCount": 1
        },
        "error_trace": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "gobo-error.log",
            "level": "WARN",
            "formatter": "default",
            "maxBytes": 10000000, # 10 MB
            "backupCount": 10
        }
    },
   "root": {
        "level": "INFO",
        "handlers": ["stdout", "main_trace", "error_trace"]
    }
})


# Establish worker queues and threads that drive its work.
import threading
import joy
from meta import safe_start, run_sidecar
from meta import Queue, Channel, Node, ShardedNodeArray, RoundRobinNodeArray


# Make sure it's safe to connect to the database.
safe_start()

channel = Channel.make()
if channel is None:
   logging.info("This worker was unable to find a channel registration")
   quit()

# The watcher will poll the channel registry and look for changes to the
# channel configuration. Right now, it's focused on the paused flag.
watcher = threading.Thread(target = channel.watch)
watcher.start()

# For the default channel, all listening nodes are working off the same
# priority queue, spreading the load, and taking up work as soon as they can.
# channel::start will continue until process ends.
if channel.name == "default":
    nodes = []
    queue = Queue.make({"name": f"default {joy.crypto.address()}"})
    
    for i in range(12):
        name = f"default {joy.crypto.address()}"
        nodes.append(Node.make({
            "queue": queue,
            "name": name,
            "channel": channel.name,
        }))

    logging.info(f'Worker node starting {channel.name}')
    channel.start(
        node_array = RoundRobinNodeArray.make({"nodes": nodes})
    )


# For the platform-specific channels, we need to be careful about getting a task
# to its assigned shard. We must respect the throttle constraints while
# spreading the load as much as possible.
# channel::start will continue until process ends.
else:
    nodes = []

    for shard in channel.shards:
        name = f"{channel.name} {shard}"
        queue = Queue.make({"name": name})
        nodes.append(Node.make({
            "queue": queue,
            "name": name,
            "channel": channel.name,
            "shard": shard
        }))

    logging.info(f'Worker node starting {channel.name}')
    if channel.sidecar:
        run_sidecar(channel.sidecar)
    channel.start(
        node_array = ShardedNodeArray.make({"nodes": nodes})
    )
