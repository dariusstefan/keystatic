---
title: "Perl"
description: "loadmodule \"perl.so\" modparam(\"perl\", \"filename\", \"/etc/opensips/perlfunctions.pl\")"
---

## Replace 183 early media reply with 180 (Ringing)
### Task
We want to catch all 183 status responses, remove the SDP body and send a plain 180 reply instead. This example script has also been posted to the OpenSIPS-Users mailinglist and should show the possibilities of the OpenSIPS Perl module.

### Usage
```c

loadmodule "perl.so"
modparam("perl", "filename", "/etc/opensips/perlfunctions.pl")

onreply_route[1]
{
    ...
    if(t_check_status("183")) {
        perl_exec("sendReplyAs180");
        drop();
    }
}

```

### Example script (Perl code)
```perl

#####################################################################
# Example perl script, sending 180 Ringing for a given reply packet
#
# Description
#
# <to be done - no time right now, script has been discussed on IRC>
#
# WARNING:
#
# This software is given as is, without any warranty and support.
# It may destroy all your servers, delete all your data, kill your
# little dog and hurt your little sister.
#
# I'm not responsible for such side effects - therefore you should
# absolutely NOT use this script unless you exactly understand what
# it will do to your environment.
#
# Author      : Thomas Gelf <thomas@gelf.net>
# License     : Unsure, but: just use it, I'll for sure not sue you!
# Last change : 2009/04/12
#
#####################################################################

use OpenSIPS qw ( log );
use OpenSIPS::Constants;

###
# Create a hashref out of ab=123;bc=45
##
sub splitKeyValue {
    my @parts = split /\;/, shift;
    my $avp;
    my $key;
    my $val;
    while (my $part = shift(@parts)) {
        ($key, $val) = split /=/, $part, 2;
        $avp->{$key} = $val;
    }
    return $avp;
}

###
# Return a hashref of arrays with all headers found in given string,
# grouped by header name (case sensitive!)
##
sub parseHeaderLines {
    my $header = shift;
    my @lines = split /\r?\n/, $header;
    my $headers;
    my $key;
    my $val;
    while ($line = shift @lines) {
        ($key, $val) = split /:\s*/, $line, 2;
        my @values = split /,/, $val;
        push @{$headers->{$key}}, @values;
    }
    return $headers;
}

###
# Should be called for 183 replies, that need to be "converted" to
# SDP-less 180 Ringing replies
##
sub sendReplyAs180 {
    my $vias;
    my $via;
    my $via_params;
    my $top_via;
    my $new_header;
    my $headers;
    my $status_line;
    my $port = 5060;
    my $message = shift;
    my @header_lines = split /\r\n/, $message->getFullHeader();

    # Separate Via lines from the rest of the header
    foreach (@header_lines) {
        if (/^Via:/) {
            $via .= $_ . "\r\n";
        } else {
            if (! $status_line) {
                $status_line = $_ . "\r\n";
            } else {
                # Skip Content-* lines
                $headers .= $_ . "\r\n" if ! /^Content-/i;
            }
        }
    }

    # Add Content-Length: 0
    $headers .= "Content-Length: 0\r\n\r\n";

    # Start new header with different status line
    $new_header = "SIP/2.0 180 Ringing\r\n";

    # Remove topmost Via
    $vias = parseHeaderLines($via);
    shift @{$vias->{Via}};
    foreach $key (keys %$vias) {
        # Add remaining Via's to new header
        foreach (@{$vias->{$key}}) {
            $new_header .= "Via: $_\r\n";
        }
    }

    # Re-add other headers
    $new_header .= $headers;

    # Retrieve destination ip and port, with respect to received and rport
    $top_via = $vias->{Via}[0];
    ($dummy, $top_via) = split /\s+/, $top_via, 2;
    ($ip, $top_via) = split /;/, $top_via, 2;
    my $via_params = splitKeyValue($top_via);
    if ($ip =~ /^(.+)\:(.+)$/) {
        $ip = $1;
        $port = $2;
    }
    $ip = $via_params->{received} if $via_params->{received} =~ /^[0-9\.]+$/;
    $port = $via_params->{rport} if $via_params->{rport} =~ /^\d{4,5}$/;

    # Finally send out the packet
    log(L_INFO, "Sending reply transformed to 180 Ringing to $ip:$port");
    sendSipMessage($ip, $port, $new_header);
    return 1;
}

###
# Send a given SIP message to given IP and port
##
sub sendSipMessage {
    my $ip = shift;
    my $port = shift;
    my $msg = shift;
    my $sock = new IO::Socket::INET (
        PeerAddr  => $ip, 
        PeerPort  => $port,
        Proto     => 'udp',
        LocalPort => '5060',
        ReuseAddr => '1'
    );
    return unless $sock;
    print $sock $msg;
    close($sock);
}

```
