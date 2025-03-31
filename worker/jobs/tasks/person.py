import logging
import joy
import models
from . import helpers as h


def remove_person(task):
    person_id = h.enforce("person_id", task)
    h.remove_person(person_id)