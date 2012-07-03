""" DNSBL checking SMTPD-Proxy """

import sys
import argparse
import pprint
import itertools
import collections
import logging

try:
    import gevent.monkey
    gevent.monkey.patch_select()
    gevent.monkey.patch_socket()
except ImportError:
    pass

import asyncore
import socket
from smtpd import PureProxy, SMTPChannel


def check(zone, predicate=2):
    """ Checks if the name resolves and if the last part of the reply is
        >= the predicate.
    """
    try:
        reply = socket.gethostbyname(zone)
        result = int(reply.split('.')[-1])
        logging.debug('DNSBL reply: {0} > result: {1}.'.format(reply, result))
        return  result >= predicate
    except (socket.error, ValueError):
        logging.debug('{0} Not resolvable.'.format(zone))
        return False

def as_reversed(ip, suffix):
    """ *Reverses* the ipv4 so that it can be checked
        >>> as_reversed(ip='89.218.52.234', suffix='ix.dnsbl.manitu.net')
        '234.52.218.89.ix.dnsbl.manitu.net.'
    """
    reverse = '.'.join(reversed(ip.split('.')))
    logging.debug('{ip}, {suffix} reversed to: {reverse}.{suffix}.'.format(
                  **locals()))
    return '{reverse}.{suffix}.'.format(reverse=reverse, suffix=suffix)

def is_spam(ip, provider, predicate=2):
    """ Returns either True or False depending on if the last digits in the
        reply is >= the predicament. 2 is the default as per RFC.
    """
    try:
        ip = socket.gethostbyname(ip) # returns ip
    except socket.error:
        logging.debug('No address associated with hostname.')
        return True # No address associated with hostname.

    zone = as_reversed(ip, provider)
    return check(zone, predicate)

def check_lists(providers):
    results = []
    for domain, provider in providers.items():
        if is_spam(ip, domain, self.predicate):
            weight = provider.get('weight', 0.0)
            results.append(weight)
            logging.info('Positive reply from {0} appending {1}'.format(
                       domain, weight))
    return results


class FuProxy(object, PureProxy):
    """ The Proxy, subclass of PureProxy.
    """
    def __init__(self, binding, upstreams, providers,
                 predicate=2, threshhold=1.0):
        logging.info('Initiating FU Proxy Server')
        self.upstreams = itertools.cycle(upstreams)
        PureProxy.__init__(self, binding, self.upstreams.next())
        self.providers = providers
        self.predicate = predicate
        self.threshhold = threshhold
        logging.info('Initialized.')

    def handle_accept(self):
        """ Checks the incoming connection against the configured DNSBL's.
            if the result is >= than the preconfigured threshhold,
            the connection gets closed.
        """
        pair = self.accept()
        if pair is not None:
            conn, addr = pair
            ip, port = addr
            logging.info('Incoming connection from {0}:{1}'.format(ip, port))
            
            results = check_lists(self.providers)

            if float(sum(results)) < float(self.threshhold):
                logging.info('{0} is below the threshhold ({1})'.format(
                          sum(results), self.threshhold))
                self._remoteaddr = self.upstreams.next()
                logging.info('Relaying message to {0}'.format(self._remoteaddr))
                channel = SMTPChannel(self, conn, addr)
            else:
                logging.info('{0} is over the threshhold {1} - SPAM!'.format(
                          sum(results), self.threshhold))
                conn.close()


def main(configurationfile):
    """ Parses the passed in configuration file-path with yaml.
    """
    import yaml
    stream = file(configurationfile, 'r')
    configuration = yaml.load(stream)
    LEVELS = {'debug':logging.DEBUG,
              'info':logging.INFO,
              'warning':logging.WARNING,
              'error':logging.ERROR,
              'critical':logging.CRITICAL,}
    
    settings = configuration.get('settings')
    providers = configuration.get('providers')
    
    if not settings:
        print "Error: No settings found in the configuration file."
        sys.exit(1)
    if settings.get('loglevel').lower() in LEVELS.keys():
        logging.basicConfig(level=LEVELS[settings['loglevel']])
    else:
        logging.basicConfig(level=logging.NOTSET)
    
    logging.debug('\nLoaded Configuration:\n' + pprint.pformat(configuration))
    
    predicate = settings.get('predicate', 2)
    threshhold = settings.get('threshhold', 1.0)
    binding = settings.get('bind', {'0.0.0.0': 25}).items()[0]
    upstream = [item.items()[0] for item in settings['upstream']]
    
    server = FuProxy(binding, upstream, providers, predicate, threshhold)
    
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        logging.critical('Interrupted. Cleaning up!')

def dispatch():
    """ Dispatching of commandline arguments to main(), the entry point for
        scripts.
    """
    parser = argparse.ArgumentParser(description='DNSBL SMTPD')
    parser.add_argument('configuration', metavar='configuration', type=str,
                        help='Configuration File in YAML-format.')
    args = parser.parse_args()
    
    main(args.configuration)

if __name__ == '__main__':
    dispatch()
