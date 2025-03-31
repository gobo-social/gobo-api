import logging
import joy
import models
from clients import Mastodon
import http_errors
from .helpers import get_mastodon_credentials
from tasks import Task


def get_redirect_url(person, base_url):
    get_mastodon_credentials(base_url)
    client = Mastodon({"base_url": base_url})
    client.login()
    state = joy.crypto.address()
    url = client.get_redirect_url(state)

    _registration = {
        "person_id": person["id"],
        "platform": "mastodon",
        "base_url": base_url,
        "state": state
    }

    registration = models.registration.find({
      "person_id": person["id"],
      "base_url": base_url
    })

    if registration == None:
        models.registration.add(_registration)
    else:
        models.registration.update(registration["id"], _registration)

    return {"redirect_url": url}


def validate_callback(data, base_url):
    output = {
      "base_url": base_url,
      "state": data.get("state", None),
      "code": data.get("code", None)
    }

    if output["state"] == None:
        raise http_errors.bad_request("field state is required")
    if output["code"] == None:
        raise http_errors.bad_request("field code is required")
    return output


def confirm_identity(registration, data):
    base_url = data["base_url"]

    if registration.get("state") == None:
        raise http_errors.unprocessable_content("invalid registration, retry step 1 of identity onboarding")

    if registration.get("state") != data["state"]:
        raise http_errors.unprocessable_content("state doesn't match, retry step 1 of identity onboarding")

    _client = models.mastodon_client.find({"base_url": base_url})
    if _client == None:
        raise http_errors.unprocessable_content(f"GOBO has no Mastodon server associated with {base_url}")

    # Convert the code into a durable OAuth token
    try:
        client = Mastodon(_client)
        client.login()
        oauth_token = client.convert_code(data["code"])
    except Exception as e:
        logging.warning(e)
        raise http_errors.unprocessable_content("unable to process provider credentials")


    # Fetch profile data to associate with this identity.
    try:
        client = Mastodon({
            "base_url": base_url,
            "oauth_token": oauth_token
        })
        client.login()
        profile = client.get_profile()
    except Exception as e:
        logging.warning(e)
        raise http_errors.unprocessable_content("unable to access profile from platform")
  
 
    # Pull together data to build an identity record.  
    profile_url = profile.url
    _identity = {
        "person_id": registration["person_id"],
        "platform": "mastodon",
        "platform_id": str(profile.id),
        "base_url": base_url,
        "profile_url": profile_url,
        "profile_image": profile.avatar,
        "username": profile.username,
        "name": profile.display_name,
        "oauth_token": oauth_token,
        "stale": False
    }

    # Store and finalize
    identity = models.identity.upsert(_identity)

    models.link.upsert({
      "origin_type": "person",
      "origin_id": identity["person_id"],
      "target_type": "identity",
      "target_id": identity["id"],
      "name": "has-identity",
      "secondary": None
    })

    Task.send(
        channel = "default",
        name = "flow - update identity",
        priority = 1,
        details = {
            "identity": identity,
            "is_onboarding": True
        }
    )
    
    models.registration.remove(registration["id"])

    return identity
