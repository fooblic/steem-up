#!/usr/bin/env python3
'''
Get last following authors' posts from Steem blockchain
Save it to Redis DB
'''
import os
import pprint
import time
import json
import sys
import hashlib

import yaml
import dateutil.parser
#import datetime

import redis

#from pistonapi.steemnoderpc import SteemNodeRPC
from steem import Steem

# My config
CFG = yaml.load(open(os.environ["STEEM_UP"]))
DEBUG = CFG['debug']
LOG = CFG['log']
RPC = Steem(nodes=[CFG['rpc']])
PRE = CFG['prefix']
DAYS = int(CFG['exp_days'])

FOLLOW = CFG['following']
STOP = CFG['stop_tags']

config = RPC.get_config()
block_interval = config["STEEMIT_BLOCK_INTERVAL"]

pp = pprint.PrettyPrinter(indent=4)
pp.pprint(config)

props = RPC.get_dynamic_global_properties()
li_block = props['last_irreversible_block_num']
pp.pprint(props)

last_block_time = RPC.get_block(li_block)['timestamp']
time_last_block = dateutil.parser.parse(last_block_time)
#pp.pprint(dys)

last_block = li_block
block_count = 0

try:
    rdb = redis.Redis(host="localhost", port=6379)
except Exception:
    print("Error connection to Redis DB")
    sys.exit(0)

rdb.set(PRE + "limit", CFG['limit'])


def update_rdb(arr, db):
    '''
    Get dictionary and put post data to Redis
    The data expires in DAYS constant
    '''
    #print(arr)

    jdump = json.dumps(arr)        #; print(jdump)
    mh = hashlib.md5()
    mh.update(jdump.encode('utf-8'))
    hinfo = mh.hexdigest()         #; print(hinfo)
    key = hinfo[:6]                #; print(key)

    redis_key = "%s%s" % (PRE, key)
    db.set(redis_key, jdump)
    db.expire(redis_key, 60 * 60 * 24 * DAYS)

    time_dys = dateutil.parser.parse(arr['time'])
    ttime = time_dys.utctimetuple()         #; print(ttime)
    db.zadd(PRE + "index", redis_key, int(time.mktime(ttime)))

    if LOG:
        with open(CFG["out_file"], 'a') as fl:
            fl.write("\n##### %s ##### %s\n" % (time.asctime(), key))
            fl.write(jdump)
        if DEBUG:
            print("-->", arr["author"], arr['time'])
        with open(CFG["log_file"], 'a') as fl:
            fl.write("%s POST   %s %s\n" % (time.asctime(), arr["author"], arr['time']))


def stop_tags(metadata):
    ''' Check if tags contain stop words'''
    jdata = json.loads(metadata["json_metadata"])
    if DEBUG:
        print(jdata["tags"])
    for tag in jdata["tags"]:
        if tag in STOP:
            if DEBUG:
                print("STOP tag: %s by %s" % (tag, metadata["author"]))
            return True
    return False


def process_block(br, rpc):
    '''Get block by number and parse it'''
    arr = {}
    dys = rpc.get_block(br)
    try:
        txs = dys['transactions']
    except TypeError:
        return

    for tx in txs:

        for operation in tx['operations']:

            if operation[0] == 'comment' and \
                operation[1]["parent_author"] == "":  # original post

                if DEBUG:
                    #print(br)
                    pp.pprint(operation[1])
                    #pp.pprint(tx['operations'])
                    #pp.pprint(dys)
                    #print(dys['previous'], dys['timestamp'])

                if operation[1]["author"] in FOLLOW:

                    if not stop_tags(operation[1]) and \
                        operation[1]["parent_author"] == "" and \
                        operation[1]["body"][0:2] != "@@":
                        arr = {"time":   dys['timestamp'],
                               "author": operation[1]["author"],
                               #"body":   operation[1]["body"],
                               "json_metadata":    operation[1]["json_metadata"],
                               "parent_permlink":  operation[1]["parent_permlink"],
                               "permlink":   operation[1]["permlink"],
                               "title":     operation[1]["title"]}
                        #print(arr)
                        update_rdb(arr, rdb)

print('Start at block %s ...' % li_block)

while True:

    for block in range(last_block, li_block+1):

        process_block(block, RPC)
        block_count += 1
        if DEBUG:
            print(time.asctime(), block)
        time.sleep(CFG['request_timeout'])

    last_block = li_block
    time.sleep(CFG['sleep_time'])
    props = RPC.get_dynamic_global_properties()
    li_block = props['last_irreversible_block_num']
    if DEBUG:
        print("#", time.asctime(), li_block)
