#!/usr/bin/env python3
'''
Read new posts from Redis and upvote it if not exeed the limit
'''
import sys
import random
import time
import json
import pprint
import getpass

import base64
import pyelliptic

import yaml
import redis

from steem import Steem

pp = pprint.PrettyPrinter(indent=4)

try:
    rdb = redis.Redis(host="localhost", port=6379)
except Exception:
    print("Error connection to Redis DB")
    sys.exit(0)

try:
    cfg = yaml.load(open("steem_up.yml"))
except Exception:
    print("No config file 'steem_up.yml'!")
    sys.exit(0)

debug  = cfg['debug']
log    = cfg['log']
prefix = cfg['prefix']
lfile  = cfg['log_file']


def to_log(name):
    '''Write to log file '''
    with open(lfile, 'a') as fl:
        fl.write("%s %s\n" % (time.asctime(), name))

limit = float(rdb.get(prefix + "limit"))       # votes per day
if limit < 1:
    to_log("Exceed the limit!")
    sys.exit(0)

timeout = float(cfg['timeout'])        # minutes between votes
vote_count = 0

pk = getpass.getpass()  # secure input
print(len(pk))

iv = base64.b64decode(cfg["iv"])
ctext = base64.b64decode(cfg["id"])
ctx2 = pyelliptic.Cipher(pk, iv, 0, ciphername='bf-cfb')

try:
    out = str(ctx2.ciphering(ctext), 'utf8').strip()
except Exception as e:
    print("Error: %s" % e)
    sys.exit(0)

steem = Steem(keys=out, node=cfg['rpc'])

pp.pprint(steem.get_account(cfg['account']))
del pk
del out

while True:

    utcnow = time.gmtime()              #; print(utcnow) # UTC
    now    = time.mktime(utcnow)        #; print(now)
    keys = rdb.zrangebyscore(prefix + "index", now - 30 * 60, now - 27 * 60)  # in 27 min 
    #print(keys)

    for key in keys:
        post = json.loads(rdb.get(key).decode())             #; print(key, post)
        url = "@%s/%s" % (post["author"], post["permlink"])  #; print(url)

        if log:
            to_log("NEW    %s" % (url))

        #Vote
        try:
            steem.commit.vote(url, int(cfg["weight"]), account=cfg["account"])
        except Exception as e:
            #e = sys.exc_info()[0]
            to_log("Error: %s" % e)

        index = float(rdb.get(prefix + "limit"))
        rdb.set(prefix + "limit", index - 1)

        if log:
            to_log("UPVOTE %s %s" % (url, cfg["weight"]))

        rdb.zadd(prefix + "upvoted", key, int(time.time()))
        rdb.zrem(prefix + "index", key)
        time.sleep(random.uniform(3.5, 30))  # 3.5 - 30 sec

    vote_count += 1
    time.sleep(timeout*60)  # minutes between votes
