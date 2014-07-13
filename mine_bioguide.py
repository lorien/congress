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

REX_CHANGE = re.compile(r'(changed (\S+ )?party affiliation|changed from|switched to).{40}', re.I)

def main():
    members = {}
    for row in csv.reader(open('cache/bioguide3.csv')):
        mid, bio = row
        name = ','.join(bio.split(',', 2)[:2])

        match = REX_CHANGE.search(bio)
        if match:
            if not mid in KNOWN_PERSONS:
                print mid, name, ' -- ', match.group(0)


if __name__ == '__main__':
    main()
