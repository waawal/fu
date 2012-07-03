=====================================
FU - The Funneling Unit
=====================================
:Info: Read the `documentation <http://fu.readthedocs.com>`_ hosted at readthedocs.
:Author: Daniel Waardal

*DNSBL* checking *SMTP-Proxy*

FU is a simple yet powerful SMTP Proxy that checks the incoming connections against a list of preconfigured DNSBL's. Based on the weights assigned to the lists and a threshhold it makes a decision weather it should proxy the email to the upstream or hang up (close) the connection.

FU is optimized to run in a virtual machine environment. It should be able to handle a couple of hundred incoming connections per second on a single core system/vm.

Features
========

* Round Robin Load Balancing of Backends.
* Ability to check multiple blacklists.

Options and Arguments
==========================

Options accepted by the ``fu`` command.

-h, --help
  Show a help message and exit.
-c, --configuration
  Configuration file.
-t, --test
  A IPv4-address to run a test against based on the provided configuration file.

Examples
========

Configuration File
------------------
::

    settings:
        loglevel: notice
        predicate: 2
        threshhold: 1.0
        bind:
            localhost: 2525
        upstream:
            - localhost: 1026
            - localhost: 1025
            

    providers:
        bl.spamcop.net: {weight: 0.3}
        ix.dnsbl.manitu.net: {weight: 1.0}
        rhsbl.ahbl.org: {weight: 0.3}
        truncate.gbudb.net: {weight: 1.0}
        zen.spamhaus.org: {weight: 0.5}

Example of a Dry Run
--------------------
::

    $fu --configuration /etc/fu.yml --test 201.8.3.1
    DEBUG:root:1.3.8.201.ix.dnsbl.manitu.net. Not resolvable. NOT SPAM!
    DEBUG:root:1.3.8.201.truncate.gbudb.net. Not resolvable. NOT SPAM!
    DEBUG:root:1.3.8.201.rhsbl.ahbl.org. Not resolvable. NOT SPAM!
    DEBUG:root:DNSBL reply: 127.0.0.11 > result: 11.
    INFO:root:Positive reply from zen.spamhaus.org appending 0.5
    DEBUG:root:1.3.8.201.bl.spamcop.net. Not resolvable. NOT SPAM!
    INFO:root:0.5 is below the threshhold (1.0)

Installation and Deployment
===========================

FU is dependent on gevent to harness the power of libevent.

Debian and Ubuntu
-----------------

A one-liner to install on a fresh system.
::

    sudo apt-get update; sudo apt-get install python-pip python-gevent python-yaml; sudo pip install fu

*You then need to create the configuration file.*

References
==========

* `RFC5782 <http://tools.ietf.org/html/rfc5782>`_
* `Wikipedia Comparison of DNS blacklists <http://en.wikipedia.org/wiki/Comparison_of_DNS_blacklists>`_
