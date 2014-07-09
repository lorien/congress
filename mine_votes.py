from glob import glob
import json
from collections import defaultdict
import os
import logging

def main():
    for congress in os.listdir('data'):
        congress = int(congress)
        for session in os.listdir('data/%s/votes' % congress):
            session = int(session)
            rolls = {}
            for branch in ('h', 's'):
                members = {}
                for roll_name in os.listdir('data/%s/votes/%s' % (congress, session)):
                    if roll_name.startswith(branch):
                        rolls[int(roll_name.lstrip(branch))] = roll_name
                for roll_num, roll_name in sorted(rolls.items(), key=lambda x: x[0]):
                    path = 'data/%s/votes/%s/%s/data.json' % (congress, session, roll_name)
                    data = json.load(open(path))
                    for vote_type in data['votes']:
                        votes = data['votes'][vote_type]
                        for vote in votes:
                            if vote == 'VP':
                                pass
                            else:
                                if not vote['id'] in members:
                                    members[vote['id']] = {
                                        'name': vote['display_name'],
                                        'current_party': vote['party'],
                                        'history': [{
                                            'date': data['date'],
                                            'party': vote['party'],
                                        }]
                                    }
                                else:
                                    if members[vote['id']]['current_party'] != vote['party']:
                                        members[vote['id']]['current_party'] = vote['party']
                                        members[vote['id']]['history'].append({
                                            'date': data['date'],
                                            'party': vote['party'],
                                        })

                path_displayed = False
                for mid, info in members.items():
                    if len(info['history']) > 1:
                        if not path_displayed:
                            print 'SESSION: %s' % path
                            path_displayed = True
                        print u'%s [%s]' % (mid, info['name'])
                        for event in info['history']:
                            print '* %s -> %s' % (event['date'], event['party'])


if __name__ == '__main__':
    main()
