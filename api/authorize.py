import logging
import os
import time
from flask import Flask, request, g
import httpx
from jose import jwt
import http_errors
import models

# TODO: Configuration
OUTSETA_DOMAIN = os.environ.get("OUTSETA_DOMAIN")
API_AUDIENCE = "gobo.outseta.com"
TOKEN_ISSUER = "https://gobo.outseta.com" 
ALGORITHMS = ["RS256"]
JWKS_TIMEOUT = 3600

cache = {}


def parse_authorization():
    header = request.headers.get("Authorization")
    if header == None:
        raise http_errors.unauthorized("request is missing authorization header")

    parts = header.split()
    if len(parts) != 2:
        raise http_errors.unauthorized("authorization header does not use expected format")

    return parts

def refresh_keyset():
    with httpx.Client() as client:
        r = client.get(f"https://{OUTSETA_DOMAIN}/.well-known/jwks")
        value = r.json()

        cache["jwks"] = {
          "value": value,
          "time": time.time()
        }
        return value

def fetch_keyset():
    keyset = cache.get("jwks")
    if keyset == None:      
        return refresh_keyset()
    elif time.time() - keyset["time"] >= JWKS_TIMEOUT:
        return refresh_keyset()
    else:
        return keyset["value"]



def validate_token(token):    
    jwks = fetch_keyset()
    unverified_claims = jwt.get_unverified_header(token)
    
    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == unverified_claims["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
    
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer=TOKEN_ISSUER
            )
        except jwt.ExpiredSignatureError:
            raise http_errors.unauthorized("token is expired")
        except jwt.JWTClaimsError:
            raise http_errors.unauthorized("incorrect claims, please check audience and issuer")
        except Exception:
            raise http_errors.unauthorized("unable to parse authentication token")
    
        return payload
        
    raise http_errors.unauthorized("Unable to find appropriate key")


"""
We're using Outseta as our identity authority. Because their overall goal is
to simplify authority integration with a product, they tend toward implicit
or prescriptive configurations to reduce the surface area they expose to
customers.

So instead of explicit role manament, they provide subscription, plan,
and add-on information that a person / person's group has purchased. 
In Gobo, we map this information into roles for access control.

We handle that mapping all upfront once we get the raw Outseta data.
I've created the Permission class to serve as a RBAC oracle. Any question we
need answered in the application, like limits on persona count,
or a lockout of some feature, needs to evaluted here and the class can
provide answers to those questions.
"""

ADMIN_PLANS = [
    "496Gr7WX"
]

GENERAL_PLANS = [
    "BWz5El9E"
]


class Permission():
    def __init__(self, data):
        self.plan = data["plan"]
        self.addons = data["addons"]
        self.roles = set()

    # TODO: This will get more sophsiticated in the future.
    def evaluate_mapping(self):
        if self.plan in ADMIN_PLANS:
            self.roles.add('admin')
        if self.plan in GENERAL_PLANS:
            self.roles.add('general')

    @staticmethod
    def make(data):
        if data is None:
            raise Exception("raw dictionary passed to Permission constructor is None")
        if data.get('plan') is None:
            raise Exception("plan passed to Permission constructor is None")
        
        self = Permission(data)
        self.evaluate_mapping()
        return self



def get_permission(token):
    claims = validate_token(token)
    g.claims = claims

    # Maps subscription information into role-based access control.
    return Permission.make({
        "plan": claims.get("outseta:planUid", ""),
        "addons": claims.get("outseta:addOnUids", [])
    })


def lookup_gobo_key(key): 
    key = models.gobo_key.find({"key": key})
    if key is None:
        return None
    
    return key["person_id"]



def authorize_request(configuration):
    try:
        schema = configuration.get("request").get("authorization")
        if schema is None:
            schema = []
        
        if "public" in schema:
            return
        
        # Below this, we're looking at the authorization header.
        parts = parse_authorization()            
        
        
        if parts[0] == "GoboKey":
            # Relies on internally managed bearer credential.
            if "gobo-key" not in schema:
                raise Exception("no matching permissions")

            person_id = lookup_gobo_key(parts[1])
            if person_id is None:
                raise Exception("no matching permissions")
            
            if "general" in schema:
                g.person = models.person.get(person_id)
                return

            if person_id == request.view_args.get("person_id"):
                g.person = models.person.get(person_id)
                return
            
            raise Exception("no matching permissions")
        

        elif parts[0] == "Bearer":
            # Relies on integration with Outseta        
            permission = get_permission(parts[1])
        
            if "admin" in permission.roles:
                return

            if "general" in permission.roles and "general" in schema:
                return

            if "person" in schema:
                person = models.person.lookup(g.claims["sub"])
                if person["id"] != request.view_args.get("person_id"):
                    raise Exception("no matching permissions")
                g.person = person
                return

            raise Exception("no matching permissions")
 

        else:
            raise http_errors.unauthorized("authorization header does not use expected scheme")
        

    except Exception:
        raise http_errors.unauthorized("requester lacks proper permissions")

    
    