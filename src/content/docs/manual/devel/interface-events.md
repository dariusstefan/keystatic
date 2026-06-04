---
title: "Events Interface"
description: "The Events Interface is an OpenSIPS interface that provides different ways to notify external applications about certain events triggered inside OpenSIPS."
---

The **Events Interface** is an OpenSIPS interface that provides different ways to notify external applications about certain events triggered inside OpenSIPS.

## Overview

In order to notify an external application about OpenSIPS internal events, the **Event Interface** provides the following functions:
* manages exported events
* manages subscriptions from different applications
* exports generic functions to raise an event (regardless the transport protocol used)
* communicates with different transport protocols to send the events

More detailed information about **OpenSIPS Event Interface** can be found in the [Event Interface Tutorial](/documentation/tutorials-eventinterface).

---

## Events

There are several types of events that can be exported by OpenSIPS:
* **Core events** - internal events that trigger changes of OpenSIPS core/global behavior. A full list of exported core events can be found [here](/manual/devel/interface-coreevents).
* **Modules events** - events triggered by each module, when loaded. Each module can export zero, one or more events. Details can be found in the [documentation page](/manual/devel/modules) of each module.
* **Custom events** - triggered from script using the [raise_event()](/manual/devel/script-corefunctions#raise_event) command.

---

## Transport Protocols

External applications can be notified about the events triggered using various transport protocols. While the interface itself is provided by OpenSIPS core, each transport protocol is implemented by a separate OpenSIPS module. Multiple transport modules can be loaded simultaneously in order to provide different ways of notifications.

Available transport protocols are :

* [event_datagram](http://www.opensips.org/html/docs/modules/4.1.x/event_datagram) - sends Datagrams over UDP or UNIX sockets
* [event_flastore](http://www.opensips.org/html/docs/modules/4.1.x/event_flatstore) - writes to plain text files
* [event_kafka](http://www.opensips.org/html/docs/modules/4.1.x/event_kafka) - sends events via Apache Kafka broker
* [event_rabbitmq](http://www.opensips.org/html/docs/modules/4.1.x/event_rabbitmq) - sends an AMQP message to a RabbitMQ server
* [event_route](http://www.opensips.org/html/docs/modules/4.1.x/event_route) - runs an OpenSIPS event_route in script
* [event_stream](http://www.opensips.org/html/docs/modules/4.1.x/event_stream) - sends a JSON-RPC command/notification over TCP
* [event_virtual](http://www.opensips.org/html/docs/modules/4.1.x/event_virtual) - aggregates event backends for failover and balancing
* [event_xmlrpc](http://www.opensips.org/html/docs/modules/4.1.x/event_xmlrpc) - sends a XML-RPC command over TCP

An external application can subscribe to any of the exported module and can be notified using any of the loaded transport modules/protocols.

---

## Events Subscription

You can subscribe for an event either at startup (using the [subscribe_event()](/manual/devel/script-corefunctions#subscribe_event) command in the script) or during runtime, using the [event_subscribe](/manual/devel/interface-coremi#event_subscribe) MI command.

---

## Examples

In order to configure a RabbbitMQ server to be notified when a custom event is triggered, first you have to subscribe it to the event, using the [subscribe_event()](/manual/devel/script-corefunctions#subscribe_event) command:

```c

    startup_route {
        subscribe_event("E_SCRIPT_CUSTOM_EVENT", "rabbitmq:127.0.0.1/opensips");
    }

```

Then, in order to trigger the event from the script, call the [raise_event()](/manual/devel/script-corefunctions#raise_event) command when needed:

```text

   ....
   raise_event("E_SCRIPT_CUSTOM_EVENT");     # raises an event without any parameters
   ...

```
