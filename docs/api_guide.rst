.. _api-guide:

ICaaS REST API Guide
^^^^^^^^^^^^^^^^^^^^

This is ICaaSs' REST API Guide.

API Operations
==============

.. rubric:: ICaaS

======================================= ===================== ======
Description                             URI                   Method
======================================= ===================== ======
`List <#list-builds>`_                  ``/icaas``            GET
`Create <#start-build>`_                ``/icaas``            POST
`Get Details <#get-build>`_     ``/icaas/<build-id>`` GET
`Update Status <#update-build>`_        ``/icaas/<build-id>`` PUT
======================================= ===================== ======

List Builds
-----------

List all image builds owned by the user.

.. rubric:: Request

========== ======
URI        Method
========== ======
``/icaas`` GET
========== ======
|
================ =========================
Request Header   Value
================ =========================
X-Auth-Token     User authentication token
================ =========================

.. rubric:: Response

=========================== =============================================
Return Code                 Description
=========================== =============================================
200 (OK)                    Request succeeded
400 (Bad Request)           Invalid or malformed request
401 (Unauthorized)          Missing or expired user token
403 (Forbidden)             User is not allowed to perform this operation
500 (Internal Server Error) The request cannot be completed because of an
\                           internal error
503 (Service Unavailable)   The server is not currently available
=========================== =============================================

|

Response body contents::

  builds: [
    {
      <build attribute>: <value>,
      ...
    }, ...
  ]

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


Start Build
-----------

Start a new build

.. rubric:: Request

========== ======
URI        Method
========== ======
``/icaas`` POST
========== ======

|
==============  =========================
Request Header  Value
==============  =========================
X-Auth-Token    User authentication token
Content-Type    Type or request body
Content-Length  Length of request body
==============  =========================

Request body contents::

  {
    <build attribute>: <value>,
    ...
  }

================= ================ ============================
Build Attribute   Required         Value
================= ================ ============================
name              ✔                String
url               ✔                Bitnami Image URL
image             ✔                Pithos image location
log               ✔                Agent log location on Pithos
================= ================ ============================

.. rubric:: Response

=========================== =============================================
Return Code                 Description
=========================== =============================================
200 (OK)                    Request succeeded
400 (Bad Request)           Invalid or malformed request
401 (Unauthorized)          Missing or expired user token
403 (Forbidden)             User is not allowed to perform this operation
500 (Internal Server Error) The request cannot be completed because of an
\                           internal error
503 (Service Unavailable)   The server is not currently available
=========================== =============================================

Get Build
---------

Get build details

.. rubric:: Request

===================== ======
URI                   Method
===================== ======
``/icaas/<build-id>`` GET
===================== ======

|
==============  =========================
Request Header  Value
==============  =========================
X-Auth-Token    User authentication token
================ =========================

.. code-block:: javascript

    {
      "build": {
        "created": "Wed, 29 Jul 2015 08:26:03 GMT",
        "deleted": false,
        "id": 1,
        "image": "pithos/123",
        "links": [
          {
            "href": "http://example.org/icaas/1",
            "rel": "self"
          }
        ],
        "log": "pithos/123.log",
        "name:": "ICAAS-new-update",
        "src": "https://image.example.org/files/stacks/redmine/3.0.3-0/example-redmine-3.0.3-0-ubuntu-14.04.zip",
        "status": "ERROR",
        "updated": "Wed, 29 Jul 2015 08:26:03 GMT"
    }

.. rubric:: Response

=========================== =============================================
Return Code                 Description
=========================== =============================================
200 (OK)                    Request succeeded
400 (Bad Request)           Invalid or malformed request
401 (Unauthorized)          Missing or expired user token
403 (Forbidden)             User is not allowed to perform this operation
500 (Internal Server Error) The request cannot be completed because of an
\                           internal error
503 (Service Unavailable)   The server is not currently available
=========================== =============================================

Update Build
------------

Update build status and reason. This is normally to be used only by the
ICaaS-agent.

.. rubric:: Request

================================= ======
URI                               Method
================================= ======
``/icaas/<build-id>``             PUT
================================= ======

|

==============  ==========================
Request Header  Value
==============  ==========================
X-ICaaS-Token   ICaaS authentication token
==============  ==========================

Request body contents::

   {
      status: <status>,
      reason: <reason>
   }

================= ================ ======================
Build Attribute   Required         Value
================= ================ ======================
status            ✔                "COMPLETED", "ERROR"
reason            **✘**            String up to 255 chars
================= ================ ======================

.. rubric:: Response

=========================== =============================================
Return Code                 Description
=========================== =============================================
200 (OK)                    Request succeeded
400 (Bad Request)           Invalid or malformed request
401 (Unauthorized)          Missing or expired user token
403 (Forbidden)             User is not allowed to perform this operation
500 (Internal Server Error) The request cannot be completed because of an
\                           internal error
503 (Service Unavailable)   The server is not currently available
=========================== =============================================
