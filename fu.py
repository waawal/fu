""" DNSBL checking SMTPD-Proxy """

import sys
import argparse
import pprint
from itertools import cycle

import gevent.monkey
gevent.monkey.patch_select()
gevent.monkey.patch_socket()

import asyncore
import socket
from smtpd import PureProxy, SMTPChannel


import yaml
from logbook import Logger


log = Logger('FU')

def check(zone, predicate=2):
    """ Checks if the name resolves and if the last part of the reply is
        >= the predicate.
    """
    try:
        reply = socket.gethostbyname(zone)
        result = int(reply.split('.')[-1])
        log.debug('DNSBL reply: {0} > result: {1}.'.format(reply, result))
        return  result >= predicate
    except (socket.error, ValueError):
        log.debug('{0} Not resolvable.'.format(zone))
        return False

def as_reversed(ip, suffix):
    """ *Reverses* the ipv4 so that it can be checked
        >>> as_reversed(ip='89.218.52.234', suffix='ix.dnsbl.manitu.net')
        '234.52.218.89.ix.dnsbl.manitu.net.'
    """
    reverse = '.'.join(reversed(ip.split('.')))
    log.info('{ip}, {suffix} reversed to: {reverse}.{suffix}.'.format(
             **locals()))
    return '{reverse}.{suffix}.'.format(reverse=reverse, suffix=suffix)

def is_spam(ip, provider, predicate=2):
    """ Returns either True or False depending on if the last digits in the
        reply is >= the predicament. 2 is the default as per RFC.
    """
    try:
        ip = socket.gethostbyname(ip) # returns ip
    except socket.error:
        log.debug('No address associated with hostname.')
        return True # No address associated with hostname.

    zone = as_reversed(ip, provider)
    return check(zone, predicate)


class FuProxy(object, PureProxy):

    def __init__(self, binding, upstreams, providers,
                 predicate=2, threshhold=1.0):
        log.notice('Initiating FU Proxy Server')
        self.upstreams = cycle(upstreams)
        PureProxy.__init__(self, binding, self.upstreams.next())
        self.providers = providers
        self.predicate = predicate
        self.threshhold = threshhold
        log.notice('Initiated.')

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            conn, addr = pair
            ip, port = addr
            log.notice('Incoming connection from {0} port {1}'.format(ip, port))
            results = []
            for domain, provider in self.providers.items():
                if is_spam(ip, domain, self.predicate):
                    weight = provider.get('weight', 0.0)
                    results.append(weight)
                    log.notice('Positive reply from {0} appending {1}'.format(
                               domain, weight))

            if float(sum(results)) < float(self.threshhold):
                log.notice('{0} is below the threshhold ({1})'.format(
                          sum(results), self.threshhold))
                self._remoteaddr = self.upstreams.next()
                log.notice('Relaying message to {0}'.format(self._remoteaddr))
                channel = SMTPChannel(self, conn, addr)
            else:
                log.notice('{0} is over the threshhold ({1}). Closing!'.format(
                          sum(results), self.threshhold))
                conn.close()


def main(configurationfile):
    stream = file(configurationfile, 'r')
    configuration = yaml.load(stream)
    log.debug('\nLoaded Configuration:\n' + pprint.pformat(configuration))
    settings = configuration.get('settings')
    providers = configuration.get('providers')
    if not settings or not providers:
        sys.exit(1)
    predicate = settings.get('predicate', 2)
    threshhold = settings.get('threshhold', 1.0)
    binding = settings['bind'].items()[0]
    upstream = [pair.items()[0] for pair in settings['upstream']]
    server = FuProxy(binding, upstream, providers,
                     predicate, threshhold)
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        log.critical('Interrupted.')
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='DNSBL SMTPD')
    parser.add_argument('configuration', metavar='configuration', type=str,
                        help='Configuration File in YAML-format.')
    args = parser.parse_args()
    main(args.configuration)
