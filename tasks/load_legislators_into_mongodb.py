import json
import os
from glob import glob
import yaml
import os.path

from database import db

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def iterate_legislators():
    ids = set()
    records = (
        {'path': 'legislators-current.yaml', 'current': True},
        {'path': 'legislators-historical.yaml', 'current': False},
    )
    for record in records:
        for person in yaml.load(open(os.path.join(ROOT_DIR, 'congress-legislators', record['path']))):
            person['_id'] = person['id']['govtrack']
            person['is_current'] = record['current']
            if person['_id'] in ids:
                raise Exception('Duplicated ID')
            else:
                ids.add(person['_id'])
                yield person


def run(opts):
    total = 0
    by_request = []
    db.legislator.drop()
    for person in iterate_legislators():
        print person['_id']
        db.legislator.save(person)
        total += 1

    print 'Total: %d' % total
