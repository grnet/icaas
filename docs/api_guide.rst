.. _api-guide:

ICaaS REST API Guide
^^^^^^^^^^^^^^^^^^^^

This is ICaaSs' REST API Guide.

API Operations
==============

.. rubric:: ICaaS

========================== ====================== ======
Description                URI                    Method
========================== ====================== ======
`List <#list-builds>`_     ``/icaas/builds``      GET
`Create <#create-build>`_  ``/icaas/builds``      POST
`View <#view-build>`_      ``/icaas/builds/<id>`` GET
`Update <#update-build>`_  ``/icaas/builds/<id>`` PUT
`Delete <#delete-build>`_  ``/icaas/builds/<id>`` DELETE
========================== ====================== ======

List Builds
-----------

List all image builds owned by the user.

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

.. rubric:: Response

+---------------------------+-----------------------------------------------+
|Return Code                |Description                                    |
+===========================+===============================================+
|200 (OK)                   | Request succeeded                             |
+---------------------------+-----------------------------------------------+
|400 (Bad Request)          | Invalid or malformed request                  |
+---------------------------+-----------------------------------------------+
|401 (Unauthorized)         | Missing or expired user token                 |
+---------------------------+-----------------------------------------------+
|500 (Internal Server Error)| The request cannot be completed because of an |
|                           | internal error                                |
+---------------------------+-----------------------------------------------+
|503 (Service Unavailable)  | The server is not currently available         |
+---------------------------+-----------------------------------------------+

|

Response body contents::

  {
    builds: [
      {
        <build attribute>: <value>,
        ...
      }, ...
    ]
  }
  
*Example List Builds: JSON*

.. code-block:: javascript

  GET https://example.org/icaas


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

Create a Build
--------------

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

=============== ======== ============================================
Build Attribute Required Value
=============== ======== ============================================
name            ✔        String
src             ✔        Bitnami Image URL
image           ✔        Pithos image location (dictionary)
image/account   **✘**    Account of the user to host the image on
image/container ✔	 Pithos container to host the image on
image/object    ✔        Name for the Pithos object of the image file
log             ✔        Agent log location on Pithos (dictionary)
log/account     **✘**    Account of the user to host the log on
log/container   ✔	 Pithos container to host the log on
log/object      ✔	 Name for the Pithos object of the log file
=============== ======== ============================================

.. rubric:: Response

+---------------------------+----------------------------------------------+
|Return Code                | Description                                  |
+===========================+==============================================+
|202 (Accepted)             | Request has been accepted for processing     |
+---------------------------+----------------------------------------------+
|400 (Bad Request)          | Invalid or malformed request                 |
+---------------------------+----------------------------------------------+
|401 (Unauthorized)         | Missing or expired user token                |
+---------------------------+----------------------------------------------+
|500 (Internal Server Error)| The request cannot be completed because of an|
|                           | internal error                               |
+---------------------------+----------------------------------------------+
|503 (Service Unavailable)  | The server is not currently available        |
+---------------------------+----------------------------------------------+

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

