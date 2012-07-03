""" DNSBL checking SMTPD-Proxy """

import sys
import argparse
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


def resolve(zone, predicate=2):
    """ Checks if the name resolves and if the last part of the reply is
        >= the predicate.
    """
    try:
        reply = socket.gethostbyname(zone)
        result = int(reply.split('.')[-1])
        logging.debug('DNSBL reply: {0} (Predicate is: {1}).'.format(result,
                                                                     predicate))
        return  result >= predicate
    except (socket.error, ValueError):
        logging.debug('Negative response from {0}'.format(zone))
        return False

def as_reversed(ip, suffix):
    """ *Reverses* the ipv4 so that it can be checked
        >>> as_reversed(ip='89.218.52.234', suffix='ix.dnsbl.manitu.net')
        '234.52.218.89.ix.dnsbl.manitu.net.'
    """
    reverse = '.'.join(reversed(ip.split('.')))
    return '{reverse}.{suffix}.'.format(reverse=reverse, suffix=suffix)

def is_spam(ip, provider, predicate=2):
    """ Returns either True or False depending on if the last digits in the
        reply is >= the predicament. 2 is the default as per RFC.
    """
    zone = as_reversed(ip, provider)
    return resolve(zone, predicate)

def check_lists(ip, providers, threshhold, predicate=2):
    results = []
    for provider, settings in providers.items():
        if is_spam(ip, provider, predicate):
            weight = settings.get('weight', 0.0)
            results.append(weight)
            logging.info('Positive response from {0} adding {1} to weight'.format(
                          provider, weight))
    if float(sum(results)) > float(threshhold):
        logging.info('{0} is above the threshhold ({1}) - SPAM!'.format(
                     sum(results), threshhold))
        return True
    logging.info('{0} is below the threshhold ({1}) - NOT SPAM!'.format(
                 sum(results), threshhold))
    return False


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
            
            spam = check_lists(ip, self.providers, self.threshhold,
                               self.predicate)

            if spam:
                conn.close()
            else:
                self._remoteaddr = self.upstreams.next()
                logging.info('Relaying message to {0}'.format(self._remoteaddr))
                channel = SMTPChannel(self, conn, addr)


def main(configurationfile, dryrun=False):
    """ Parses the passed in configuration file-path with yaml.
    """
    import yaml
    stream = file(configurationfile, 'r')
    configuration = yaml.load(stream)


    settings = configuration.get('settings')
    providers = configuration.get('providers')

    if not settings:
        print "Error: No settings found in the configuration file."
        sys.exit(1)

    predicate = settings.get('predicate', 2)
    threshhold = settings.get('threshhold', 1.0)
    binding = settings.get('bind', {'0.0.0.0': 25}).items()[0]
    upstream = [item.items()[0] for item in settings['upstream']]

    if not dryrun:
        FORMAT = "%(levelname)s %(asctime)s %(message)s"
        LEVELS = {'debug':logging.DEBUG,
                  'info':logging.INFO,
                  'warning':logging.WARNING,
                  'error':logging.ERROR,
                  'critical':logging.CRITICAL,}
        if settings.get('loglevel').lower() in LEVELS.keys():
            logging.basicConfig(level=LEVELS[settings['loglevel']], format=FORMAT)
        else:
            logging.basicConfig(level=logging.NOTSET, format=FORMAT)

        server = FuProxy(binding, upstream, providers, predicate, threshhold)
        try:
            asyncore.loop()
        except KeyboardInterrupt:
            logging.critical('Interrupted. Cleaning up!')
    else:
        FORMAT = "%(message)s"
        logging.basicConfig(level=logging.DEBUG, format=FORMAT)
        check_lists(dryrun, providers, threshhold, predicate)

def dispatch():
    """ Dispatching of commandline arguments to main(), the entry point for
        scripts.
    """
    parser = argparse.ArgumentParser(description='DNSBL SMTPD')
    parser.add_argument('-c', '--configuration',
                        metavar='configuration', type=str,
                        help='Configuration File in YAML-format.')
    parser.add_argument('-t', '--test', metavar='test', type=str, default='',
                        help='A IPv4 address to test for false positives')
    args = parser.parse_args()
    main(args.configuration, args.test)

if __name__ == '__main__':
    dispatch()
