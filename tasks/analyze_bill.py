from collections import Counter
from datetime import datetime

from database import db

def parse_date(val):
    return datetime.strptime(val, '%Y-%m-%d').date()


def render_pairs(pairs):
    out = []
    for val, count in pairs:
        out.append('%s (%d)' % (val, count))
    return ', '.join(out) 


def print_stat(stat, year):
    title = 'Year: %s' % str(year).title()
    print title 
    print '-' * len(title)

    print 'Status:',
    print render_pairs(stat[year]['status'].most_common())

    print 'Branch:',
    print render_pairs(stat[year]['branch'].most_common())

    print 'Party:',
    print render_pairs(stat[year]['party'].most_common())

    print 'Top 10 states:',
    print render_pairs(stat[year]['state'].most_common(10))
    print 'Count: %d' % stat[year]['count']

    print


def get_empty_stat_item():
    return {
        'status': Counter(),
        'branch': Counter(),
        'party': Counter(),
        'state': Counter(),
        'count': 0,
    }


def load_legislators():
    reg = {}
    for leg in db.legislator.find():
        if 'thomas' in leg['id']:
            reg[leg['id']['thomas']] = leg['terms'][-1]['party']
    return reg


def run(opts):
    total = 0

    legislators = load_legislators()
    stat = {
        'total': get_empty_stat_item(),
    }

    for bill in db.bill.find({'by_request': True}):
        stat[parse_date(bill['introduced_at']).year] = get_empty_stat_item()


    for bill in db.bill.find({'by_request': True}):
        year = parse_date(bill['introduced_at']).year

        stat[year]['status'][bill['status']] += 1
        stat['total']['status'][bill['status']] += 1

        title = bill['sponsor'].get('Title', bill['sponsor']['title'])
        stat[year]['branch'][title] += 1
        stat['total']['branch'][title] += 1

        party = legislators[bill['sponsor']['thomas_id']]
        stat[year]['party'][party] += 1
        stat['total']['party'][party] += 1

        stat[year]['state'][bill['sponsor']['state']] += 1
        stat['total']['state'][bill['sponsor']['state']] += 1

        stat[year]['count'] += 1
        stat['total']['count'] += 1

    print 'Bills by Request Statistics'
    print '==========================='
    print

    for key in sorted([x for x in stat.keys() if x != 'total']):
        print_stat(stat, key)
    print_stat(stat, 'total')
