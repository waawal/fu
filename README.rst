FU!
---

**DNSBL** checking *SMTPD-Proxy*

FU is a simple yet powerful SMTP Proxy that checks the incoming connections against preconfigured DNSBL's. Based on weights and threshholds it then decides weather it should proxy the email to the upstream or hang up (close) the connection.

FU is optimized to run in a virtual machine environment. It should be able to handle a couple of hundred incoming connections per second on a single core system/vm.

Features
========

* Round Robin Load Balancing of Backends.
* Ability to check several blacklists.

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
