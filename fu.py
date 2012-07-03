""" DNSBL checking SMTPD-Proxy on gevent steroids """


__all__ = ('resolve', 'as_reversed', 'check_lists', 'is_spam')


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


def resolve(zone):
    """ Checks if the name resolves and if the last part of the reply is
        >= the predicate.
        
       :param zone: A valid zone for lookup ex: '234.52.218.89.ix.dnsbl.manitu.net.'
       :type zone: string
       :rtype: integer
    """
    try:
        reply = socket.gethostbyname(zone)
        result = int(reply.split('.')[-1])
        logging.debug('DNSBL reply: {0}'.format(result))
        return  result >= predicate
    except (socket.error, ValueError):
        logging.debug('Negative response from {0}'.format(zone))
        return False

def as_reversed(ip, suffix):
    """ *Reverses* the ipv4 so that it can be checked
        >>> as_reversed(ip='89.218.52.234', suffix='ix.dnsbl.manitu.net')
        '234.52.218.89.ix.dnsbl.manitu.net.'
        
        :param ip: A IPv4 address.
        :type ip: string
        :param suffix: The FQDN of the DNSBL Provider.
        :type predicate: string
        :rtype: string
    """
    reverse = '.'.join(reversed(ip.split('.')))
    return '{reverse}.{suffix}.'.format(reverse=reverse, suffix=suffix)

def is_spam(ip, provider, predicate=2):
    """ Returns either True or False depending on if the last digits in the
        reply is >= the predicament. 2 is the default as per RFC.
        
        :param ip: A IPv4 address to be checked.
        :type ip: string
        :param provider: The FQDN of the DNSBL Provider.
        :type provider: string
        :param predicate: The DNSBL-reply must be equal to this or higher.
        :type predicate: integer
        :rtype: bool
    """
    zone = as_reversed(ip, provider)
    return resolve(zone) >= predicate

def check_lists(ip, providers, threshhold, predicate=2):
    """ Checks a ip against a list of DNSBL providers.
        
        :param ip: A IPv4 address to be checked.
        :type ip: string
        :param providers: A mapping (dict) containing FQDN's as keys and weights as values (floats).
        :type providers: Mapping
        :param threshhold: If the combined results >= this value, we deem it as spam.
        :type threshhold: float
        :param predicate: The DNSBL-reply must be equal to this or higher.
        :type predicate: integer
        :rtype: bool
    """
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
    """ The Proxy, subclass of smptd.PureProxy.
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
            if the result is >=  self.threshhold, the connection gets closed.
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
