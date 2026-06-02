---
title: "OpenSIPS FreeSwitch Integration"
description: "This tutorial can be used as a cut and paste complete and working installation. Please follow strictly all the steps, in the order given."
---

## Realtime **OpenSIPS - FreeSWITCH** Integration
**Author `Giovanni Maruzzelli <gmaruzz at gmail dot com>`**

**This tutorial is made for OpenSIPS 1.8.x and FreeSWITCH 1.2.x**

---

### Scope

This tutorial can be used as a cut and paste complete and working installation. Please follow strictly all the steps, in the order given.

This tutorial presents the concept and implementation of a realtime integration of OpenSIPS SIP server and FreeSWITCH media server.

OpenSIPS is used a SIP server - users are registering with it, it routes calls, etc - while the purpose of FreeSWITCH is to provide a full set of media services - like voicemail, conference, announcements, etc.

It is a realtime integration because both OpenSIPS and FreeSWITCH are provisioned in the same time when comes to user accounts - when creating a new OpenSIPS user, automatically FreeSWITCH will learn about it an provide and configure all necessary  media services for it.

Both OpenSIPS and FreeSWITCH will be provisioned (for user accounts) via a shared mysql database.

All FreeSWITCH functionalities will be available to OpenSIPS users by prefixing "*" (eg: star) to the extension dialed. *1234 will be passed to FreeSWITCH as 1234, while **1234 will be passed to FreeSWITCH as *1234

---

### Setup presentation

This tutorial can be used as a cut and paste complete and working installation. Please follow strictly all the steps, in the order given.

The following services will be offered by FreeSWITCH by this integrated configuration:

* **voicemail** - users will get access to their mailbox; authentication will be done by OpenSIPS; while FreeSWITCH will only provide voicemail IVR (with access PIN);
* **conference**' - OpenSIPS will detect and forward calls related to conference service (based on prefixes) to FreeSWITCH, which will provide access (pin based) to the conference rooms;

* **all functionalities** - OpenSIPS users will prefix * to reach the corresponding extension in FreeSWITCH (*1234 will be passed to FreeSWITCH as 1234, while **1234 will be passed to FreeSWITCH as *1234)

## Installation and First Configuration

---

### Install Linux

Start from a fresh Debian 6 (Squeeze) base install, bring in the latest updates and reboot

```bash

apt-get clean
apt-get update
apt-get upgrade
apt-get dist-upgrade
reboot

```

---

### Install the prerequisites

```bash

apt-get install build-essential \
                subversion automake autoconf wget  libtiff4-dev libtool \
                libncurses5-dev git-core libcurl4-openssl-dev libjpeg-dev \
                mysql-server libmysqlclient-dev mysql-client \
                unixodbc-dev unixodbc libmyodbc flex bison libncurses-dev \
                build-essential openssl bison flex perl libdbi-perl \
                libdbd-mysql-perl libdbd-pg-perl libfrontier-rpc-perl \
                libterm-readline-gnu-perl libberkeleydb-perl ncurses-dev \
                libpcre3-dev libxml2-dev libxmlrpc-c-dev libpcre3 libxml2 \
                perl libdbi-perl libdbd-mysql-perl libfrontier-rpc-perl \
                libterm-readline-gnu-perl libberkeleydb-perl apache2 \
                libapache2-mod-php5 php5 php5-cli php5-gd php5-mysql php-pear \
                php5-xmlrpc

```

---

### Compile and install OpenSIPS

```bash

cd /usr/src
svn co https://opensips.svn.sourceforge.net/svnroot/opensips/branches/1.8 opensips_1_8

cd opensips_1_8
make menuconfig

```

Go to 'Configure Compile Options' and then 'Configure Excluded Modules'. Select the db_mysql, db_unixodbc, dialplan, mi_xmlrpc, presence*, pua*, regex modules with the spacebar key, then hit the 'q' key. Go to 'Configure Install Prefix' and set the prefix to /usr/local/opensips . Hit 'Save Changes' and then compile and install OpenSIPS.

---

### Create OpenSIPS Database and Configuration File

```text

cd /usr/local/opensips/etc/opensips/
vi opensipsctlrc

```

