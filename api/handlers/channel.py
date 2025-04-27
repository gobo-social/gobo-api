import logging
from flask import request
import http_errors
import models
from .helpers import parse_query

def _parse_channel_query(parameters, args):
    value = args.get("name")
    if value != None:
        parameters["where"].append({
            "key": "name",
            "value": value,
            "operator": "eq"
        })

def channels_get():
    views = ["created"]
    parameters = parse_query(views, request.args)
    _parse_channel_query(parameters, request.args)
    return {"content": models.channel.query(parameters)}

def channels_post():
    channel = models.channel.add(request.json)
    return {"content": channel}

def channel_get(id):
    channel = models.channel.get(id)
    if channel == None:
        raise http_errors.not_found(f"channel {id} is not found")
    
    return {"content": channel}

def channel_put(id):
    if request.json["id"] != None and id != request.json["id"]:
        raise http_errors.unprocessable_content(
            f"channel {id} does not match resource in body, rejecting"
        )

    channel = models.channel.update(id, request.json)
    if channel == None:
        channel = models.channel.add(request.json)

    return {"content": channel}

def channel_delete(id):
    channel = models.channel.remove(id)
    if channel == None:
        raise http_errors.not_found(f"channel {id} is not found")

    return {"content": ""}