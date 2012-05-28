FU!
---
DNSBL checking SMTPD-Proxy

Example Configuration File
==========================
::

    settings:
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