.. code-block:: javascript

    {
      "build": {
        "created": "Wed, 29 Jul 2015 08:26:03 GMT",
        "deleted": false,
        "id": 1,
        "image": {
          "account": "1ad2898a-5879-11e5-993e-1c6f65d381fb",
          "container": "pithos",
          "object": "image.diskdump"
        },
        "links": [
          {
            "href": "http://example.org/icaas/1",
            "rel": "self"
          }
        ],
        "log": {
          "account": "1ad2898a-5879-11e5-993e-1c6f65d381fb",
          "container": "log",
          "object": "log.txt"
	},
        "name:": "ICAAS-new-update",
        "src": "https://image.example.org/files/stacks/redmine/3.0.3-0/example-redmine-3.0.3-0-ubuntu-14.04.zip",
        "status": "ERROR",
        "updated": "Wed, 29 Jul 2015 08:26:03 GMT"
    }

.. rubric:: Response

+---------------------------+---------------------------------------------+
|Return Code                |Description                                  |
+===========================+=============================================+
|200 (OK)                   |Request succeeded                            |
+---------------------------+---------------------------------------------+
|400 (Bad Request)          |Invalid or malformed request                 |
+---------------------------+---------------------------------------------+
|401 (Unauthorized)         |Missing or expired user token                |
+---------------------------+---------------------------------------------+
|404 (Not Found)            |The requested build was not found            |
+---------------------------+---------------------------------------------+
|500 (Internal Server Error)|The request cannot be completed because of an|
|                           |internal error                               |
+---------------------------+---------------------------------------------+
|503 (Service Unavailable)  |The server is not currently available        |
+---------------------------+---------------------------------------------+

Update Build
------------

Update build status and reason. This is normally to be used only by the
ICaaS-agent.

.. rubric:: Request

====================== ======
URI                    Method
====================== ======
``/icaas/builds/<id>`` PUT
====================== ======

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

+---------------------------+---------------------------------------------+
|Return Code                |Description                                  |
+===========================+=============================================+
|200 (OK)                   |Request succeeded                            |
+---------------------------+---------------------------------------------+
|400 (Bad Request)          |Invalid or malformed request                 |
+---------------------------+---------------------------------------------+
|401 (Unauthorized)         |Missing or expired user token                |
+---------------------------+---------------------------------------------+
|404 (Not Found)            |The requested build does not exist           |
+---------------------------+---------------------------------------------+
|500 (Internal Server Error)|The request cannot be completed because of an|
|                           |internal error                               |
+---------------------------+---------------------------------------------+
|503 (Service Unavailable)  |The server is not currently available        |
+---------------------------+---------------------------------------------+

Update Build
------------

Update build status and reason. This is normally to be used only by the
ICaaS-agent.

.. rubric:: Request

====================== ======
URI                    Method
====================== ======
``/icaas/builds/<id>`` PUT
====================== ======

|

============== ===================================
Request Header Value
============== ===================================
X-ICaaS-Token  ICaaS internal authentication token
============== ===================================

Request body contents::

   {
      status: <status>,
      details: <details>
   }

================= ================ ==================================
Build Attribute   Required         Value
================= ================ ==================================
status            ✔                "CREATING", "COMPLETED" or "ERROR"
details           **✘**            String up to 255 chars
================= ================ ==================================

.. rubric:: Response

+---------------------------+---------------------------------------------+
|Return Code                |Description                                  |
+===========================+=============================================+
|200 (OK)                   |Request succeeded                            |
+---------------------------+---------------------------------------------+
|400 (Bad Request)          |Invalid or malformed request                 |
+---------------------------+---------------------------------------------+
|401 (Unauthorized)         |Missing or expired user token                |
+---------------------------+---------------------------------------------+
|404 (Not Found)            |The requested build does not exist           |
+---------------------------+---------------------------------------------+
|500 (Internal Server Error)|The request cannot be completed because of an|
|                           |internal error                               |
+---------------------------+---------------------------------------------+
|503 (Service Unavailable)  |The server is not currently available        |
+---------------------------+---------------------------------------------+

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

Request body contents::

   {
   }

.. rubric:: Response

+---------------------------+---------------------------------------------+
|Return Code                |Description                                  |
+===========================+=============================================+
|200 (OK)                   |Request succeeded                            |
+---------------------------+---------------------------------------------+
|400 (Bad Request)          |Invalid or malformed request                 |
+---------------------------+---------------------------------------------+
|401 (Unauthorized)         |Missing or expired user token                |
+---------------------------+---------------------------------------------+
|404 (Not Found)            |The requested build does not exist           |
+---------------------------+---------------------------------------------+
|500 (Internal Server Error)|The request cannot be completed because of an|
|                           |internal error                               |
+---------------------------+---------------------------------------------+
|503 (Service Unavailable)  |The server is not currently available        |
+---------------------------+---------------------------------------------+

