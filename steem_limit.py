#!/usr/bin/env python3
'''
Update vote limit in Redis DB
Remove old items
'''
import sys
import time

import yaml
import redis

CFG = yaml.load(open("steem_up.yml"))
LOG = CFG['log']
LFILE = CFG['log_file']
LIM = CFG['limit']
PRE = CFG['prefix']

try:
    rdb = redis.Redis(host="localhost", port=6379)
except Exception as e:
    print("Error connection to Redis DB! %s\n" % e)
    sys.exit(0)


def to_log(name, value):
    '''Write to log file '''
    with open(LFILE, 'a') as fname:
        fname.write("%s %s %s\n" % (time.asctime(), name, value))

CUR_LIM = float(rdb.get(PRE + "limit"))

if CUR_LIM < LIM:
    NEW_LIM = CUR_LIM + LIM/24  # per hour
    rdb.set(PRE + "limit", NEW_LIM)

    if LOG:
        with open(LFILE, 'a') as fl:
            fl.write("%s new_limit: %.1f\n" % (time.asctime(), NEW_LIM))

NOW = time.mktime(time.gmtime())  # seconds
KEYS = rdb.zrangebyscore(PRE + "upvoted", 0, NOW - 60 * 60 * 24 * 7)  # older then 7 days

for key in KEYS:
    rdb.zrem(PRE + "upvoted", key)

    if LOG:
        to_log("remove_upvoted:", key)

POSTS = rdb.zrangebyscore(PRE + "index", 0, NOW - 60 * 60 * 24)  # older then a days

for post in POSTS:
    rdb.zrem(PRE + "index", post)

    if LOG:
        to_log("remove_indexed:", post)
