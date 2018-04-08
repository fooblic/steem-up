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
    CFG = yaml.load(open(os.environ["STEEM_UP"]))
except Exception as e:
    print("Could not load config 'steem_up.yml'! %s" % e)
    sys.exit(0)

DEBUG = CFG['debug']
LOG = CFG['log']
PREFIX = CFG['prefix']
LFILE = CFG['log_file']


def to_log(name):
    '''Write to log file '''
    with open(LFILE, 'a') as fl:
        fl.write("%s %s\n" % (time.asctime(), name))

timeout = float(CFG['timeout'])        # minutes between votes
#vote_count = 0

pk = getpass.getpass()  # secure input
print(len(pk))

iv = base64.b64decode(CFG["iv"])
ctext = base64.b64decode(CFG["id"])
ctx2 = pyelliptic.Cipher(pk, iv, 0, ciphername='bf-cfb')

try:
    out = str(ctx2.ciphering(ctext), 'utf8').strip()
except Exception as e:
    print("Error: %s" % e)
    sys.exit(0)

steem = Steem(keys=out, nodes = [CFG['rpc']])
ACCOUNT = steem.get_account(CFG['account'])
vp = ACCOUNT["voting_power"] / 100

pp.pprint(ACCOUNT)
print(vp)
del pk
del out

try:
    rdb = redis.Redis(host="localhost", port=6379)
except Exception:
    print("Error connection to Redis DB")
    sys.exit(0)

    
def change_vp(vpower):
    '''Cubic function'''
    CENTER = 70
    MAXIMUM = 100 - CENTER

    dv = pow((float(vpower) - CENTER) / MAXIMUM, 3) * MAXIMUM
    newp = vpower + dv

    if newp > 99:
        newp = 99
    elif newp < 10:
        newp = 1
    
    return int(newp)
    

def voting(vkey, vurl, vlimit, vpower):
    '''Vote the post'''

    new_vp = change_vp(vpower)
    
    try:
        #steem.commit.vote(vurl, int(CFG["weight"]), account=CFG["account"])
        steem.commit.vote(vurl, new_vp, account=CFG["account"])
    except Exception as e:
        #e = sys.exc_info()[0]
        to_log("Error: %s" % e)

    #index = float(rdb.get(prefix + "limit"))
    rdb.set(PREFIX + "limit", vlimit - 1)

    rdb.zadd(PREFIX + "upvoted", vkey, int(time.time()))
    rdb.zrem(PREFIX + "index", vkey)

    if LOG:
        to_log("UPVOTE %s VOTE%s VP%s" % (vurl, str(new_vp), str(vpower)))

    time.sleep(random.uniform(3.5, 30))  # 3.5 - 30 sec    


def skip(vkey, vurl, vlimit, vpower):
    '''Remove the post from upvoting list'''

    to_log("Exceed the limit %s!" % vlimit)
    #TODO: save remove stats
    rdb.zrem(PREFIX + "index", vkey)

    if LOG:
        to_log("REMOVE %s VP%s" % (vurl, str(vpower)))

    time.sleep(timeout * 60)  # minutes between votes


while True:

    utcnow = time.gmtime()              #; print(utcnow) # UTC
    now = time.mktime(utcnow)        #; print(now)
    keys = rdb.zrangebyscore(PREFIX + "index", now - 30 * 60, now - 27 * 60)  # in 27 min 
    #print(keys)

    for key in keys:
        post = json.loads(rdb.get(key).decode())             #; print(key, post)
        url = "@%s/%s" % (post["author"], post["permlink"])  #; print(url)

        if LOG:
            to_log("NEW    %s" % (url))

        limit = float(rdb.get(PREFIX + "limit"))       # votes per day
        vp = float(steem.get_account(CFG['account'])["voting_power"]) / 100

        if limit > 0:
            #Vote
            voting(key, url, limit, vp)

        else:
            skip(key, url, limit, vp)

    #vote_count += 1
    time.sleep(timeout * 60)  # minutes between votes
