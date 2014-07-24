import json
import os
from glob import glob

from database import db

def iterate_bill_files():
    for congress in os.listdir('data'):
        for btype in os.listdir('data/%s/bills' % congress):
            for bill in os.listdir('data/%s/bills/%s' % (congress, btype)):
                path = 'data/%s/bills/%s/%s/data.json' % (congress, btype, bill)
                yield path


def run(opts):
    total = 0
    by_request = []
    db.bill.drop()
    for path in iterate_bill_files():
        print path
        bill = json.load(open(path))
        bill['_id'] = bill['bill_id']
        db.bill.save(bill, w=1)
        total += 1

    print 'Total: %d' % total
