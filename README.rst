FU!
===

The **F**unneling **U**nit

**DNSBL** checking *SMTP-Proxy*

FU is a simple yet powerful SMTP Proxy that checks the incoming connections against a list of preconfigured DNSBL's. Based on the weights assigned to the lists and a threshhold it makes a decision weather it should proxy the email to the upstream or hang up (close) the connection.

FU is optimized to run in a virtual machine environment. It should be able to handle a couple of hundred incoming connections per second on a single core system/vm.

Features
--------

* Round Robin Load Balancing of Backends.
* Ability to check several blacklists.

Deployment
==========

FU is dependent on gevent to harness the power of libevent. You may of course pip-install fu as a normal python application/module, however it is usually easier to just fetch gevent from the OS package repository.

Debian and Ubuntu
-----------------

    ``sudo`` ``apt-get`` install python-pip python-gevent python-yaml; ``pip`` install fu


Example Configuration File
==========================
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
