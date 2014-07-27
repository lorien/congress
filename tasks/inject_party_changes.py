"""
This script injects known changes in party affiliation during the congress term
into `term` objects inside the legislators yaml file.

Affected files:
  * congress-legislators/legislators-current.yaml
  * congress-legislators/legislators-historical.yaml
"""
import json
from datetime import datetime
import rtyaml
from collections import OrderedDict
import hashlib
import cPickle as pickle
import os.path

try:
    from yaml import CLoader as Loader
except ImportError:
    print '*** Warning! ***'
    print 'The yaml.CLoader is not available. It could take much more time to load large yaml files.'


def parse_date(dt):
    if 'T' in dt:
        return datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S')
    else:
        return datetime.strptime(dt, '%Y-%m-%d')


def normalize_party_name(name):
    if name in ('Democrat', 'Independent', 'Republican'):
        return name
    elif name == 'D':
        return 'Democrat'
    elif name == 'I':
        return 'Independent'
    elif name == 'R':
        return 'Republican'
    else:
        raise Exception('Unknown party name: %s' % name)


def load_yaml(path):
    """
    Load data from the yaml-file.

    If pickle-cache is availabe use it instead of bothering with the yaml-file.
    If pickle-cache does not exist, create the pickle-cache after data upacked from the yaml-file.
    """
    raw_data = open(path).read()
    data_hash = hashlib.md5(raw_data).hexdigest()
    cached_path = 'cache/%s.pickle' % data_hash
    if os.path.exists(cached_path):
        print 'Loading cached content of %s from %s' % (path, cached_path)
        data = pickle.load(open(cached_path))
    else:
        print 'Parsing yaml content from %s' % path
        data = rtyaml.load(raw_data)
        print 'Saving parsed data from %s into cache %s' % (path, cached_path)
        pickle.dump(data, open(cached_path, 'w'))
    return data


def process_legislators(legislators, changers):
    mod_count = 0
    for legislator in legislators:
        bio_id = legislator['id'].get('bioguide')
        if bio_id in changers:
            changer = changers[bio_id]
            print 'Injecting party changes into record of %s [%s]' % (changer['name'], changer['bioguide_id'])
            mod_count += 1

            # First, delete old "party_changes" from each term object
            # to avoid any update/collision issues
            for term in legislator['terms']:
                if 'party_changes' in term:
                    del term['party_changes']
            for change in changer['changes']:
                change_date = parse_date(change['time2']['date'])

                term_found = False
                for term in legislator['terms']:
                    if parse_date(term['start']) < change_date < parse_date(term['end']):
                        term_found = True
                        term_start = parse_date(term['start'])
                        party_changes = term.setdefault('party_changes', [])
                        party_changes.append(OrderedDict((
                            ('start', term_start.strftime('%Y-%m-%d')),
                            ('end', change_date.strftime('%Y-%m-%d')),
                            ('party', normalize_party_name(change['time1']['party'])),
                        )))
                if not term_found:
                    raise Exception('Term not found for legislator %s' % bio_id)
    return mod_count


def run(opts):
    changers = json.load(open('cache/party_changers.json'))
    legislators_current = load_yaml('congress-legislators/legislators-current.yaml')
    legislators_historical = load_yaml('congress-legislators/legislators-historical.yaml')

    current_mods = process_legislators(legislators_current, changers)
    historical_mods = process_legislators(legislators_historical, changers)

    rtyaml.dump(legislators_current, open('congress-legislators/legislators-current.new.yaml', 'w'))
    rtyaml.dump(legislators_historical, open('congress-legislators/legislators-historical.new.yaml', 'w'))

    print 'Party changes injected into legislators-current.yaml: %d' % current_mods
    print 'Party changes injected into legislators-historical.yaml: %d' % historical_mods
