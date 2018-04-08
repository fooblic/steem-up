#!/usr/bin/python3
'''
Source:
https://dev.gajim.org/gajim/python-nbxmpp/raw/master/doc/examples/xsend.py
'''
import sys
import logging
import yaml

import nbxmpp
try:
    from gi.repository import GObject as gobject
except Exception:
    import gobject

consoleloghandler = logging.StreamHandler()
root_log = logging.getLogger('nbxmpp')
#root_log.setLevel('DEBUG')
root_log.addHandler(consoleloghandler)

if len(sys.argv) < 1:
    print("Syntax: xsend text")
    sys.exit(0)

text = ' '.join(sys.argv[1:])

config_file = "/etc/jabber_ru.yml"
try:
    Conf = yaml.load( open(config_file) )
    jidparams = { 'jid': Conf["username"], 'password': Conf["password"] }
    to_jid = Conf["contact"]
except:
    print("Error jabber config %s" % config_file)
    sys.exit(0)
    
class Connection:
    def __init__(self):
        self.jid = nbxmpp.protocol.JID(jidparams['jid'])
        self.password = jidparams['password']
        self.sm = nbxmpp.Smacks(self) # Stream Management
        self.client_cert = None

    def on_auth(self, con, auth):
        if not auth:
            print('could not authenticate!')
            sys.exit()
        print('authenticated using ' + auth)
        self.send_message(to_jid, text)

    def on_connected(self, con, con_type):
        print('connected with ' + con_type)
        auth = self.client.auth(self.jid.getNode(), self.password, resource=self.jid.getResource(), sasl=1, on_auth=self.on_auth)

    def get_password(self, cb, mech):
        cb(self.password)

    def on_connection_failed(self):
        print('could not connect!')

    def _event_dispatcher(self, realm, event, data):
        pass

    def connect(self):
        idle_queue = nbxmpp.idlequeue.get_idlequeue()
        self.client = nbxmpp.NonBlockingClient(self.jid.getDomain(), idle_queue, caller=self)
        self.con = self.client.connect(self.on_connected, self.on_connection_failed, secure_tuple=('tls', '', '', None, None),
                                       hostname = Conf["server"],
                                       port = Conf["port"])

    def send_message(self, to_jid, text):
        id_ = self.client.send(nbxmpp.protocol.Message(to_jid, text, typ='chat'))
        print('sent message with id ' + id_)
        gobject.timeout_add(1000, self.quit)

    def quit(self):
        self.disconnect()
        ml.quit()

    def disconnect(self):
        self.client.start_disconnect()


con = Connection()
con.connect()
ml = gobject.MainLoop()
ml.run()

