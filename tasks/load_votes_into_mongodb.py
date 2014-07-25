import json
import os
from glob import glob

from database import db

def iterate_bill_files():
    for congress in os.listdir('data'):
        if os.path.exists('data/%s/votes' % congress):
            for session in os.listdir('data/%s/votes' % congress):
                for vote in os.listdir('data/%s/votes/%s' % (congress, session)):
                    path = 'data/%s/votes/%s/%s/data.json' % (congress, session, vote)
                    yield path


def run(opts):
    total = 0
    by_request = []
    db.vote.drop()
    for path in iterate_bill_files():
        print path
        vote = json.load(open(path))
        vote['_id'] = vote['vote_id']
        db.vote.save(vote, w=1)
        total += 1

    print 'Total: %d' % total
