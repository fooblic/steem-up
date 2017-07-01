#!/usr/bin/env python3
'''
Get last following posts from Steem blockchain
Save it to Redis DB
'''
import pprint
import time
import json
import sys
import hashlib

import yaml
import dateutil.parser
#import datetime

import redis

from pistonapi.steemnoderpc import SteemNodeRPC

# My config
my_config = yaml.load(open("steem_up.yml"))
debug = my_config['debug']
log   = my_config['log']
rpc   = SteemNodeRPC(my_config['rpc'])
prefix = my_config['prefix']
days = int(my_config['exp_days'])

try:
    rdb = redis.Redis(host="localhost", port=6379)
except Exception:
    print("Error connection to Redis DB")
    sys.exit(0)

rdb.set(prefix + "limit", my_config['limit'])

following = my_config['following']

config = rpc.get_config()
block_interval = config["STEEMIT_BLOCK_INTERVAL"]

pp = pprint.PrettyPrinter(indent=4)
pp.pprint(config)

props = rpc.get_dynamic_global_properties()
li_block = props['last_irreversible_block_num']
pp.pprint(props)

last_block_time = rpc.get_block(li_block)['timestamp']
time_last_block = dateutil.parser.parse(last_block_time)
#pp.pprint(dys)

last_block = li_block
block_count = 0


def update_rdb(arr, rdb):
    #print(arr)

    jdump = json.dumps(arr)        #; print(jdump)
    mh = hashlib.md5()
    mh.update(jdump.encode('utf-8'))     
    hinfo = mh.hexdigest()         #; print(hinfo)
    key = hinfo[:6]                #; print(key)

    redis_key = "%s%s" % (prefix, key)
    rdb.set(redis_key, jdump)
    rdb.expire(redis_key, 60*60*24*days)

    time_dys = dateutil.parser.parse(arr['time'])
    ttime    = time_dys.utctimetuple()         #; print(ttime)
    rdb.zadd(prefix + "index", redis_key, int(time.mktime(ttime) ) )

    if log:
        with open(my_config["out_file"], 'a') as fl:
            fl.write("\n##### %s ##### %s\n" % (time.asctime(), key) )
            fl.write(jdump)
        if debug:
            print("-->", arr["author"], arr['time'])
        with open(my_config["log_file"], 'a') as fl:
            fl.write("%s POST   %s %s\n" % (time.asctime(), arr["author"], arr['time']))


def process_block(br, rpc):

    arr = {}
    dys = rpc.get_block(br)
    txs = dys['transactions']

    for tx in txs:

        for operation in tx['operations']:

            if operation[0] == 'comment' and \
                operation[1]["parent_author"] == "": # original post

                if debug:
                    print(br)
                    pp.pprint(tx['operations'])
                    #pp.pprint(dys)
                    #print(dys['previous'], dys['timestamp'])

                if operation[0] == 'comment':

                    if operation[1]["author"] in following and \
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

        process_block(block, rpc)
        block_count += 1
        if debug:
            print(time.asctime(), block)
        time.sleep(my_config['request_timeout'])

    last_block = li_block
    time.sleep(my_config['sleep_time'])
    props = rpc.get_dynamic_global_properties()
    li_block = props['last_irreversible_block_num']
    if debug:
        print("#", time.asctime(), li_block)
