import pymongo

db = pymongo.MongoClient()['congress']

# Bill index
db.bill.ensure_index('by_request')

# Legislator index
db.legislator.ensure_index('is_current')
db.legislator.ensure_index([('id.thomas', 1)])
db.legislator.ensure_index([('id.lis', 1)])

# Vote index
db.vote.ensure_index('session')
db.vote.ensure_index('congress')
