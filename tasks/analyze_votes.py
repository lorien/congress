"""
This script finds changes in members' party affiliation during the
one congress term.
"""
import json
import os
import logging
from datetime import datetime
import sys
#from argparse import ArgumentParser

def iterate_congress_names():
    """
    Iterate over all congress names in hronological order.
    """
    res = []
    for fname in os.listdir('data'):
        res.append(int(fname))
    return sorted(res)


def iterate_sessions_of_congress(congress):
    """
    Iterate over all session in given congress in hronological order.
    """
    res = []
    for fname in os.listdir('data/%d/votes' % congress):
        res.append(int(fname))
    return sorted(res)


def iterate_votes_of_session(congress, session, branch):
    """
    Iterate over all votes in given session.

    Order is not defined.
    """
    for vote_fname in os.listdir('data/%s/votes/%s' % (congress, session)):
        if vote_fname.startswith(branch):
            full_path = 'data/%s/votes/%s/%s/data.json' % (congress, session, vote_fname)
            yield full_path, json.load(open(full_path))


def parse_vote_date(date_str):
    """
    Convert date from text representation into `datetime` object.
    """
    # Example of input: 2003-01-07T12:30:00-05:00
    # Ignore time zone offset
    dt = date_str.rsplit('-', 1)[0]
    return datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S')
   

def iterate_vote_records(vote_data):
    """
    Iterate over members' votes of particular roll call vote.
    """
    vote_date = parse_vote_date(vote_data['date'])
    for vote_type, votes in vote_data['votes'].iteritems():
        for vote in votes:
            if vote == 'VP':
                pass
            else:
                yield {
                    'display_name': vote['display_name'],
                    'id': vote['id'],
                    'date': vote_date,
                    'party': vote['party'],
                }


def iterate_members_of_congress(congress):
    """
    Iterate over personal and vote history information
    of each member of the given congress.
    """
    members = {}

    # Load vote records of each member of the given congress
    for session in iterate_sessions_of_congress(congress):
        for branch in ('h', 's'):
            for file_path, vote_data in iterate_votes_of_session(congress, session, branch):
                for record in iterate_vote_records(vote_data):
                    if not record['id'] in members:
                        members[record['id']] = {
                            'id': record['id'],
                            'name': record['display_name'],
                            'party_log': [],
                        }
                    members[record['id']]['party_log'].append({
                        'date': record['date'],
                        'party': record['party'],
                        'file_path': file_path,
                    })

    return members


def find_party_walkers(members):
    """
    Iterate over those members of particular congress
    who have changed party affiliation during the congress
    at least one time.
    """
    for member_id, member in members.iteritems():
        history = []
        current_party = None
        for event in sorted(member['party_log'], key=lambda x: x['date']):
            if event['party'] != current_party:
                history.append(event)
                current_party = event['party']
        if len(history) > 1:
            yield {
                'id': member['id'],
                'name': member['name'],
                'history': history,
            }


def run(opts):
    # Opts
    # --verbose: bool
    # --congress: int

    #parser = ArgumentParser()
    #parser.add_argument('-v', '--verbose', action='store_true', default=False)
    #parser.add_argument('-c', '--congress', type=int)
    #opts = parser.parse_args()

    if opts['congress']:
        congress_names = [int(opts['congress'])]
    else:
        congress_names = list(iterate_congress_names())

    for congress in congress_names:
        print 'CONGRESS: %s' % congress
        print '-------------'
        members = iterate_members_of_congress(congress)

        for walker in find_party_walkers(members):
            prev_event = walker['history'][0]
            for event in walker['history'][1:]:
                print '   %s - %s - %s - %s - %s - %s' % (
                    walker['id'], walker['name'],
                    prev_event['date'].strftime('%b/%d/%Y %H:%M'),
                    event['date'].strftime('%b/%d/%Y %H:%M'),
                    prev_event['party'], event['party'],
                )
                if opts.get('verbose'):
                    print '     1) %s 2) %s' % (prev_event['file_path'], event['file_path'])
                prev_event = event
