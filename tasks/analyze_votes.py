"""
This script finds changes in members' party affiliation during the
one congress term.
"""
import json
import os
import logging
from datetime import datetime
import sys

from database import db
import analyze_bioguide
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
    if os.path.exists('data/%d/votes' % congress):
        for fname in os.listdir('data/%d/votes' % congress):
            res.append(int(fname))
    return sorted(res)


def iterate_votes_of_session(congress, session, branch):
    """
    Iterate over all votes in given session.

    Order is not defined.
    """

    # file-system storage
    #for vote_fname in os.listdir('data/%s/votes/%s' % (congress, session)):
        #if vote_fname.startswith(branch):
            #full_path = 'data/%s/votes/%s/%s/data.json' % (congress, session, vote_fname)
            #yield full_path, json.load(open(full_path))

    # mongodb storage
    for vote in db.vote.find({'session': str(session)}):
        yield None, vote


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
    # --save-json: bool

    #parser = ArgumentParser()
    #parser.add_argument('-v', '--verbose', action='store_true', default=False)
    #parser.add_argument('-c', '--congress', type=int)
    #opts = parser.parse_args()

    if 'congress' in opts:
        congress_names = [int(opts['congress'])]
    else:
        congress_names = list(iterate_congress_names())

    bioguide_walkers = dict((x[0], x) for x in analyze_bioguide.extract_walkers())

    result_changers = {}

    found_mids = []
    for congress in congress_names:
        title = 'CONGRESS: %s' % congress
        print '=' * len(title)
        print title
        print '=' * len(title)
        members = iterate_members_of_congress(congress)

        for walker in find_party_walkers(members):
            prev_event = walker['history'][0]
            for event in walker['history'][1:]:
                if len(walker['id']) < 7:
                    bioguide_id = db.legislator.find_one({'id.lis': walker['id']})['id']['bioguide']
                else:
                    bioguide_id = walker['id']
                found_mids.append(bioguide_id)
                print '    %s - %s - %s - %s - %s - %s' % (
                    walker['id'], walker['name'],
                    prev_event['date'].strftime('%b/%d/%Y %H:%M'),
                    event['date'].strftime('%b/%d/%Y %H:%M'),
                    prev_event['party'], event['party'],
                )
                if opts.get('verbose'):
                    print '     1) %s 2) %s' % (prev_event['file_path'], event['file_path'])
                print '    http://bioguide.congress.gov/scripts/biodisplay.pl?index=%s' % bioguide_id

                if bioguide_id in bioguide_walkers:

                    def compare_dates(bioguide_date, vote_date1, vote_date2):
                        if bioguide_date is None:
                            # Assume dates match if bioguidate date could not be parsed
                            return True
                        elif bioguide_date.isdigit():
                            # bioguide_date is "dddd" i.e. year
                            year = int(bioguide_date)
                            return vote_date1.year == year or vote_date2.year == year
                        else:
                            # bioguide_date is "Month day, YEAR"
                            date = datetime.strptime(bioguide_date, '%B %d, %Y') 
                            return vote_date1 < date < vote_date2

                    bio_dates = [x[0] for x in bioguide_walkers[bioguide_id][2]]
                    if any(compare_dates(x, prev_event['date'], event['date']) for x in bio_dates):
                        date_status = 'YES'
                    else:
                        date_status = 'NO'
                    print '    [bioguide: YES, dates match: %s]' % date_status
                    for date, snippet in bioguide_walkers[bioguide_id][2]:
                        print '    %s' % snippet
                else:
                    print '    [bioguide: NO]'
                    print '    NA'
                    date_status = None
                print

                if not bioguide_id in result_changers:
                    result_changers[bioguide_id] = {
                        'bioguide_id': bioguide_id,
                        'name': walker['name'],
                        'changes': [],
                    }
                result_changers[bioguide_id]['changes'].append({
                    'time1': {
                        'date': prev_event['date'].strftime('%Y-%m-%dT%H:%M:%S'),
                        'party': prev_event['party'],
                    },
                    'time2': {
                        'date': event['date'].strftime('%Y-%m-%dT%H:%M:%S'),
                        'party': event['party'],
                    },
                    #'bioguide_match': date_status is not None,
                    #'bioguide_date_match': date_status == 'YES',
                })

                prev_event = event


    print
    print '========================'
    print 'Bioguide matched records'
    print '========================'
    matched = [x for x in bioguide_walkers.itervalues() if x[0] in found_mids]
    for mid, name, changes in sorted(matched, key=lambda x: x[0]):
        for date, snippet in changes:
            date_rep = date if date is not None else 'NA'
            print u'[%s] %s (%s) -- %s' % (mid, name, date_rep, snippet)


    print
    print '=========================='
    print 'Bioguide unmatched records'
    print '=========================='
    matched = [x for x in bioguide_walkers.itervalues() if x[0] not in found_mids]
    for mid, name, changes in sorted(matched, key=lambda x: x[0]):
        for date, snippet in changes:
            date_rep = date if date is not None else 'NA'
            print u'[%s] %s (%s) -- %s' % (mid, name, date_rep, snippet)


    if 'save-json' in opts:
        json.dump(result_changers, open('cache/party_changers.json', 'w'), indent=2)
