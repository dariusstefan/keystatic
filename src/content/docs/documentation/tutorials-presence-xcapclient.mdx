---
title: "Xcap_client module"
description: "Presence_xml module assumes that in the database table 'xcap' there is always the newest version of an xcap document that he has previously sent a request fo..."
---

## Exported Parameters
* *db_url(str)*: database URL
* *xcap_table(str)*: the name of the database table used for storing the XCAP documents retrieved from the XCAP servers
* *periodical_query(int)*: flag to disable periodical query as a method of checking if an update for a stored document occurred on the server; if this flag is unset, the server must have the capability to announce an update by issuing the exported MI command - **refreshXcapDoc**
* *query_period(int)*: the time interval in seconds at which the servers will be queried for updates (used if periodical_query flag is set)

---

## Developer's Guide
This module represents an XCAP client interface for OpenSIPS with retrieving capabilities only. It is meant to be used by other OpenSIPS modules that use XCAP storage. Now this module is used by **presence_xml** and **rls** modules. 

**Presence_xml and xcap_client interaction(when integrated_xcap_client parameter is not set)**  

Presence_xml module assumes that in the database table 'xcap' there is always the newest version of an xcap document that he has previously sent a request for to xcap_client module.
When a searched document is not found in the table, a request is sent to the xcap_client module, saying it to retrieve the document from the xcap server in future synchronize the version in the database table with that on the server, by calling the function **getNewDoc**.

The API contains the following functions:

* xcap_get_elem_t **get_elem**
->typedef char* (***xcap_get_elem_t**)(xcap_get_req_t req, char** etag);
->This function retrieves an element from the excap server( either a hole document or a node from the document. 

* xcapGetNewDoc_t getNewDoc; 
->typedef char* (*xcapGetNewDoc_t)(xcap_get_req_t req, str user, str domain);
->This function is a request to fetch the document indicated in the request strucuture and handle its update. Calling this function will ensures that in the database table will always be the updated version of the document.  

->The argument of the two functions is a structure containing the request. It has the following fields:
  * char* **xcap_root**:    the path to the location where the XCAP documetns are stored ( includes the server address and the local path; ex: http://xcap-server.com/xcap-root/)
  * unsigned **int port**: the port where the server is listening , if different than default 80
  * xcap_doc_sel_t **doc_sel**: a structure that indicates the selection of the document
  * xcap_node_sel_t* **node_sel**: a structure that indicates the selection of the node inside the document 
  * char* **etag**: an XCAP etag
  * int **match_type**: the way to use the etag for selection in the HTTP request; it can be IF_MATCH or IF_NONE_MATCH. 

The **xcap_doc_sel_t** has the following structure:
  * str auid: application defined Unique ID
  * int doc_type: the document type ; if can have one of the values: PRES_RULES, RESOURCE_LIST, RLS_SERVICE, PIDF_MANIPULATION.
  * int type: the type of the path segment after the AUID  which must either be GLOBAL_TYPE (for "global") or USERS_TYPE (for "users")
  * str xid: the XCAP User Identifier if type is USERS_TYPE
  * str filename: the name of the file 
Example: 
For selecting a presence authorization rules document the strucuture is filed like this:
	xcap_doc_sel_t doc_sel;

	doc_sel.auid.s= "presence-rules";
	doc_sel.auid.len= strlen("presence-rules");
	doc_sel.doc_type= PRES_RULES;
	doc_sel.type= USERS_TYPE;
	doc_sel.xid= uri;
	doc_sel.filename.s= "index";
	doc_sel.filename.len= 5;

The **xcap_node_sel_t**  structure that identifies a node from a document can be constructed using functions from the API:
* xcap_nodeSel_init_t **int_node_sel**: initializeaza o structura de tip 
->typedef xcap_node_sel_t* (***xcap_nodeSel_init_t** )(void);

* xcap_nodeSel_add_step_t **add_step** : add
->typedef xcap_node_sel_t* (***xcap_nodeSel_add_step_t**)(xcap_node_sel_t* curr_sel, str* name, str* namespace, int pos, attr_test_t*  attr_test, str* extra_sel);
->The **attr_test** in the parameters list is to be used in case an attribute test should be made to select the node. The definition of the structure is:
->typedef struct att_test
->`{`
->	str name;
->	str value;
->`}`attr_test_t;

* xcap_nodeSel_add_terminal_t add_terminal;
->typedef xcap_node_sel_t* (*xcap_nodeSel_add_terminal_t)(xcap_node_sel_t* curr_sel, char* attr_sel, char* namespace_sel, char* extra_sel );

* xcap_nodeSel_free_t free_node_sel;
->typedef void (*xcap_nodeSel_free_t)(xcap_node_sel_t* node);

There is also one function which allows registering a callback to be called by the module when a change occurs in a document:
* register_xcapcb_t register_xcb; /* function to register a callback to document changes*/

---

## Module Readme
You can read the modules's readme here .