modify like the follow (you'll find in the next section the file ready to be copied and pasted).

```bash

# this parameter.
DBENGINE=MYSQL

## database host
DBHOST=localhost

## database name (for ORACLE this is TNS name)
DBNAME=opensips

# database path used by dbtext or db_berkeley
# DB_PATH="/usr/local/etc/opensips/dbtext"

## database read/write user
DBRWUSER=opensips

## password for database read/write user
DBRWPW="mydbpassword"

## database super user (for ORACLE this is 'scheme-creator' user)
DBROOTUSER="root"

```

then create the database

```text

cd ../..
cd sbin
./opensipsdbctl create

```

you can then check database creation success with

```text

mysql -D opensips -p

```

then create the OpenSIPS configuration file

```text

./osipsconfig

```

Go to 'Generate OpenSIPS Script' and then to 'Residential Script', 'Configure Residential Script'.
Add ENABLE_TCP, USE_ALIASES, USE_AUTH, USE_DBACC, USE_DBUSRLOC, USE_DIALOG, USE_DIALPLAN, VM_DIVERSION

Hit 'q' and then go to 'Generate Residential Script', which will generate a CFG file in your install path, in the /usr/local/opensips/etc/opensips/ folder.

Change its name, and edit it (you'll find in the next section the file ready to be copied and pasted).

```text

cd ../etc/opensips
mv opensips_residential_2012-12-19_8\:51\:27.cfg opensips_residential_01.cfg

vi opensips_residential_01.cfg

```

Follow this guidelines

```c

#follow CUSTOMIZE ME
# modify db password

# modify
$du = "sip:127.0.0.2:5060"; # CUSTOMIZE ME
#to
$du = "sip:192.168.1.110:5090"; # CUSTOMIZE ME

#modify mpath to /usr/local/opensips/lib64/opensips/modules/

#modify from
#### URI module
loadmodule "uri.so"
modparam("uri", "use_uri_table", 0)

#to
#### URI module
loadmodule "uri.so"
modparam("uri", "use_uri_table", 0)
modparam("uri", "db_url",
                "mysql://opensips:mydbpassword@localhost/opensips") # CUSTOMIZE ME

```

(you'll find in the next section the file ready to be copied and pasted)

### Install OpenSIPS init files

then install and edit OpenSIPS init script

```bash

cd /usr/src/opensips_1_8/
cd packaging/
cd debian
cp opensips.init /etc/init.d/opensips
chmod +x /etc/init.d/opensips
vi /etc/init.d/opensips

```

change the following lines, with the correct location of OpenSIPS executable, comment out those lines for debug, and edit the OPTIONS line as instructed

```bash

DAEMON=/usr/local/opensips/sbin/opensips #CUSTOMIZE

#comment out if [ "$1" != "debug" ]; then
#comment out check_fork
#comment out fi

# edit OPTIONS adding -f config-file
OPTIONS="-P $PIDFILE -m $S_MEMORY -M $P_MEMORY -u $USER -g $GROUP -f /usr/local/opensips/etc/opensips/opensips_residential_01.cfg"

```

then edit the accessory files

```text

cp opensips.default /etc/default/opensips
vi /etc/default/opensips

```

edit it as in

```text

RUN_OPENSIPS=yes
USER=root
GROUP=root
S_MEMORY=128

```

edit the system logger configuration file so to instruct it to convey OpenSIPS info to the right file

```text

vi /etc/rsyslog.conf

```

add at file's end:

```text

local1.* -/var/log/opensips.log

```

then restart the syslogger and OpenSIPS

```text

/etc/init.d/rsyslog restart
/etc/init.d/opensips start

```

---

### Install OpenSIPS Control Panel

This is a web configuration and management tool we will use to manage all our platform, both OpenSIPS and FreeSWITCH (eg we'll manage OpenSIPS, actually, but FreeSWITCH will source its user management data from the same database used by OpenSIPS and managed with OpenSIP-CP).

```text

cd /var/www
svn co https://opensips-cp.svn.sourceforge.net/svnroot/opensips-cp/trunk opensips-cp

pear install mdb2
pear install mdb2#mysql

cd opensips-cp
vi config/db.inc.php

```

edit it like this:

```text

//database connection user
$config->db_user = "opensips"; //CUSTOMIZE

//database connection password
$config->db_pass = "mydbpassword"; //CUSTOMIZE

```

then edit the other config files

```text

vi config/boxes.global.inc.php

```

make it like this:

```text

//## use fifo
//$boxes[$box_id]['mi']['conn']="127.0.0.1:8000";
$boxes[$box_id]['mi']['conn']="/tmp/opensips_fifo";

//#comment out with double slashes monit stuff
// monit host:port
//$boxes[$box_id]['monit']['conn']="192.168.0.1:2812";
//$boxes[$box_id]['monit']['user']="admin";
//$boxes[$box_id]['monit']['pass']="pass";
//$boxes[$box_id]['monit']['has_ssl']=1;

```

```text

vi config/tools/system/dialog/local.inc.php

```

make it like this:

```text

$box[1]['mi']['conn']="/tmp/opensips_fifo";;

```

```text

vi config/tools/system/dispatcher/local.inc.php

```

make it like this:

```text

$box[1]['mi']['conn']="/tmp/opensips_fifo";

```

then add an alias to the apache configuration

```text

vi /etc/apache2/apache2.conf

```

add at end of the file:
```text

Alias /cp /var/www/opensips-cp/web

```

then change the ownership of the files, do the logging part and the CDR related editing

```bash

chown www-data.www-data /var/www/opensips-cp/config/access.log
pear install log

mysql -Dopensips -p < config/tools/admin/add_admin/ocp_admin_privileges.mysql
mysql -Dopensips -p -e "INSERT INTO ocp_admin_privileges (username,password,ha1,available_tools,permissions) values
       ('admin','admin',md5('admin:admin'),'all','all');"
mysql -Dopensips -p < config/tools/system/cdrviewer/cdrs.mysql
mysql -Dopensips -p < config/tools/system/cdrviewer/opensips_cdrs.mysql
mysql -Dopensips -p < config/tools/system/smonitor/tables.mysql

vi /var/www/opensips-cp/cron_job/generate-cdrs_mysql.sh

```

edit to look like:

```text

mysql -h $HOSTNAME -u $USER -p$PASS -e "call opensips_cdrs(); " $DATABASE

```

then activate the CDR cronjob

```text

vi /etc/crontab

```

add the following lines to it

```text

*/3 * * * * root /var/www/opensips-cp/cron_job/generate-cdrs_mysql.sh
* * * * *   root   php /var/www/opensips-cp/cron_job/get_opensips_stats.php > /dev/null

```

and restart both apache and OpenSIPS

```text

/etc/init.d/apache2 restart
/etc/init.d/opensips restart
/etc/init.d/cron restart

```

---

### FreeSWITCH compile and install

Let's install FreeSWITCH and go for a coffee in the while (will take time)

```bash

cd /usr/src
git clone -b v1.2.stable git://git.freeswitch.org/freeswitch.git
cd freeswitch/

./bootstrap.sh && ./configure && make && make install && make hd-sounds-install && make hd-moh-install && make samples

```

---

### FreeSWITCH listening ports

Edit the SIP ports for FreeSWITCH

```text

vi /usr/local/freeswitch/conf/vars.xml

```

to be

```text

<X-PRE-PROCESS cmd="set" data="internal_sip_port=5090"/>
<X-PRE-PROCESS cmd="set" data="external_sip_port=5091"/>

```

---

### Install OpenSIPS and FreeSWITCH configs and database script, and ODBC configs

Back up the original files for your reference

```text

cp /usr/local/opensips/etc/opensips/opensipsctlrc /usr/local/opensips/etc/opensips/opensipsctlrc.originale
cp /usr/local/freeswitch/conf/dialplan/public.xml /usr/local/freeswitch/conf/dialplan/public.xml.original
cp /usr/local/freeswitch/conf/vars.xml /usr/local/freeswitch/conf/vars.xml.original
cp /usr/local/freeswitch/conf/autoload_configs/modules.conf.xml /usr/local/freeswitch/conf/autoload_configs/modules.conf.xml.original
cp /usr/local/freeswitch/conf/autoload_configs/lua.conf.xml /usr/local/freeswitch/conf/autoload_configs/lua.conf.xml.original
cp /usr/local/freeswitch/conf/autoload_configs/acl.conf.xml /usr/local/freeswitch/conf/autoload_configs/acl.conf.xml.original
cp /etc/odbcinst.ini /etc/odbcinst.ini.original
cp /etc/odbc.ini /etc/odbc.ini.original

```

Files' content follows, but first the files' list:

```text

/usr/local/opensips/etc/opensips/opensipsctlrc
/usr/local/opensips/etc/opensips/opensips_residential_01.cfg
/usr/local/freeswitch/conf/dialplan/public.xml
/usr/local/freeswitch/scripts/config.lua
/usr/local/freeswitch/scripts/xml_handler.lua
/usr/local/freeswitch/conf/vars.xml
/usr/local/freeswitch/conf/autoload_configs/modules.conf.xml
/usr/local/freeswitch/conf/autoload_configs/lua.conf.xml
/usr/local/freeswitch/conf/autoload_configs/acl.conf.xml
/etc/odbcinst.ini
/etc/odbc.ini

```

You will copy and paste each one the files, overwriting the existing ones you just backed-up.

## Scripts and Configuration files you can Copy and Paste, with explanations

Below the files' content, with some explanation, file by file.

You copy and paste each one the following files, overwriting the existing ones (you just made a backup of them).

Then you can change them to your like, eg: changing the "mydbpasswd" password and the IP addresses.

The files as they are here compose a working installation, provided you followed this tutorial step by step, and you use the same IP addresses.

All that has been changed from original installed files is marked as "CUSTOMIZE"

Follow "CUSTOMIZE", Neo.

---

### /usr/local/opensips/etc/opensips/opensipsctlrc

In this file, that configures the behavior of the opensipsctrl utilities, you modify the DB-related values.

```bash

# $Id: opensipsctlrc 9049 2012-05-24 14:03:31Z osas $
#
# The OpenSIPS configuration file for the control tools.
#
# Here you can set variables used in the opensipsctl and opensipsdbctl setup
# scripts. Per default all variables here are commented out, the control tools
# will use their internal default values.

## your SIP domain
# SIP_DOMAIN=opensips.org

## chrooted directory
# $CHROOT_DIR="/path/to/chrooted/directory"

## database type: MYSQL, PGSQL, ORACLE, DB_BERKELEY, or DBTEXT,
## by default none is loaded
# If you want to setup a database with opensipsdbctl, you must at least specify
# this parameter.
DBENGINE=MYSQL

## database host #CUSTOMIZE
DBHOST=localhost

## database name (for ORACLE this is TNS name) #CUSTOMIZE
DBNAME=opensips

# database path used by dbtext or db_berkeley
# DB_PATH="/usr/local/etc/opensips/dbtext"

## database read/write user #CUSTOMIZE
DBRWUSER=opensips

## password for database read/write user #CUSTOMIZE
DBRWPW="mydbpassword"

## database super user (for ORACLE this is 'scheme-creator' user) #CUSTOMIZE
DBROOTUSER="root"

# user name column
# USERCOL="username"

# SQL definitions
# If you change this definitions here, then you must change them
# in db/schema/entities.xml too.
# FIXME

# FOREVER="2020-05-28 21:32:15"
# DEFAULT_ALIASES_EXPIRES=$FOREVER
# DEFAULT_Q="1.0"
# DEFAULT_CALLID="Default-Call-ID"
# DEFAULT_CSEQ="13"
# DEFAULT_LOCATION_EXPIRES=$FOREVER

# Program to calculate a message-digest fingerprint
# MD5="md5sum"

# awk tool
# AWK="awk"

# grep tool
# GREP="grep"

# sed tool
# SED="sed"

# Describe what additional tables to install. Valid values for the variables
# below are yes/no/ask. With ask (default) it will interactively ask the user
# for an answer, while yes/no allow for automated, unassisted installs.
#

# If to install tables for the modules in the EXTRA_MODULES variable.
# INSTALL_EXTRA_TABLES=ask

# If to install presence related tables.
# INSTALL_PRESENCE_TABLES=ask

# Define what module tables should be installed.
# If you use the postgres database and want to change the installed tables,
# then you must also adjust the STANDARD_TABLES or EXTRA_TABLES variable
# accordingly in the opensipsdbctl.base script.

# opensips standard modules
# STANDARD_MODULES="standard acc domain group permissions registrar usrloc
#                   msilo alias_db uri_db speeddial avpops auth_db pdt dialog
#                   dispatcher dialplan drouting nathelper load_balancer"

# opensips extra modules
# EXTRA_MODULES="imc cpl siptrace domainpolicy carrierroute userblacklist b2b registrant"

## type of aliases used: DB - database aliases; UL - usrloc aliases
## - default: none
# ALIASES_TYPE="DB"

## control engine: FIFO or UNIXSOCK
## - default FIFO
# CTLENGINE=xmlrpc

## path to FIFO file
# OSIPS_FIFO="/tmp/opensips_fifo"

## MI_CONNECTOR control engine: FIFO, UNIXSOCK, UDP, XMLRPC
# MI_CONNECTOR=FIFO:/tmp/opensips_fifo
# MI_CONNECTOR=UNIXSOCK:/tmp/opensips.sock
# MI_CONNECTOR=UDP:192.168.2.133:8000
# MI_CONNECTOR=XMLRPC:192.168.2.133:8000

## check ACL names; default on (1); off (0)
# VERIFY_ACL=1

## ACL names - if VERIFY_ACL is set, only the ACL names from below list
## are accepted
# ACL_GROUPS="local ld int voicemail free-pstn"

## verbose - debug purposes - default '0'
# VERBOSE=1

## do (1) or don't (0) store plaintext passwords
## in the subscriber table - default '1'
# STORE_PLAINTEXT_PW=0

## do not display the output highlighted
# NOHLPRINT=1

## OPENSIPS START Options
## PID file path - default is: /var/run/opensips.pid
# PID_FILE=/var/run/opensips.pid

## Extra start options - default is: not set
# example: start opensips with 64MB share memory: STARTOPTIONS="-m 64"
# STARTOPTIONS=

```

---

### /usr/local/opensips/etc/opensips/opensips_residential_01.cfg

We created before using the osipsconfig utility a residential script, and we requested the following options: ENABLE_TCP, USE_ALIASES, USE_AUTH, USE_DBACC, USE_DBUSRLOC, USE_DIALOG, USE_DIALPLAN, VM_DIVERSION.

So, we have tcp in addition to udp connectivity, aliases on login, authorization checks, db based accounting and location service, dialog tracking, dialplan transformations, and diversion (redirection) to voicemail server in case of no answer, busy, declined, etc.

In this file you modify DB related values, inserting one block that was missed, IP addresses, syslog facility, modules path (follow "CUSTOMIZE").

Then you add a route( marked "2") that checks if the called number begins with "*" (star) in which case strips the first * and sends the call to FreeSWITCH (marked "freeswitch").

Then you put the correct FreeSWITCH IP address where it redirects to VM (marked "freeswitch").

```c

#
# $Id: opensips_residential.m4 9042 2012-05-17 13:57:10Z vladut-paiu $
#
# OpenSIPS residential configuration script
#     by OpenSIPS Solutions <team@opensips-solutions.com>
#
# This script was generated via "make menuconfig", from
#   the "Residential" scenario.
# You can enable / disable more features / functionalities by
#   re-generating the scenario with different options.#
#
# Please refer to the Core CookBook at:
#      http://www.opensips.org/Resources/DocsCookbooks
# for a explanation of possible statements, functions and parameters.
#

####### Global Parameters #########

debug=3
log_stderror=no
log_facility=LOG_LOCAL1 # CUSTOMIZE ME

fork=yes
children=4

/* uncomment the following lines to enable debugging */
#debug=6
#fork=no
#log_stderror=yes

/* uncomment the next line to enable the auto temporary blacklisting of
   not available destinations (default disabled) */
#disable_dns_blacklist=no

/* uncomment the next line to enable IPv6 lookup after IPv4 dns
   lookup failures (default disabled) */
#dns_try_ipv6=yes

/* comment the next line to enable the auto discovery of local aliases
   based on revers DNS on IPs */
auto_aliases=no

listen=udp:192.168.1.110:5060   # CUSTOMIZE ME

disable_tcp=no
listen=tcp:192.168.1.110:5060   # CUSTOMIZE ME

disable_tls=yes

####### Modules Section ########

#set module path
mpath="/usr/local/opensips/lib64/opensips/modules/" # CUSTOMIZE ME

#### SIGNALING module
loadmodule "signaling.so"

#### StateLess module
loadmodule "sl.so"

#### Transaction Module
loadmodule "tm.so"
modparam("tm", "fr_timer", 5)
modparam("tm", "fr_inv_timer", 30)
modparam("tm", "restart_fr_on_each_reply", 0)
modparam("tm", "onreply_avp_mode", 1)

#### Record Route Module
loadmodule "rr.so"
/* do not append from tag to the RR (no need for this script) */
modparam("rr", "append_fromtag", 0)

#### MAX ForWarD module
loadmodule "maxfwd.so"

#### SIP MSG OPerationS module
loadmodule "sipmsgops.so"

#### FIFO Management Interface
loadmodule "mi_fifo.so"
modparam("mi_fifo", "fifo_name", "/tmp/opensips_fifo")
modparam("mi_fifo", "fifo_mode", 0666)

#### URI module
loadmodule "uri.so"
modparam("uri", "use_uri_table", 0)
modparam("uri", "db_url", # ADD and CUSTOMIZE ME
        "mysql://opensips:mydbpassword@localhost/opensips") # ADD and CUSTOMIZE ME

#### MYSQL module
loadmodule "db_mysql.so"

#### USeR LOCation module
loadmodule "usrloc.so"
modparam("usrloc", "nat_bflag", 10)
modparam("usrloc", "db_mode",   2)
modparam("usrloc", "db_url",
        "mysql://opensips:mydbpassword@localhost/opensips") # CUSTOMIZE ME

#### REGISTRAR module
loadmodule "registrar.so"
modparam("registrar", "tcp_persistent_flag", 7)

/* uncomment the next line not to allow more than 10 contacts per AOR */
#modparam("registrar", "max_contacts", 10)

#### ACCounting module
loadmodule "acc.so"
/* what special events should be accounted ? */
modparam("acc", "early_media", 0)
modparam("acc", "report_cancels", 0)
/* by default we do not adjust the direct of the sequential requests.
   if you enable this parameter, be sure the enable "append_fromtag"
   in "rr" module */
modparam("acc", "detect_direction", 0)
modparam("acc", "failed_transaction_flag", 3)
/* account triggers (flags) */
modparam("acc", "db_flag", 1)
modparam("acc", "db_missed_flag", 2)
modparam("acc", "db_url",
        "mysql://opensips:mydbpassword@localhost/opensips") # CUSTOMIZE ME

#### AUTHentication modules
loadmodule "auth.so"
loadmodule "auth_db.so"
modparam("auth_db", "calculate_ha1", yes)
modparam("auth_db", "password_column", "password")
modparam("auth_db", "db_url",
        "mysql://opensips:mydbpassword@localhost/opensips") # CUSTOMIZE ME
modparam("auth_db", "load_credentials", "")

#### ALIAS module
loadmodule "alias_db.so"
modparam("alias_db", "db_url",
        "mysql://opensips:mydbpassword@localhost/opensips") # CUSTOMIZE ME

#### DIALOG module
loadmodule "dialog.so"
modparam("dialog", "dlg_match_mode", 1)
modparam("dialog", "default_timeout", 21600)  # 6 hours timeout
modparam("dialog", "db_mode", 2)
modparam("dialog", "db_url",
        "mysql://opensips:mydbpassword@localhost/opensips") # CUSTOMIZE ME

####  DIALPLAN module
loadmodule "dialplan.so"
modparam("dialplan", "db_url",
        "mysql://opensips:mydbpassword@localhost/opensips") # CUSTOMIZE ME

####### Routing Logic ########

# main request routing logic

route{

        if (!mf_process_maxfwd_header("10")) {
                sl_send_reply("483","Too Many Hops");
                exit;
        }

        if (has_totag()) {
                # sequential request withing a dialog should
                # take the path determined by record-routing
                if (loose_route()) {

                        # validate the sequential request against dialog
                        if ( $DLG_status!=NULL && !validate_dialog() ) {
                                xlog("In-Dialog $rm from $si (callid=$ci) is not valid according to dialog\n");
                                ## exit;
                        }

                        if (is_method("BYE")) {
                                setflag(1); # do accounting ...
                                setflag(3); # ... even if the transaction fails
                        } else if (is_method("INVITE")) {
                                # even if in most of the cases is useless, do RR for
                                # re-INVITEs alos, as some buggy clients do change route set
                                # during the dialog.
                                record_route();
                        }

                        # route it out to whatever destination was set by loose_route()
                        # in $du (destination URI).
                        route(1);
                } else {

                        if ( is_method("ACK") ) {
                                if ( t_check_trans() ) {
                                        # non loose-route, but stateful ACK; must be an ACK after
                                        # a 487 or e.g. 404 from upstream server
                                        t_relay();
                                        exit;
                                } else {
                                        # ACK without matching transaction ->
                                        # ignore and discard
                                        exit;
                                }
                        }
                        sl_send_reply("404","Not here");
                }
                exit;
        }

        # CANCEL processing
        if (is_method("CANCEL"))
        {
                if (t_check_trans())
                        t_relay();
                exit;
        }

        t_check_trans();

        if ( !(is_method("REGISTER")  ) ) {

                if (from_uri==myself)

                {

                        # authenticate if from local subscriber
                        # authenticate all initial non-REGISTER request that pretend to be
                        # generated by local subscriber (domain from FROM URI is local)
                        if (!proxy_authorize("", "subscriber")) {
                                proxy_challenge("", "0");
                                exit;
                        }
                        if (!db_check_from()) {
                                sl_send_reply("403","Forbidden auth ID");
                                exit;
                        }

                        consume_credentials();
                        # caller authenticated

                } else {
                        # if caller is not local, then called number must be local

                        if (!uri==myself) {
                                send_reply("403","Rely forbidden");
                                exit;
                        }
                }

        }

        # preloaded route checking
        if (loose_route()) {
                xlog("L_ERR",
                "Attempt to route with preloaded Route's [$fu/$tu/$ru/$ci]");
                if (!is_method("ACK"))
                        sl_send_reply("403","Preload Route denied");
                exit;
        }

        # record routing
        if (!is_method("REGISTER|MESSAGE"))
                record_route();

        # account only INVITEs
        if (is_method("INVITE")) {

                # create dialog with timeout
                if ( !create_dialog("B") ) {
                        send_reply("500","Internal Server Error");
                        exit;
                }

                setflag(1); # do accounting
        }

        if (!uri==myself) {
                append_hf("P-hint: outbound\r\n");
                route(1);
        }

        # requests for my domain

        if (is_method("PUBLISH|SUBSCRIBE"))
        {
                sl_send_reply("503", "Service Unavailable");
                exit;
        }

        if (is_method("REGISTER"))
        {

                # authenticate the REGISTER requests
                if (!www_authorize("", "subscriber"))
                {
                        www_challenge("", "0");
                        exit;
                }

                if (!db_check_to())
                {
                        sl_send_reply("403","Forbidden auth ID");
                        exit;
                }

                if ( proto==TCP ||  0 ) setflag(7);

                if (!save("location"))
                        sl_reply_error();

                exit;
        }

        if ($rU==NULL) {
                # request with no Username in RURI
                sl_send_reply("484","Address Incomplete");
                exit;
        }

        # apply DB based aliases
        alias_db_lookup("dbaliases");

        # apply transformations from dialplan table
        dp_translate("0","$rU/$rU");

        #freeswitch
        route(2); # ADD and CUSTOMIZE ME

        # do lookup with method filtering
        if (!lookup("location","m")) {
                if (!db_does_uri_exist()) {
                        send_reply("420","Bad Extension");
                        exit;
                }

                # redirect to a different VM system
                $du = "sip:192.168.1.110:5090"; # CUSTOMIZE ME #freeswitch
                route(1);

        }

        # when routing via usrloc, log the missed calls also
        setflag(2);
        route(1);
}

route[1] {
        # for INVITEs enable some additional helper routes
        if (is_method("INVITE")) {

                t_on_branch("2");
                t_on_reply("2");
                t_on_failure("1");
        }

        if (!t_relay()) {
                send_reply("500","Internal Error");
        };
        exit;
}

# freeswitch
route[2] {# ADD and CUSTOMIZE ME
        if (!is_method("INVITE")) {
                return;
        }

        # if the called number begins with "star" (*) then strip it and redirect to freeswitch 
        # (if it begins with two stars, eg: **, then one will be passed to FS)
        if ($rU=~"^\*") {
                strip(1);
                $du = "sip:192.168.1.110:5090"; # CUSTOMIZE ME
                route(1);
        }
}

branch_route[2] {
        xlog("new branch at $ru\n");
}

onreply_route[2] {

        xlog("incoming reply\n");
}

failure_route[1] {
        if (t_was_cancelled()) {
                exit;
        }

        # uncomment the following lines if you want to block client
        # redirect based on 3xx replies.
        ##if (t_check_status("3[0-9][0-9]")) {
        ##t_reply("404","Not found");
        ##      exit;
        ##}

        # redirect the failed to a different VM system
        if (t_check_status("486|408")) {
                $du = "sip:192.168.1.110:5090"; # CUSTOMIZE ME
                # do not set the missed call flag again
                route(1);
        }
}

local_route {
        if (is_method("BYE") && $DLG_dir=="UPSTREAM") {

                acc_db_request("200 Dialog Timeout", "acc");

        }
}

```

---

### /usr/local/freeswitch/conf/dialplan/public.xml

Starting from the freshly installed default FreeSWITCH "public" (eg: from outside, not trusted to access services and features) dialplan, you insert as the first "extension", aptly named "from_opensips", an instruction that checks if the call is coming from the OpenSIPS server IP address, in which case the call is transferred to the corresponding destination_number in the "default" dialplan (eg: can access the services and features as an internal user).

You must edit the OpenSIPS IP address.

Follow "CUSTOMIZE".

```bash

<!--
    NOTICE:

    This context is usually accessed via the external sip profile listening on port 5080.

    It is recommended to have separate inbound and outbound contexts.  Not only for security
    but clearing up why you would need to do such a thing.  You don't want outside un-authenticated
    callers hitting your default context which allows dialing calls thru your providers and results
    in Toll Fraud.
-->

<!-- http://wiki.freeswitch.org/wiki/Dialplan_XML -->
<include>
  <context name="public">

    <extension name="from_opensips">
      <condition field="network_addr" expression="^192\.168\.1\.110$"> <!--CUSTOMIZE-->
        <action application="transfer" data="${destination_number} XML default"/>
      </condition>
    </extension>

    <extension name="unloop">
      <condition field="${unroll_loops}" expression="^true$"/>
      <condition field="${sip_looped_call}" expression="^true$">
        <action application="deflect" data="${destination_number}"/>
      </condition>
    </extension>
    <!--
        Tag anything pass thru here as an outside_call so you can make sure not
        to create any routing loops based on the conditions that it came from
        the outside of the switch.
    -->
    <extension name="outside_call" continue="true">
      <condition>
        <action application="set" data="outside_call=true"/>
        <action application="export" data="RFC2822_DATE=${strftime(%a, %d %b %Y %T %z)}"/>
      </condition>
    </extension>

    <extension name="call_debug" continue="true">
      <condition field="${call_debug}" expression="^true$" break="never">
        <action application="info"/>
      </condition>
    </extension>

    <extension name="public_extensions">
      <condition field="destination_number" expression="^(10[01][0-9])$">
        <action application="transfer" data="$1 XML default"/>
      </condition>
    </extension>

    <!--
        You can place files in the public directory to get included.
    -->
    <X-PRE-PROCESS cmd="include" data="public/*.xml"/>
    <!--
        If you have made it this far lets challenge the caller and if they authenticate
        lets try what they dialed in the default context. (commented out by default)
    -->
    <!--
    <extension name="check_auth" continue="true">
      <condition field="${sip_authorized}" expression="^true$" break="never">
        <anti-action application="respond" data="407"/>
      </condition>
    </extension>

    <extension name="transfer_to_default">
      <condition>
        <action application="transfer" data="${destination_number} XML default"/>
      </condition>
    </extension>
    -->
  </context>
</include>

```

---

### /usr/local/freeswitch/scripts/config.lua

This file you create ex-nihilo (eg: is not installed by FreeSWITCH). 

It is read by the xml_handler script, and configure it with the correct values for directories and database name, user and password.

Edit it all, or at least edit "mydbpassword".

Follow "CUSTOMIZE".

```text

--switch directories
        sounds_dir = "/usr/local/freeswitch/sounds";
        recordings_dir = "/usr/local/freeswitch/recordings";

--database connection info
        db_type = "mysql";
        db_name = "opensips";
        dsn_name = "opensips";
        dsn_username = "opensips";
        dsn_password = "mydbpassword"; --CUSTOMIZE

--additional info
        tmp_dir = "";

```

---

### /usr/local/freeswitch/scripts/xml_handler.lua

This file you create ex-nihilo (eg: is not installed by FreeSWITCH).

It is executed by the mod_lua Lua module, and fetch from OpenSIPS database the values with which it constructs an xml directory snippet that is passed in real time to FreeSWITCH when FS needs info about users.

You don't need to edit this file, but can be interesting to read.

This file comes originally from FusionPBX ( www.fusionpbx.com ), an opensource web interface to configure and manage FreeSWITCH, and has been cannibalized for our tutorial purposes.

Particularly, you can find there almost all the fields that are supported in FS directory (eg user management), so it can be extended easyly sourcing values from the same or other databases.

```bash

--      HEAVILY MODIFIED AND POSSIBLY BUGIFIED BY Giovanni Maruzzelli (gmaruzz@gmail.com)

--      xml_handler.lua
--      Part of FusionPBX
--      Copyright (C) 2010 Mark J Crane <markjcrane@fusionpbx.com>
--      All rights reserved.
--
--      Redistribution and use in source and binary forms, with or without
--      modification, are permitted provided that the following conditions are met:
--
--      1. Redistributions of source code must retain the above copyright notice,
--         this list of conditions and the following disclaimer.
--
--      2. Redistributions in binary form must reproduce the above copyright
--         notice, this list of conditions and the following disclaimer in the
--         documentation and/or other materials provided with the distribution.
--
--      THIS SOFTWARE IS PROVIDED ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES,
--      INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY
--      AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
--      AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
--      OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
--      SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
--      INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
--      CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
--      ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
--      POSSIBILITY OF SUCH DAMAGE.

--      HEAVILY MODIFIED AND POSSIBLY BUGIFIED BY Giovanni Maruzzelli (gmaruzz@gmail.com)

--set the debug level
debug["params"] = true;
debug["sql"] = true;
debug["xml_request"] = true;
debug["xml_string"] = true;

--show param debug info
if (debug["params"]) then
        freeswitch.consoleLog("notice", "[xml_handler] Params:\n" .. params:serialize() .. "\n");
end

--get the params and set them as variables
local domain_name = params:getHeader("domain");
local purpose   = params:getHeader("purpose");
local profile   = params:getHeader("profile");
local key    = params:getHeader("key");
local user   = params:getHeader("user");
local user_context = params:getHeader("variable_user_context");
local call_context = params:getHeader("Caller-Context");
local destination_number = params:getHeader("Caller-Destination-Number");
local caller_id_number = params:getHeader("Caller-Caller-ID-Number");

--include the lua script
scripts_dir = string.sub(debug.getinfo(1).source,2,string.len(debug.getinfo(1).source)-(string.len(argv[0])+1));
include = assert(loadfile(scripts_dir .. "/config.lua"));
include();

--connect to the database
--ODBC - data source name
        if (dsn_name) then
                dbh = freeswitch.Dbh(dsn_name,dsn_username,dsn_password);
        end
--FreeSWITCH core db handler
        if (db_type == "sqlite") then
                dbh = freeswitch.Dbh("core:"..db_path.."/"..db_name);
        end

--handle the directory
if (XML_REQUEST["section"] == "directory" and key and user and domain_name) then

--prevent processing for invalid user
continue = true;
if (user == "*97") then
        continue = false;
end

--get the extension from the database
if (continue) then

        sql = "SELECT * FROM subscriber WHERE domain = '" .. domain_name .. "' and username = '" .. user .. "' ";
        if (debug["sql"]) then
                freeswitch.consoleLog("notice", "[xml_handler] SQL: " .. sql .. "\n");
        end
        dbh:query(sql, function(row)
                --general
                        domain_uuid = "";
                        extension = row.username;
                        cidr = "";
                        number_alias = "";
                --params
                        password = row.password;
                        vm_enabled = "true";
                        vm_password = row.password;
                        vm_attach_file = "true";
                        vm_keep_local_after_email = "true";
                        vm_mailto = row.email_address;
                        mwi_account = "";
                        auth_acl = "";
                --variables
                        sip_from_user = "";
                        call_group = "";
                        hold_music = "";
                        toll_allow = "";
                        accountcode = "";
                        user_context = "default";
                        effective_caller_id_name = "";
                        effective_caller_id_number = "";
                        outbound_caller_id_name = "";
                        outbound_caller_id_number = "";
                        emergency_caller_id_number = "";
                        directory_full_name = "";
                        directory_visible = "";
                        directory_exten_visible = "";
                        limit_max = "";
                        limit_destination = "";
                        sip_force_contact = "";
                        sip_force_expires = "";
                        nibble_account = "";
                        sip_bypass_media = "";

                --set the dial_string
                dial_string = "{sip_invite_domain=" .. domain_name .. ",presence_id=" .. user .. "@" ..
domain_name .. "}${sofia_contact(" .. user .. "@" .. domain_name .. ")}";

        end);
end
--set the xml array and then concatenate the array to a string
if (password) then
        local xml = {}
        table.insert(xml, [[<?xml version="1.0" encoding="UTF-8" standalone="no"?>]]);
        table.insert(xml, [[<document type="freeswitch/xml">]]);
        table.insert(xml, [[    <section name="directory">]]);
        table.insert(xml, [[            <domain name="]] .. domain_name .. [[">]]);
        if (number_alias) then
                if (cidr) then
                        table.insert(xml, [[                    <user id="]] .. extension .. [["]] .. cidr .. number_alias .. [[>]]);
                else
                        table.insert(xml, [[                    <user id="]] .. extension .. [["]] .. number_alias .. [[>]]);
                end
        else
                if (cidr) then
                        table.insert(xml, [[                    <user id="]] .. extension .. [["]] .. cidr .. [[>]]);
                else
                        table.insert(xml, [[                    <user id="]] .. extension .. [[">]]);
                end
        end
        table.insert(xml, [[                    <params>]]);
        table.insert(xml, [[                            <param name="password" value="]] .. password .. [["/>]]);
        table.insert(xml, [[                            <param name="vm-enabled" value="]] .. vm_enabled .. [["/>]]);
        if (string.len(vm_mailto) > 0) then
                table.insert(xml, [[                            <param name="vm-password" value="]] .. vm_password  .. [["/>]]);
                table.insert(xml, [[                            <param name="vm-email-all-messages" value="]] .. vm_enabled  ..[["/>]]);
                table.insert(xml, [[                            <param name="vm-attach-file" value="]] .. vm_attach_file .. [["/>]]);
                table.insert(xml, [[                            <param name="vm-keep-local-after-email" value="]] .. vm_keep_local_after_email .. [["/>]]);
                table.insert(xml, [[                            <param name="vm-mailto" value="]] .. vm_mailto .. [["/>]]);
        end
        if (string.len(mwi_account) > 0) then
                table.insert(xml, [[                            <param name="MWI-Account" value="]] .. mwi_account .. [["/>]]);
        end
        if (string.len(auth_acl) > 0) then
                table.insert(xml, [[                            <param name="auth-acl" value="]] .. auth_acl .. [["/>]]);
        end
        table.insert(xml, [[                            <param name="dial-string" value="]] .. dial_string .. [["/>]]);
        table.insert(xml, [[                    </params>]]);
        table.insert(xml, [[                    <variables>]]);
        table.insert(xml, [[                            <variable name="domain_uuid" value="]] .. domain_uuid .. [["/>]]);
        if (user_context ~= "default" and user_context ~= "public" and user_context ~= "features") then
                table.insert(xml, [[                            <variable name="domain_name" value="]] .. user_context .. [["/>]]);
        end
        table.insert(xml, [[                            <variable name="caller_id_name" value="]] .. sip_from_user .. [["/>]]);
        table.insert(xml, [[                            <variable name="caller_id_number" value="]] .. sip_from_user .. [["/>]]);
        if (string.len(call_group) > 0) then
                table.insert(xml, [[                            <variable name="call_group" value="]] .. call_group .. [["/>]]);
        end
        if (string.len(hold_music) > 0) then
                table.insert(xml, [[                            <variable name="hold_music" value="]] .. hold_music .. [["/>]]);
        end
        if (string.len(toll_allow) > 0) then
                table.insert(xml, [[                            <variable name="toll_allow" value="]] .. toll_allow .. [["/>]]);
        end
        if (string.len(accountcode) > 0) then
                table.insert(xml, [[                            <variable name="accountcode" value="]] .. accountcode .. [["/>]]);
        end
        table.insert(xml, [[                            <variable name="user_context" value="]] .. user_context .. [["/>]]);
        if (string.len(effective_caller_id_name) > 0) then
                table.insert(xml, [[                            <variable name="effective_caller_id_name" value="]] .. effective_caller_id_name.. [["/>]]);
        end
        if (string.len(effective_caller_id_number) > 0) then
                table.insert(xml, [[                            <variable name="effective_caller_id_number" value="]] .. effective_caller_id_number.. [["/>]]);
        end
        if (string.len(outbound_caller_id_name) > 0) then
                table.insert(xml, [[                            <variable name="outbound_caller_id_name" value="]] .. outbound_caller_id_name .. [["/>]]);
                table.insert(xml, [[                            <variable name="outbound_caller_id_name" value="]] .. outbound_caller_id_name .. [["/>]]);
        end
        if (string.len(outbound_caller_id_number) > 0) then
                table.insert(xml, [[                            <variable name="outbound_caller_id_number" value="]] .. outbound_caller_id_number .. [["/>]]);
        end
        if (string.len(emergency_caller_id_number) > 0) then
                table.insert(xml, [[                            <variable name="emergency_caller_id_number" value="]] .. emergency_caller_id_number .. [["/>]]);
        end
        if (string.len(directory_full_name) > 0) then
                table.insert(xml, [[                            <variable name="directory_full_name" value="]] .. directory_full_name .. [["/>]]);
        end
        if (string.len(directory_visible) > 0) then
                table.insert(xml, [[                            <variable name="directory-visible" value="]] .. directory_visible .. [["/>]]);
        end
        if (string.len(directory_exten_visible) > 0) then
                table.insert(xml, [[                            <variable name="directory-exten-visible" value="]] .. directory_exten_visible .. [["/>]]);
        end
        if (string.len(limit_max) > 0) then
                table.insert(xml, [[                            <variable name="limit_max" value="]] .. limit_max .. [["/>]]);
        else
                table.insert(xml, [[                            <variable name="limit_max" value="5"/>]]);
        end
        if (string.len(limit_destination) > 0) then
                table.insert(xml, [[                            <variable name="limit_destination" value="]] .. limit_destination .. [["/>]]);
        end
        if (string.len(sip_force_contact) > 0) then
                table.insert(xml, [[                            <variable name="sip_force_contact" value="]] .. sip_force_contact .. [["/>]]);
        end
        if (string.len(sip_force_expires) > 0) then
                table.insert(xml, [[                            <variable name="sip-force-expires" value="]] .. sip_force_expires .. [["/>]]);
        end
        if (string.len(nibble_account) > 0) then
                table.insert(xml, [[                            <variable name="nibble_account" value="]] .. nibble_account .. [["/>]]);
        end
        if (sip_bypass_media == "bypass-media") then
                table.insert(xml, [[                            <variable name="bypass_media" value="true"/>]]);
        end
        if (sip_bypass_media == "bypass-media-after-bridge") then
                table.insert(xml, [[                            <variable name="bypass_media_after_bridge" value="true"/>]]);
        end
        if (sip_bypass_media == "proxy-media") then
                table.insert(xml, [[                            <variable name="proxy_media" value="true"/>]]);
        end
        table.insert(xml, [[                            <variable name="record_stereo" value="true"/>]]);
        table.insert(xml, [[                            <variable name="transfer_fallback_extension" value="operator"/>]]);
        table.insert(xml, [[                            <variable name="export_vars" value="domain_name"/>]]);
        table.insert(xml, [[                    </variables>]]);
        table.insert(xml, [[                    </user>]]);
        table.insert(xml, [[            </domain>]]);
        table.insert(xml, [[    </section>]]);
        table.insert(xml, [[</document>]]);
        XML_STRING = table.concat(xml, "\n");
else
        XML_STRING = "";
end

--send the xml to a file
if (debug["xml_string"]) then
        local file = assert(io.open("/tmp/directory.xml", "w"));
        file:write(XML_STRING);
        file:close();
end

--send the xml to the console
if (debug["xml_string"]) then
        freeswitch.consoleLog("notice", "[xml_handler] XML_STRING: \n" .. XML_STRING .. "\n");
end
end

if (debug["xml_request"]) then
        freeswitch.consoleLog("notice", "[xml_handler] Section: " .. XML_REQUEST["section"] .. "\n");
        freeswitch.consoleLog("notice", "[xml_handler] Tag Name: " .. XML_REQUEST["tag_name"] .. "\n");
        freeswitch.consoleLog("notice", "[xml_handler] Key Name: " .. XML_REQUEST["key_name"] .. "\n");
        freeswitch.consoleLog("notice", "[xml_handler] Key Value: " .. XML_REQUEST["key_value"] .. "\n");
end

```

---

### /usr/local/freeswitch/conf/vars.xml

This file contains the variables that are interpolated into FreeSWITCH configuration files when they are sourced the first time at FreeSWITCH startup (eg: NOT when you "reload" FreeSWITCH).

Here you do not have to change nothing, we configured FreeSWITCH ports before.

Anyway, they're marked "CUSTOMIZE".

```text

<include>
  <!-- Preprocessor Variables
       These are introduced when configuration strings must be consistent across modules.
       NOTICE: YOU CAN NOT COMMENT OUT AN X-PRE-PROCESS line, Remove the line instead.

       WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING

       YOU SHOULD CHANGE THIS default_password value if you don't want to be subject to any
       toll fraud in the future.  It's your responsibility to secure your own system.

       This default config is used to demonstrate the feature set of FreeSWITCH.

       WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING
  -->
  <X-PRE-PROCESS cmd="set" data="default_password=1234"/>
  <!-- Did you change it yet? -->

  <X-PRE-PROCESS cmd="set" data="sound_prefix=$${sounds_dir}/en/us/callie"/>

  <!--
      This setting is what sets the default domain FreeSWITCH will use if all else fails.

      FreeSWICH will default to $${local_ip_v4} unless changed.  Changing this setting does
      affect the sip authentication.  Please review conf/directory/default.xml for more
      information on this topic.
  -->
  <X-PRE-PROCESS cmd="set" data="domain=$${local_ip_v4}"/>
  <X-PRE-PROCESS cmd="set" data="domain_name=$${domain}"/>
  <X-PRE-PROCESS cmd="set" data="hold_music=local_stream://moh"/>
  <X-PRE-PROCESS cmd="set" data="use_profile=internal"/>

  <!--
      Enable ZRTP globally you can override this on a per channel basis

      http://wiki.freeswitch.org/wiki/ZRTP (on how to enable zrtp)
  -->
  <X-PRE-PROCESS cmd="set" data="zrtp_secure_media=true"/>

  <!--
       Examples of codec options: (module must be compiled and loaded)

       codecname[@8000h|16000h|32000h[@XXi]]

       XX is the frame size must be multples allowed for the codec
       FreeSWITCH can support 10-120ms on some codecs.
       We do not support exceeding the MTU of the RTP packet.

       iLBC@30i         - iLBC using mode=30 which will win in all cases.
       DVI4@8000h@20i   - IMA ADPCM 8kHz using 20ms ptime. (multiples of 10)
       DVI4@16000h@40i  - IMA ADPCM 16kHz using 40ms ptime. (multiples of 10)
       speex@8000h@20i  - Speex 8kHz using 20ms ptime.
       speex@16000h@20i - Speex 16kHz using 20ms ptime.
       speex@32000h@20i - Speex 32kHz using 20ms ptime.
       BV16             - BroadVoice 16kb/s narrowband, 8kHz
       BV32             - BroadVoice 32kb/s wideband, 16kHz
       G7221@16000h     - G722.1 16kHz (aka Siren 7)
       G7221@32000h     - G722.1C 32kHz (aka Siren 14)
       CELT@32000h      - CELT 32kHz, only 10ms supported
       CELT@48000h      - CELT 48kHz, only 10ms supported
       GSM@40i          - GSM 8kHz using 40ms ptime. (GSM is done in multiples of 20, Default is 20ms)
       G722             - G722 16kHz using default 20ms ptime. (multiples of 10)
       PCMU             - G711 8kHz ulaw using default 20ms ptime. (multiples of 10)
       PCMA             - G711 8kHz alaw using default 20ms ptime. (multiples of 10)
       G726-16          - G726 16kbit adpcm using default 20ms ptime. (multiples of 10)
       G726-24          - G726 24kbit adpcm using default 20ms ptime. (multiples of 10)
       G726-32          - G726 32kbit adpcm using default 20ms ptime. (multiples of 10)
       G726-40          - G726 40kbit adpcm using default 20ms ptime. (multiples of 10)
       AAL2-G726-16     - Same as G726-16 but using AAL2 packing. (multiples of 10)
       AAL2-G726-24     - Same as G726-24 but using AAL2 packing. (multiples of 10)
       AAL2-G726-32     - Same as G726-32 but using AAL2 packing. (multiples of 10)
       AAL2-G726-40     - Same as G726-40 but using AAL2 packing. (multiples of 10)
       LPC              - LPC10 using 90ms ptime (only supports 90ms at this time in FreeSWITCH)
       L16              - L16 isn't recommended for VoIP but you can do it. L16 can exceed the MTU rather quickly.

       These are the passthru audio codecs:

       G729             - G729 in passthru mode. (mod_g729)
       G723             - G723.1 in passthru mode. (mod_g723_1)
       AMR              - AMR in passthru mode. (mod_amr)

       These are the passthru video codecs: (mod_h26x)

       H261             - H.261 Video
       H263             - H.263 Video
       H263-1998        - H.263-1998 Video
       H263-2000        - H.263-2000 Video
       H264             - H.264 Video

       RTP Dynamic Payload Numbers currently used in FreeSWITCH and what for.

       96  - AMR
       97  - iLBC (30)
       98  - iLBC (20)
       99  - Speex 8kHz, 16kHz, 32kHz
       100 -
       101 - telephone-event
       102 -
       103 -
       104 -
       105 -
       106 - BV16
       107 - G722.1 (16kHz)
       108 -
       109 -
       110 -
       111 -
       112 -
       113 -
       114 - CELT 32kHz, 48kHz
       115 - G722.1C (32kHz)
       116 -
       117 - SILK 8kHz
       118 - SILK 12kHz
       119 - SILK 16kHz
       120 - SILK 24kHz
       121 - AAL2-G726-40 && G726-40
       122 - AAL2-G726-32 && G726-32
       123 - AAL2-G726-24 && G726-24
       124 - AAL2-G726-16 && G726-16
       125 -
       126 -
       127 - BV32

  -->
  <X-PRE-PROCESS cmd="set" data="global_codec_prefs=G722,PCMU,PCMA,GSM"/>
  <X-PRE-PROCESS cmd="set" data="outbound_codec_prefs=PCMU,PCMA,GSM"/>

  <!--
      xmpp_client_profile and xmpp_server_profile
      xmpp_client_profile can be any string.
      xmpp_server_profile is appended to "dingaling_" to form the database name
      containing the "subscriptions" table.
      used by: dingaling.conf.xml enum.conf.xml
  -->

  <X-PRE-PROCESS cmd="set" data="xmpp_client_profile=xmppc"/>
  <X-PRE-PROCESS cmd="set" data="xmpp_server_profile=xmpps"/>
  <!--
       THIS IS ONLY USED FOR DINGALING

       bind_server_ip

       Can be an ip address, a dns name, or "auto".
       This determines an ip address available on this host to bind.
       If you are separating RTP and SIP traffic, you will want to have
       use different addresses where this variable appears.
       Used by: dingaling.conf.xml
  -->
  <X-PRE-PROCESS cmd="set" data="bind_server_ip=auto"/>

  <!-- NOTICE NOTICE NOTICE NOTICE NOTICE NOTICE NOTICE NOTICE NOTICE NOTICE NOTICE

       If you're going to load test FreeSWITCH please input real IP addresses
       for external_rtp_ip and external_sip_ip
  -->

  <!-- external_rtp_ip
       Can be an one of:
           ip address: "12.34.56.78"
           a stun server lookup: "stun:stun.server.com"
           a DNS name: "host:host.server.com"
       where fs.mydomain.com is a DNS A record-useful when fs is on
       a dynamic IP address, and uses a dynamic DNS updater.
       If unspecified, the bind_server_ip value is used.
       Used by: sofia.conf.xml dingaling.conf.xml
  -->
  <X-PRE-PROCESS cmd="set" data="external_rtp_ip=stun:stun.freeswitch.org"/>

  <!-- external_sip_ip
      Used as the public IP address for SDP.
       Can be an one of:
           ip address: "12.34.56.78"
           a stun server lookup: "stun:stun.server.com"
           a DNS name: "host:host.server.com"
       where fs.mydomain.com is a DNS A record-useful when fs is on
       a dynamic IP address, and uses a dynamic DNS updater.
       If unspecified, the bind_server_ip value is used.
       Used by: sofia.conf.xml dingaling.conf.xml
  -->
  <X-PRE-PROCESS cmd="set" data="external_sip_ip=stun:stun.freeswitch.org"/>

  <!-- unroll-loops
       Used to turn on sip loopback unrolling.
  -->
  <X-PRE-PROCESS cmd="set" data="unroll_loops=true"/>

  <!-- outbound_caller_id and outbound_caller_name
       The caller ID telephone number we should use when calling out.
       Used by: conference.conf.xml and user directory for default
       outbound callerid name and number.
  -->
  <X-PRE-PROCESS cmd="set" data="outbound_caller_name=FreeSWITCH"/>
  <X-PRE-PROCESS cmd="set" data="outbound_caller_id=0000000000"/>

  <!-- various debug and defaults -->
  <X-PRE-PROCESS cmd="set" data="call_debug=false"/>
  <X-PRE-PROCESS cmd="set" data="console_loglevel=info"/>
  <X-PRE-PROCESS cmd="set" data="default_areacode=918"/>
  <X-PRE-PROCESS cmd="set" data="default_country=US"/>

  <!-- if false or undefined, the destination number is included in presence NOTIFY dm:note.
       if true, the destination number is not included -->
  <X-PRE-PROCESS cmd="set" data="presence_privacy=false"/>

  <X-PRE-PROCESS cmd="set" data="be-ring=%(1000,3000,425)"/>
  <X-PRE-PROCESS cmd="set" data="ca-ring=%(2000,4000,440,480)"/>
  <X-PRE-PROCESS cmd="set" data="cn-ring=%(1000,4000,450)"/>
  <X-PRE-PROCESS cmd="set" data="cy-ring=%(1500,3000,425)"/>
  <X-PRE-PROCESS cmd="set" data="cz-ring=%(1000,4000,425)"/>
  <X-PRE-PROCESS cmd="set" data="de-ring=%(1000,4000,425)"/>
  <X-PRE-PROCESS cmd="set" data="dk-ring=%(1000,4000,425)"/>
  <X-PRE-PROCESS cmd="set" data="dz-ring=%(1500,3500,425)"/>
  <X-PRE-PROCESS cmd="set" data="eg-ring=%(2000,1000,475,375)"/>
  <X-PRE-PROCESS cmd="set" data="es-ring=%(1500,3000,425)"/>
  <X-PRE-PROCESS cmd="set" data="fi-ring=%(1000,4000,425)"/>
  <X-PRE-PROCESS cmd="set" data="fr-ring=%(1500,3500,440)"/>
  <X-PRE-PROCESS cmd="set" data="hk-ring=%(400,200,440,480);%(400,3000,440,480)"/>
  <X-PRE-PROCESS cmd="set" data="hu-ring=%(1250,3750,425)"/>
  <X-PRE-PROCESS cmd="set" data="il-ring=%(1000,3000,400)"/>
  <X-PRE-PROCESS cmd="set" data="in-ring=%(400,200,425,375);%(400,2000,425,375)"/>
  <X-PRE-PROCESS cmd="set" data="jp-ring=%(1000,2000,420,380)"/>
  <X-PRE-PROCESS cmd="set" data="ko-ring=%(1000,2000,440,480)"/>
  <X-PRE-PROCESS cmd="set" data="pk-ring=%(1000,2000,400)"/>
  <X-PRE-PROCESS cmd="set" data="pl-ring=%(1000,4000,425)"/>
  <X-PRE-PROCESS cmd="set" data="ro-ring=%(1850,4150,475,425)"/>
  <X-PRE-PROCESS cmd="set" data="rs-ring=%(1000,4000,425)"/>
  <X-PRE-PROCESS cmd="set" data="ru-ring=%(800,3200,425)"/>
  <X-PRE-PROCESS cmd="set" data="sa-ring=%(1200,4600,425)"/>
  <X-PRE-PROCESS cmd="set" data="tr-ring=%(2000,4000,450)"/>
  <X-PRE-PROCESS cmd="set" data="uk-ring=%(400,200,400,450);%(400,2000,400,450)"/>
  <X-PRE-PROCESS cmd="set" data="us-ring=%(2000,4000,440,480)"/>
  <X-PRE-PROCESS cmd="set" data="bong-ring=v=-7;%(100,0,941.0,1477.0);v=-7;>=2;+=.1;%(1400,0,350,440)"/>
  <X-PRE-PROCESS cmd="set" data="sit=%(274,0,913.8);%(274,0,1370.6);%(380,0,1776.7)"/>
  <!--
      Setting up your default sip provider is easy.
      Below are some values that should work in most cases.

      These are for conf/directory/default/example.com.xml
  -->
  <X-PRE-PROCESS cmd="set" data="default_provider=example.com"/>
  <X-PRE-PROCESS cmd="set" data="default_provider_username=joeuser"/>
  <X-PRE-PROCESS cmd="set" data="default_provider_password=password"/>
  <X-PRE-PROCESS cmd="set" data="default_provider_from_domain=example.com"/>
  <!-- true or false -->
  <X-PRE-PROCESS cmd="set" data="default_provider_register=false"/>
  <X-PRE-PROCESS cmd="set" data="default_provider_contact=5000"/>

  <!--
      SIP and TLS settings. http://wiki.freeswitch.org/wiki/Tls
  -->
  <X-PRE-PROCESS cmd="set" data="sip_tls_version=tlsv1"/>

  <!-- Internal SIP Profile -->
  <X-PRE-PROCESS cmd="set" data="internal_auth_calls=true"/>
  <X-PRE-PROCESS cmd="set" data="internal_sip_port=5090"/> <!--CUSTOMIZE-->
  <X-PRE-PROCESS cmd="set" data="internal_tls_port=5061"/>
  <X-PRE-PROCESS cmd="set" data="internal_ssl_enable=false"/>
  <X-PRE-PROCESS cmd="set" data="internal_ssl_dir=$${base_dir}/conf/ssl"/>

  <!-- External SIP Profile -->
  <X-PRE-PROCESS cmd="set" data="external_auth_calls=false"/>
  <X-PRE-PROCESS cmd="set" data="external_sip_port=5091"/> <!--CUSTOMIZE-->
  <X-PRE-PROCESS cmd="set" data="external_tls_port=5081"/>
  <X-PRE-PROCESS cmd="set" data="external_ssl_enable=false"/>
  <X-PRE-PROCESS cmd="set" data="external_ssl_dir=$${base_dir}/conf/ssl"/>
</include>

```

---

### /usr/local/freeswitch/conf/autoload_configs/modules.conf.xml

This file controls which FreeSWITCH modules are loaded at startup time.

No changes from standard original FreeSWITCH configuration, just be sure mod_lua is not commented out. We use Lua for database user management.

```text

<configuration name="modules.conf" description="Modules">
  <modules>

    <!-- Loggers (I'd load these first) -->
    <load module="mod_console"/>
    <load module="mod_logfile"/>
    <!-- <load module="mod_syslog"/> -->

    <!--<load module="mod_yaml"/>-->

    <!-- Multi-Faceted -->
    <!-- mod_enum is a dialplan interface, an application interface and an api command interface -->
    <load module="mod_enum"/>

    <!-- XML Interfaces -->
    <!-- <load module="mod_xml_rpc"/> -->
    <!-- <load module="mod_xml_curl"/> -->
    <!-- <load module="mod_xml_cdr"/> -->
    <!-- <load module="mod_xml_scgi"/> -->

    <!-- Event Handlers -->
    <load module="mod_cdr_csv"/>
    <!-- <load module="mod_cdr_sqlite"/> -->
    <!-- <load module="mod_event_multicast"/> -->
    <load module="mod_event_socket"/>
    <!-- <load module="mod_event_zmq"/> -->
    <!-- <load module="mod_zeroconf"/> -->
    <!-- <load module="mod_erlang_event"/> -->
    <!-- <load module="mod_snmp"/> -->

    <!-- Directory Interfaces -->
    <!-- <load module="mod_ldap"/> -->

    <!-- Endpoints -->
    <!-- <load module="mod_dingaling"/> -->
    <!-- <load module="mod_portaudio"/> -->
    <!-- <load module="mod_alsa"/> -->
    <load module="mod_sofia"/>
    <load module="mod_loopback"/>
    <!-- <load module="mod_woomera"/> -->
    <!-- <load module="mod_freetdm"/> -->
    <!-- <load module="mod_openzap"/> -->
    <!-- <load module="mod_unicall"/> -->
    <!-- <load module="mod_skinny"/> -->
    <!-- <load module="mod_khomp"/>   -->
    <!-- <load module="mod_rtmp"/>   -->

    <!-- Applications -->
    <load module="mod_commands"/>
    <load module="mod_conference"/>
    <load module="mod_db"/>
    <load module="mod_dptools"/>
    <load module="mod_expr"/>
    <load module="mod_fifo"/>
    <load module="mod_hash"/>
    <load module="mod_voicemail"/>
    <!--<load module="mod_directory"/>-->
    <!--<load module="mod_distributor"/>-->
    <!--<load module="mod_lcr"/>-->
    <load module="mod_esf"/>
    <load module="mod_fsv"/>
    <load module="mod_cluechoo"/>
    <load module="mod_valet_parking"/>
    <!--<load module="mod_fsk"/>-->
    <!--<load module="mod_spy"/>-->
    <!--<load module="mod_random"/>-->
    <load module="mod_httapi"/>

    <!-- SNOM Module -->
    <!--<load module="mod_snom"/>-->

    <!-- This one only works on Linux for now -->
    <!--<load module="mod_ladspa"/>-->

    <!-- Dialplan Interfaces -->
    <!-- <load module="mod_dialplan_directory"/> -->
    <load module="mod_dialplan_xml"/>
    <load module="mod_dialplan_asterisk"/>

    <!-- Codec Interfaces -->
    <load module="mod_spandsp"/>
    <load module="mod_g723_1"/>
    <load module="mod_g729"/>
    <load module="mod_amr"/>
    <!--<load module="mod_ilbc"/>-->
    <load module="mod_speex"/>
    <load module="mod_h26x"/>
    <load module="mod_vp8"/>
    <!--<load module="mod_siren"/>-->
    <!--<load module="mod_isac"/>-->
    <!--<load module="mod_celt"/>-->
    <!--<load module="mod_opus"/>-->

    <!-- File Format Interfaces -->
    <load module="mod_sndfile"/>
    <load module="mod_native_file"/>
    <!-- <load module="mod_shell_stream"/> -->
    <!--For icecast/mp3 streams/files-->
    <!--<load module="mod_shout"/>-->
    <!--For local streams (play all the files in a directory)-->
    <load module="mod_local_stream"/>
    <load module="mod_tone_stream"/>

    <!-- Timers -->
    <!-- <load module="mod_timerfd"/> -->
    <!-- <load module="mod_posix_timer"/> -->

    <!-- Languages -->
    <load module="mod_spidermonkey"/>
    <!-- <load module="mod_perl"/> -->
    <!-- <load module="mod_python"/> -->
    <!-- <load module="mod_java"/> -->
    <load module="mod_lua"/>

    <!-- ASR /TTS -->
    <!-- <load module="mod_flite"/> -->
    <!-- <load module="mod_pocketsphinx"/> -->
    <!-- <load module="mod_cepstral"/> -->
    <!-- <load module="mod_tts_commandline"/> -->
    <!-- <load module="mod_rss"/> -->

    <!-- Say -->
    <load module="mod_say_en"/>
    <!-- <load module="mod_say_ru"/> -->
    <!-- <load module="mod_say_zh"/> -->

    <!-- Third party modules -->
    <!--<load module="mod_nibblebill"/>-->
    <!--<load module="mod_callcenter"/>-->

  </modules>
</configuration>

```

---

### /usr/local/freeswitch/conf/autoload_configs/lua.conf.xml

This is the configuration file for mod_lua.

Start with the standard installed file, and then add the name of the script that will provide the XML data (in our case "xml_handler.lua") for which part of FreeSWITCH (in our case just for the "directory" part).

You don't need to customize this file, but the lines added are marked as "CUSTOMIZE".

```text

<configuration name="lua.conf" description="LUA Configuration">
  <settings>

    <!--
    Specify local directories that will be searched for LUA modules
    These entries will be pre-pended to the LUA_CPATH environment variable
    -->
    <!-- <param name="module-directory" value="/usr/lib/lua/5.1/?.so"/> -->
    <!-- <param name="module-directory" value="/usr/local/lib/lua/5.1/?.so"/> -->

    <!--
    Specify local directories that will be searched for LUA scripts
    These entries will be pre-pended to the LUA_PATH environment variable
    -->
    <!-- <param name="script-directory" value="/usr/local/lua/?.lua"/> -->
    <!-- <param name="script-directory" value="$${base_dir}/scripts/?.lua"/> -->

    <!--<param name="xml-handler-script" value="/dp.lua"/>-->
    <!--<param name="xml-handler-bindings" value="dialplan"/>-->

    <!--
        The following options identifies a lua script that is launched
        at startup and may live forever in the background.
        You can define multiple lines, one for each script you
        need to run.
    -->
    <!--<param name="startup-script" value="startup_script_1.lua"/>-->
    <!--<param name="startup-script" value="startup_script_2.lua"/>-->
        <param name="xml-handler-script" value="xml_handler.lua"/> <!--CUSTOMIZE-->
        <param name="xml-handler-bindings" value="directory"/> <!--CUSTOMIZE-->
  </settings>
</configuration>

```

---

### /usr/local/freeswitch/conf/autoload_configs/acl.conf.xml

This file configure the Access Control List (ACL) for FreeSWITCH.

Starting from the original installed file, you insert one line that allows (without further checking for authorization) any call coming from the OpenSIPS IP address.

You need to customize that IP address, follow "CUSTOMIZE".

```text

<configuration name="acl.conf" description="Network Lists">
  <network-lists>
    <!--
         These ACL's are automatically created on startup.

         rfc1918.auto  - RFC1918 Space
         nat.auto      - RFC1918 Excluding your local lan.
         localnet.auto - ACL for your local lan.
         loopback.auto - ACL for your local lan.
    -->

    <list name="lan" default="allow">
      <node type="deny" cidr="192.168.42.0/24"/>
      <node type="allow" cidr="192.168.42.42/32"/>
    </list>

    <!--
        This will traverse the directory adding all users
        with the cidr= tag to this ACL, when this ACL matches
        the users variables and params apply as if they
        digest authenticated.
    -->
    <list name="domains" default="deny">
      <!-- domain= is special it scans the domain from the directory to build the ACL -->
      <node type="allow" domain="$${domain}"/>
      <!-- use cidr= if you wish to allow ip ranges to this domains acl. -->
      <!-- <node type="allow" cidr="192.168.0.0/24"/> -->
      <node type="allow" cidr="192.168.1.110/24"/> <!--CUSTOMIZE-->
    </list>

  </network-lists>
</configuration>

```

---

### /etc/odbcinst.ini

This is the ODBC configuration file that tells ODBC where to find drivers.

You probably don't need to customize it. Just check that is like the following.

```text

[MySQL]
Description     = MySQL driver
Driver          = /usr/lib64/odbc/libmyodbc.so
Setup           = /usr/lib64/odbc/libodbcmyS.so
UsageCount      = 1
FileUsage       = 1
Threading       = 0

```

---

### /etc/odbc.ini

PAY ATTENTION TO THIS FILE !!!

If you insert comments in it, it will not work (brain damaged, but true).

You need at least to change "mydbpassword".

DON'T INSERT COMMENTS

```text

[opensips]
Driver          = /usr/lib64/odbc/libmyodbc.so
SERVER          = 127.0.0.1
PORT            = 3306
DATABASE        = opensips
OPTION          = 67108864
USER            = opensips
PASSWORD        = mydbpassword

```

---

## PROFIT !

Restart it all

```text

/etc/init.d/apache2 restart
/etc/init.d/opensips restart
/usr/local/freeswitch/bin/freeswitch -stop
/usr/local/freeswitch/bin/freeswitch -nc -nonat

```

Go with your browser to http://webserveripaddress/cp

Use OpenSIPS-CP to create a domain, then a couple users in that domain.

Verify that all is working.

They can call each other, calls goes to voicemail when needed, FreeSWITCH features can be accessed prepending * (star) to the corresponding FreeSWITCH extension (eg: *9664 for Music).

Get rich!
