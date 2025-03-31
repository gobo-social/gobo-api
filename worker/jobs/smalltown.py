import logging
import models
import joy
from clients import Smalltown
from . import tasks

h = tasks.helpers

def dispatch(task):
    if task.name == "get profile":
        return tasks.get_profile(task)
    
    
    if task.name == "pull sources":
        return tasks.pull_sources(task)
    if task.name == "pull posts":
        return tasks.pull_posts(task)
    if task.name == "pull notifications":
        return tasks.pull_notifications(task)

    if task.name == "dismiss notification":
        return tasks.dismiss_notification(task)
    

    if task.name == "create post":
        return create_post(task)
    if task.name == "unpublish post":
        return unpublish_post(task)
    if task.name == "add post edge":
       return add_post_edge(task)
    if task.name == "remove post edge":
        return remove_post_edge(task)

    logging.warning("No matching job for task: %s", task)
    

@tasks.handle_stale
@tasks.handle_delivery
def create_post(task):
    identity = h.enforce("identity", task)
    thread = h.enforce("thread", task)

    client = Smalltown(identity)
    client.login()

    references = []
    reply_parent = None
    for post in thread:
        metadata = post["metadata"]

        if reply_parent is not None:
            metadata["reply"] = reply_parent

        if len(post["attachments"]) > 4:
            raise Exception("smalltown posts are limited to 4 attachments.")
        for file in post["attachments"]:
            file["data"] = h.read_draft_file(file)

        result = client.create_post(post, metadata)
        logging.info("smalltown: create post complete")    

        reply_parent = {
            "platform_id": result["id"]
        }

        references.append({
            "reference": result["id"],
            "url": result["url"]
        })

    return references


@tasks.handle_stale
@tasks.handle_unpublish
def unpublish_post(task):
    identity = h.enforce("identity", task)
    target = h.enforce("target", task)
    references = target["stash"]["references"]

    client = Smalltown(identity)
    client.login()
    for item in references:
        client.remove_post(item["reference"])
    logging.info("smalltown: unpublish post complete")


@tasks.handle_stale
def add_post_edge(task):
    identity = h.enforce("identity", task)
    post = h.enforce("post", task)
    name = h.enforce("name", task)
    edge = h.enforce("edge", task)
    client = Smalltown(identity)
    client.login()

    if name in ["like", "repost"]:
        if name == "like":
            client.favourite_post(post)
            models.post_edge.add(edge)
            logging.info(f"smalltown: like post complete on {post['id']}")
        elif name == "repost":
            client.boost_post(post)
            models.post_edge.add(edge)
            logging.info(f"smalltown: repost post complete on {post['id']}")
    else:
        raise Exception(
            f"smalltown does not have post edge action defined for {name}"
        )


@tasks.handle_stale
def remove_post_edge(task):
    identity = h.enforce("identity", task)
    post = h.enforce("post", task)
    name = h.enforce("name", task)
    edge = h.enforce("edge", task)
    client = Smalltown(identity)
    client.login()

    if name in ["like", "repost"]:
        if name == "like":
            client.undo_favourite_post(post)
            models.post_edge.remove(edge["id"])
            logging.info(f"smalltown: undo like post complete on {post['id']}")
        elif name == "repost":
            client.undo_boost_post(post)
            models.post_edge.remove(edge["id"])
            logging.info(f"smalltown: undo repost post complete on {post['id']}")
    else:
        raise Exception(
            f"smalltown does not have post edge action defined for {name}"
        )
