#!/usr/bin/python
'''Get last day upvoted report and send over xmpp'''
import os
import pprint
import json
import time

import redis
import yaml

import jabber_send

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

report = "For last 24h\n "
report += "%.1f rate limit\n" % float(rdb.get(PRE + "limit"))
report += "%s posts with authors:\n" % len(posts)
report += ", ".join(str(s) for s in authors)

if posts:
    jabber_send.send_xmpp(report)
    #jabber_send.send_xmpp("\n".join(posts))

pp.pprint(report)

