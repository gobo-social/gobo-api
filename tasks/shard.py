import logging
from os import environ
import time
import hashlib
import models

where = models.helpers.where
QueryIterator = models.helpers.QueryIterator

FLAG_LATENCY = int(environ.get("FLAG_LATENCY", 60))
cache = {}

# This allows us to estimate how many shards are available so we can dynamically
# distribute tasks to the available shards. However this algorithm only counts
# the total shards. We'd want to consider other options in the future.
def get_counts():
    channels = QueryIterator(model = models.channel)
    seen = set()
    counts = {}
    for channel in channels:
        name = channel["name"]
        seen.add(name)
        if not channel["processing"]:
            continue
        value = counts.get(name, 0)
        counts[name] = value + len(channel["shards"])
    
    # This allows us to gracefully gather tasks if we are otherwise unable to
    # determine how many shards there are.
    for name in seen:
        if name not in counts:
            counts[name] = 1
    
    return counts

def refresh_counts():
    value = get_counts()
    cache["counts"] = {
        "value": value,
        "time": time.time()
    }
    return value

def fetch_counts():
    bundle = cache.get("counts")
    if bundle == None:      
        return refresh_counts()
    elif time.time() - bundle["time"] >= FLAG_LATENCY:
        return refresh_counts()
    else:
        return bundle["value"]



# Based on uniform hashing algorithm here:
# https://www.d.umn.edu/~gshute/cs2511/slides/hash_tables/sections/uniform_hashing.xhtml
def uniform_shard(string, count):    
    m = hashlib.sha512()
    m.update(bytearray(string, "utf-8"))
    byte_array = m.digest()
    
    result = 1
    for value in byte_array:
      result = (result * 31) + value
    return result % count

def get_shard(platform, task):
    counts = fetch_counts()
    
    if platform not in counts:
        raise Exception(f"channel {platform} is not recognized")

    identity = task.details.get("identity")
    if identity is None:
        raise Exception("cannot shard a task that lacks an identity")
    
    base_url = identity.get("base_url")
    if base_url is None:
        raise Exception("cannot shard a task with identity that lacks base_url")
    
    platform_id = identity.get("platform_id")
    if platform_id is None:
        raise Exception("cannot shard a task with identity that lacks platform_id")
    
    string = base_url + platform_id
    count = counts[platform]
    return uniform_shard(string, count)


non_shard_channels = [
    "default",
    "cron"
]

def shard_task(task):
  channel = task.channel
  
  if channel in non_shard_channels:
      return 0
  else:
      return get_shard(channel, task)
