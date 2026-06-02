---
title: "PUA USRLOC config file"
description: "debug=3 fork=yes log_stderror=no"
---

```c

#
# OpenSIPS 1.11.x configuration file
#
# Pua_usrloc + Presence Server 
#

# ----------- global configuration parameters ------------------------

debug=3
fork=yes
log_stderror=no

check_via=no
dns=no
rev_dns=no

listen=udp:10.10.10.10:5060
children=2

# ------------------ module loading ----------------------------------
mpath="/usr/local/opensips/lib/modules/"

loadmodule "db_mysql.so"
loadmodule "sl.so"
loadmodule "signaling.so"
loadmodule "tm.so"
loadmodule "maxfwd.so"
loadmodule "textops.so"
loadmodule "sipmsgops.so"
loadmodule "rr.so"
loadmodule "mi_fifo.so"
loadmodule "usrloc.so"
loadmodule "registrar.so"
loadmodule "presence.so"
loadmodule "presence_xml.so"
loadmodule "pua.so"
loadmodule "pua_usrloc.so"

# Uncomment this if you want digest authentication
#loadmodule "auth.so"
#loadmodule "auth_db.so"

# ----------------- setting module-specific parameters ---------------
modparam("mi_fifo","fifo_name","/tmp/opensips_fifo")

# -- usrloc params --
modparam("usrloc","db_mode",2)
modparam("usrloc","db_url","mysql://opensips:opensipsrw@localhost/opensips")

# -- auth params --
# Uncomment if you are using auth module
#modparam("auth_db", "calculate_ha1", yes)
#modparam("auth_db", "password_column", "password")

# -- presence params --
modparam("presence|presence_xml","db_url","mysql://opensips:opensipsrw@localhost/opensips")
modparam("presence","server_address","sip:sa@10.10.10.10:5060")
modparam("presence_xml","force_active",1)

# -- pua and pua_usrloc parameters --
modparam("pua","db_url","mysql://opensips:opensipsrw@localhost/opensips")
modparam("pua_usrloc","default_domain","10.10.10.10")

# -------------------------  request routing logic -------------------

# main routing logic
route{

	# initial sanity checks
	if(!mf_process_maxfwd_header("10")) {
		send_reply("483","Too Many Hops");
		exit;
	}

	if (has_totag()) {
		# sequential requests within a dialog should
		# take the path determined by record-routing
		if (loose_route()) {
			# route it out to whatever destination was set by loose_route()
			# in $du (destination URI).
			route(relay);
		} else {
			if (is_method("SUBSCRIBE") && uri==myself) {
				# in-dialog subscribe requests
				route(handle_presence);
				exit;
			} else if ( is_method("ACK") ) {
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
			send_reply("404","Not here");
		}
		exit;
	}

	# CANCEL processing
	if (is_method("CANCEL")) {
		if (t_check_trans())
			t_relay();
		exit;
	}

	t_check_trans();

	# record routing
	if (!is_method("REGISTER|MESSAGE"))
		record_route();

	if (uri!=myself) {
		# routing to other SIP domains
		route(relay);
	}

	if (is_method("PUBLISH|SUBSCRIBE")) {
		route(handle_presence);
		exit;
	}

	if (is_method("REGISTER")) {

		# Uncomment this if you want to use digest authentication
		#if (!www_authorize("", "subscriber")) {
		#  www_challenge("", "0");
		#  exit;
		#}

		# make pua_usrloc send PUBLISH for phones which do not support
		# presence; do filter after User-Agent header
		if ( $hdr("User-Agent")!~"X-Lite" )
			pua_set_publish();

		save("location");
		exit;
	}

	# native SIP destinations are handled using our USRLOC DB
	if(!lookup("location")) {
		send_reply("404","Not Found");
		exit;
	}

	route(relay);
}

route[relay]{
	# send it out
	if(!t_relay())
		sl_reply_error();

	exit;
}

route[handle_presence]
{
	if(!t_newtran()){
		sl_reply_error();
		exit;
	}

	if (is_method("PUBLISH")) {
		handle_publish();
	} else
	if (is_method("SUBSCRIBE")) {
		handle_subscribe();
	}

	exit;
}

```
