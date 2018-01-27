#!/usr/bin/env python3
'''
Read new posts from Redis and upvote it if not exeed the limit
'''
import sys
import os
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
    cfg = yaml.load(open(os.environ["STEEM_UP"]))
except Exception as e:
    print("Could not load config 'steem_up.yml'! %s" % e)
    sys.exit(0)

debug  = cfg['debug']
log    = cfg['log']
prefix = cfg['prefix']
lfile  = cfg['log_file']


def to_log(name):
    '''Write to log file '''
    with open(lfile, 'a') as fl:
        fl.write("%s %s\n" % (time.asctime(), name))

timeout = float(cfg['timeout'])        # minutes between votes
#vote_count = 0

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

steem = Steem(keys=out, nodes = [cfg['rpc']])

pp.pprint(steem.get_account(cfg['account']))
del pk
del out

try:
    rdb = redis.Redis(host="localhost", port=6379)
except Exception:
    print("Error connection to Redis DB")
    sys.exit(0)


def voting(vkey, vurl, vlimit):
    '''Vote the post'''

    try:
        steem.commit.vote(vurl, int(cfg["weight"]), account=cfg["account"])
    except Exception as e:
        #e = sys.exc_info()[0]
        to_log("Error: %s" % e)

    #index = float(rdb.get(prefix + "limit"))
    rdb.set(prefix + "limit", vlimit - 1)

    rdb.zadd(prefix + "upvoted", vkey, int(time.time()))
    rdb.zrem(prefix + "index", vkey)

    if log:
        to_log("UPVOTE %s %s" % (vurl, cfg["weight"]))

    time.sleep(random.uniform(3.5, 30))  # 3.5 - 30 sec    


def skip(vkey, vurl, vlimit):
    '''Remove the post from upvoting list'''

    to_log("Exceed the limit %s!" % vlimit)
    #TODO: save remove stats
    rdb.zrem(prefix + "index", vkey)

    if log:
        to_log("REMOVE %s %s" % (vurl, cfg["weight"]))

    time.sleep(timeout*60)  # minutes between votes


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

        limit = float(rdb.get(prefix + "limit"))       # votes per day
        if limit > 0:
            #Vote
            voting(key, url, limit)

        else:
            skip(key, url, limit)

    #vote_count += 1
    time.sleep(timeout*60)  # minutes between votes
