#!/usr/bin/env python3
'''Get last day upvoted report and send over xmpp'''
import os
import pprint
import json
import time
import subprocess

import redis
import yaml

from steem import Steem

#import jabber_send  # for python2.7

CFG = yaml.load(open(os.environ["STEEM_UP"]))
LOG = CFG['log']
PRE = CFG["prefix"]

rdb = redis.Redis(host=CFG["redis_host"], port=CFG["redis_port"])
pp = pprint.PrettyPrinter(indent=4)

# Steem upvoted
NOW = time.mktime(time.gmtime())        #; print NOW
redis_keys = rdb.zrangebyscore(PRE + "upvoted", NOW - 60 * 60 * 24, NOW)  # in 24h

posts = []
authors = set()
for post in redis_keys[::-1]:  # from the list end
    item = json.loads(rdb.get(post).decode())

    url = "https://steemit.com/%s/@%s/%s" % (item['parent_permlink'],
                                             item['author'],
                                             item['permlink'])

    posts.append("%s - %s" % (item["time"], url))
    authors.add(item['author'])

steem = Steem(nodes = [CFG['rpc']])
ACCOUNT = steem.get_account(CFG['account'])

report = "Last: %s" % ACCOUNT["last_vote_time"]
report += "\nVP: %s" % str(ACCOUNT["voting_power"] / 100)
report += "\nRate limit: %.1f" % float(rdb.get(PRE + "limit"))
report += "\n%s posts with authors:\n" % len(posts)
report += ", ".join(str(s) for s in authors)
report += "\nReward: %s" % ACCOUNT["reward_vesting_steem"]

#if posts:
#    jabber_send.send_xmpp(report)
    #jabber_send.send_xmpp("\n".join(posts))

if posts:
    p = subprocess.Popen(['./xsend.py', report],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    output, err = p.communicate()
    print(output, err)

pp.pprint(report)

