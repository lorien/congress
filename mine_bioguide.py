import csv
import re

KNOWN_PERSONS = (
   'T000058',
   'L000119',
   'P000066',
   'D000168',
   'H000390',
   'G000280',
   'M000206',
   'F000257',
   'J000072',
   'H000067',
   'A000361',
   'S001177',
   'G000557',
   'S000709',
   'H001028',
   'H000323',
   'P000596',
   'E000172',
   'G000280',
)

REX_CHANGE = re.compile(r'(changed (\S+ )?party affiliation|changed from|switched to)[^;]+', re.I)
REX_CHANGE_DATE = re.compile(r'\b\w+ \d+, \d{4}\b', re.I)
REX_CHANGE_YEAR = re.compile(r'\b\d{4}\b', re.I)

def main():
    members = {}
    walkers = {
        'known': [],
        'new': [],
    }
    for row in csv.reader(open('cache/bioguide3.csv')):
        mid, bio = [x.decode('utf-8') for x in row]
        name = ','.join(bio.split(',', 2)[:2])

        match = REX_CHANGE.search(bio)
        if match:
            snippet = match.group(0)
            try:
                change_date = REX_CHANGE_DATE.search(snippet).group(0)
            except AttributeError:
                try:
                    change_date = REX_CHANGE_YEAR.search(snippet).group(0)
                except AttributeError:
                    change_date = None
            item = (mid, name, change_date, snippet)
            if mid in KNOWN_PERSONS:
                walkers['known'].append(item)
            else:
                walkers['new'].append(item)

    print '============='
    print 'Known walkers'
    print '============='
    for mid, name, date, snippet in walkers['known']:
        date_rep = date if date is not None else 'NA'
        print u'[%s] %s (%s) -- %s' % (mid, name, date_rep, snippet)


    print
    print '=============='
    print 'Unnown walkers'
    print '=============='
    for mid, name, date, snippet in walkers['known']:
        print u'[%s] %s (%s) -- %s' % (mid, name, date, snippet)


if __name__ == '__main__':
    main()
