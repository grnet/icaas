.. _api-guide:

ICaaS REST API Guide
^^^^^^^^^^^^^^^^^^^^

This is ICaaSs' REST API Guide.

API Operations
==============

.. rubric:: ICaaS

====================================== ============================ ======
Description                            URI                          Method
====================================== ============================ ======
`Create <#create-build>`_              ``/icaas/builds``            POST
`List <#list-builds>`_                 ``/icaas/builds``            GET
`View <#view-build>`_                  ``/icaas/builds/<id>``       GET
`Update <#update-build>`_              ``/icaas/builds/<id>``       PUT
`Agent Update <#agent-update-build>`_  ``/icaas/builds/agent/<id>`` PUT
`Delete <#delete-build>`_              ``/icaas/builds/<id>``       DELETE
====================================== ============================ ======

Create Build
------------

Create a new image build

.. rubric:: Request

================= ======
URI               Method
================= ======
``/icaas/builds`` POST
================= ======

|

============== =========================
Request Header Value
============== =========================
X-Auth-Token   User authentication token
Content-Type   Type or request body
Content-Length Length of request body
============== =========================

Request body contents::

  {
    build:
      {
        <build attribute>: <value>,
        ...
      }
  }

=============== ======== ================================================
Build Attribute Required Value
=============== ======== ================================================
name            ✔        Registration name for the resulting image
src             ✔        Bitnami Image URL
image           ✔        Pithos image location (dictionary)
image/account   **✘**    Account of the user to host the image on
image/container ✔	 Pithos container to host the image on
image/object    ✔        Name for the Pithos object of the image file
log             ✔        Agent log location on Pithos (dictionary)
log/account     **✘**    Account of the user to host the log on
log/container   ✔	 Pithos container to host the log on
log/object      ✔	 Name for the Pithos object of the log file
description     **✘**    Image Description (up to 256 characters)
public          **✘**    Should the image be registered as public? (true|false)
project         **✘**    ID of the project to assign the agent VM to
networks        **✘**    A list of network dictionaries. Check the
                         create_server() method of kamaki.clients.compute
                         for more info
=============== ======== ================================================

.. rubric:: Response

=========================== =============================================
Return Code                 Description
=========================== =============================================
202 (Accepted)              Request has been accepted for processing
400 (Bad Request)           Invalid or malformed request
401 (Unauthorized)          Missing or expired user token
500 (Internal Server Error) The request cannot be completed because of an
                            internal error
503 (Service Unavailable)   The server is not currently available
=========================== =============================================

|

Response body contents::

  {
    "build": {
        <build attribute>: <value>,
        ...
    }
  }

|

Example Create Build Response:

.. code-block:: javascript

  {
    "build": {
      "created": "Wed, 23 Sep 2015 09:57:47 GMT",
      "id": 1,
      "image": {
        "container": "images",
        "object": "wordpress.diskdump"
      },
      "links": [
        {
          "href": "http://example.org/icaas/builds/1",
          "rel": "self"
        }
      ],
      "log": {
        "container": "log",
        "object": "wordpress.log"
      },
      "name:": "wordpress",
      "src": "https://downloads.bitnami.com/files/stacks/wordpress/4.1.2-0/bitnami-wordpress-4.1.2-0-ubuntu-14.04.zip",
      "status": "CREATING",
      "status_details": "build request accepted",
      "updated": "Wed, 23 Sep 2015 09:57:47 GMT"
    }
  }


List Builds
-----------

List image builds owned by the user.

.. rubric:: Request

================= ======
URI               Method
================= ======
``/icaas/builds`` GET
================= ======

|

============== =========================
Request Header Value
============== =========================
X-Auth-Token   User authentication token
============== =========================

|

============== ======== ===========================================
List Attribute Required Value
============== ======== ===========================================
status         **✘**    Only display Builds that are in this status
                        (*CREATING*, *COMPLETED*, *ERROR*)
details        **✘**    Display details for each build (1|0)
============== ======== ===========================================


.. rubric:: Response

=========================== =============================================
Return Code                 Description
=========================== =============================================
200 (OK)                    Request succeeded
400 (Bad Request)           Invalid or malformed request
401 (Unauthorized)          Missing or expired user token
500 (Internal Server Error) The request cannot be completed because of an
                            internal error
503 (Service Unavailable)   The server is not currently available
=========================== =============================================

|

Response body contents::

  {
    "builds": [
      {
        <build attribute>: <value>,
        ...
      }, ...
    ]
  }

Example List Builds response:

