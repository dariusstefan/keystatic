---
title: "OpenSIPS Tools"
description: "This list contains a few tools which can be used in setting up or testing your OpenSIPS installation."
---

This list contains a few tools which can be used in setting up or testing your **OpenSIPS** installation.

---

## m4
Included on most Linuxes. This is a simple way to set up and use separate parameter files or even a good way of accomplishing INCLUDE's in your configs.
Example of usage is provided by Iñaki Baz Castillo;
```c

I strongly recommend you to use M4 to compile your opensips.cfg file:

file /etc/opensips/opensips.cfg.m4:
---------------------------------------------
debug=3
log_stderror=no
log_facility=LOG_LOCAL7
fork=yes
...
listen=MY_IP:MY_PORT
...
    rewritehost("MEDIA_SERVER_IP:MEDIA_SERVER_PORT");
...
---------------------------------------------

file /etc/opensips/defines.m4 (at your home):
---------------------------------------------
divert(-1)
define(`MY_IP',		`192.168.10.23')
define(`MY_PORT',		`5060')
define(`MEDIA_SERVER_IP',   `192.168.10.23')
define(`MEDIA_SERVER_PORT', `5065')
divert(0)dnl
---------------------------------------------

file /etc/opensips/defines.m4 (at your office):
---------------------------------------------
divert(-1)
define(`MY_IP',		`123.123.123.123')
define(`MY_PORT',		`5060')
define(`MEDIA_SERVER_IP',	`22.22.22.22')
define(`MEDIA_SERVER_PORT',	`5065')
divert(0)dnl
---------------------------------------------

Create a bash script:
/usr/local/bin/op-restart.sh:
----------------------------------------------
#!/bin/bash
DIR="/etc/opensips"
m4 $DIR/defines.m4 $DIR/opensips.cfg.m4 > $DIR/opensips.cfg
/etc/init.d/opensips restart
----------------------------------------------

So you just must change the /etc/opensips/opensips.cfg.m4 file and the
defines.m4 (this last file will be different depending on your location).

```

---

## ngrep
```bash

### capture all SIP packages on 5060 on all interfaces
ngrep -W byline -td any . port 5060

### capture all SIP packages containing 'username' on port 5060 on all interfaces
ngrep -W byline -tqd any username port 5060

```

---

## SIPp

---

## tshark
```bash

### Filter on RTCP packets reporting any packet loss or jitter over 30ms:
tshark -i eth0 -o "rtcp.heuristic_rtcp: TRUE" -R 'rtcp.ssrc.fraction >= 1 or rtcp.ssrc.jitter >= 30' -V

### View a remote realtime capture with a local wireshark:
wireshark -k -i <(ssh -l root 192.168.10.98 tshark -w - not tcp port 22)

```

---

## sipviewer

---

## sipana

---

## pcapsipdump

pcapsipdump is libpcap-based SIP sniffer with per-call sorting capabilities. It writes SIP/RTP sessions to disk in a same format, as "tcpdump -w", but one file per SIP session (even if there is thousands of concurrent SIP sessions). 

WEB page http://pcapsipdump.sourceforge.net/

---

## sipscenario

---

## the "siptrace" table
Don't forget the sip_trace() command (in module http://www.opensips.org/html/docs/modules/1.4.x/siptrace.html )

(Maybe some clever usage for something other than just plain searching it (like an integration with sipscenario))

---

## sipinspector
->http://sites.google.com/site/sipinspectorsite/

---

## Resync/reboot Linksys phones

PhPSIP UA for sending a NOTIFY to resync/reboot Linksys phone. The tool can authenticate (SIP digest) against the Linksys phone.

->http://code.google.com/p/php-sip/

---

## Nagios memory check plugin

->http://level7systems.co.uk/en/blog/OpenSIPs+memory+check+in+Nagios