.. code-block:: javascript

  {
    "builds": [
      {
        "links": [
          {
            "href": "https://example.org/icaas/42",
            "rel": "self"
          }
        ],
        "id": "42",
        "name": "My Image",
      }, {
        "links": [
          {
            "href": "https://example.org/icaas/43",
            "rel": "self"
          }
        ],
        "id": "84",
        "name": "My Image 2",
      }
    ]
  }


View Build
----------

View details for a build

.. rubric:: Request

====================== ======
URI                    Method
====================== ======
``/icaas/builds/<id>`` GET
====================== ======

|

============== =========================
Request Header Value
============== =========================
X-Auth-Token   User authentication token
============== =========================

.. rubric:: Response

=========================== =============================================
Return Code                 Description
=========================== =============================================
200 (OK)                    Request succeeded
400 (Bad Request)           Invalid or malformed request
401 (Unauthorized)          Missing or expired user token
404 (Not Found)             The requested build was not found
500 (Internal Server Error) The request cannot be completed because of an
                            internal error
503 (Service Unavailable)   The server is not currently available
=========================== =============================================

Response body contents::

  {
    "build": {
      <build attribute>: <value>,
      ...
    }
  }

Example View Build response:

.. code-block:: javascript

  {
    "build": {
      "created": "Tue, 22 Sep 2015 15:56:04 GMT",
      "id": 1,
      "image": {
        "container": "images",
        "object": "wordpress.diskdump"
      },
      "links": [
        {
          "href": "http://example.org/icaas/builds/1",
          "rel": "self"
        }
      ],
      "log": {
        "container": "log",
        "object": "wordpress.log"
      },
      "name:": "wordpress",
      "src": "https://downloads.bitnami.com/files/stacks/wordpress/4.1.2-0/bitnami-wordpress-4.1.2-0-ubuntu-14.04.zip",
      "status": "ERROR",
      "status_details": "agent: Image creation failed. Check the log for more info",
      "updated": "Tue, 22 Sep 2015 16:00:06 GMT"
    }
  }


Update Build
------------

Perform an action on an active build. For now, the only valid action is
`cancel`.

.. rubric:: Request

====================== ======
URI                    Method
====================== ======
``/icaas/builds/<id>`` PUT
====================== ======

|

============== =========================
Request Header Value
============== =========================
X-Auth-Token   User authentication token
============== =========================

Request body contents::

   {
      status: <status>
   }

================= ================ ======
Build Attribute   Required         Value
================= ================ ======
action            ✔                cancel
================= ================ ======

.. rubric:: Response

=========================== ==================================================
Return Code                 Description
=========================== ==================================================
204 (No Content)            Request succeeded
400 (Bad Request)           Invalid or malformed request
401 (Unauthorized)          Missing or expired user token
403 (Forbidden)		    The request is not active. Updating is not allowed
404 (Not Found)             The requested build does not exist
500 (Internal Server Error) The request cannot be completed because of an
                            internal error
503 (Service Unavailable)   The server is not currently available
=========================== ==================================================

Agent Update Build
------------------

Update build status and reason. This is to be used by the ICaaS Agent.

.. rubric:: Request

============================ ======
URI                          Method
============================ ======
``/icaas/builds/agent/<id>`` PUT
============================ ======

|

============== ===================================
Request Header Value
============== ===================================
X-ICaaS-Token  ICaaS internal authentication token
============== ===================================

Request body contents::

   {
      status: <status>,
      reason: <reason>
   }

================= ================ ==================================
Build Attribute   Required         Value
================= ================ ==================================
status            ✔                "CREATING", "COMPLETED" or "ERROR"
details           **✘**            String up to 255 chars
================= ================ ==================================

.. rubric:: Response

=========================== =============================================
Return Code                 Description
=========================== =============================================
204 (No Content)            Request succeeded
400 (Bad Request)           Invalid or malformed request
401 (Unauthorized)          Missing or expired user token
404 (Not Found)             The requested build does not exist
500 (Internal Server Error) The request cannot be completed because of an
                            internal error
503 (Service Unavailable)   The server is not currently available
=========================== =============================================

Delete Build
------------

Delete an existing finished or unfinished build. (This will not delete the
created image)

.. rubric:: Request

====================== ======
URI                    Method
====================== ======
``/icaas/builds/<id>`` DELETE
====================== ======

|

======================== ===================================
Request Header           Value
======================== ===================================
X-Auth-Token             User authentication token
======================== ===================================

.. rubric:: Response


=========================== =============================================
Return Code                 Description
=========================== =============================================
204 (No Content)            Request succeeded
400 (Bad Request)           Invalid or malformed request
401 (Unauthorized)          Missing or expired user token
404 (Not Found)             The requested build does not exist
500 (Internal Server Error) The request cannot be completed because of an
                            internal error
503 (Service Unavailable)   The server is not currently available
=========================== =============================================

