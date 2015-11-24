Architecture
============

Overview
^^^^^^^^

ICaaS is a service for creating OS images for Synnefo. A user may do an OS
image creation request by providing an image URL and his Synnefo authentication
token. The service will validate the token by using Synnefo's Identity
Management Service (`Astakos <https://www.synnefo.org/docs/synnefo/latest/astakos.html>`_)
and if the token is valid, it will create a special purpose Agent VM on the
Synnefo deployment to carry out the request. The VM will download the original
OS image from the user provided URL and will make changes on its format and
content to make it suitable for using it with Synnefo. Then, it will upload it,
together with the image creation log, to `Pythos
<https://www.synnefo.org/docs/synnefo/latest/pithos.html>`_ and will register
it on `Cyclades <https://www.synnefo.org/docs/synnefo/latest/cyclades.html>`_
on behalf of the user. After the image creation process has finished, the Agent
VM will contact back the service and will inform it about the creation process.
The final step is the destruction of this special-purpose VM.

The following figure shows a detailed flow of the ICaaS image creation process:

.. code-block:: javascript

                                              .------------------.
                                              | Kamaki or web UI |
                                              '------------------'
                                                        |
                                                        |
                                                        |1) Image creation request
                                                        |
                                                        |
                                                        |
                                                        v           2) Is the token the
                                                .---------------.   user provided valid?
                                                |               |------------------------.
                                                |               |                        v
                                                |               |           .------------------------.
                           .------------------->| ICaaS Service |           | Astakos (Auth Service) |
                           |                    |               |           '------------------------'
                           |                    |               |                        |
                           |                    |               |<-----------------------'
                           |                    '---------------'   3) Yes, proceed
                           |                      |           |
                           |                      |           |
                           |      9) Destroy ICaaS|           | 4) Create ICaaS Agent
                           |      Agent VM        |           | VM, inject manifest
                           |                      |           |
                           |                      |           |
        8) Build completed |                      v           v
        successfully       |              .----------------------------.
                           |              | Cyclades (Compute Service) |
                           |              '----------------------------'
                           |                             |
                           |                             | 5) Cyclades create
                           |                             | the ICaaS Agent VM
    .---------------------------------------------.      |
    | Virtual Machine                             |      |
    | Accounted and billed to the user            | <----'
    |                                             |
    |      .--------------------------------------.
    |      | ICaaS-Agent                          |                   .---------.
    |      | Running inside the VM                | 6) Download Image |         |
    |      |                                      |------------------>| Bitnami |
    |      |                                      |<------------------|         |
    |      |                                      |                   '---------'
    |      |                                      |
    |      |                                      |
    |      |                                      |
    |      |                                      |
    '------'--------------------------------------'
                          |
                          | 7) Upload Image (diskdump)
                          | and creation logs. Register
                          | Image to Plankton
                          v
          .-------------------------------.
          | Pithos (BlockStorage Service) |
          '-------------------------------'


As you may have noticed from the figure above, the software has 2 main
components:

1. A service which exposes an API to serve user requests
2. An agent that is hosted in a Cyclades registered OS image that gets
   deployed on a temporary VM.

We will describe each one of those components below, after we discuss the goals
that led us to this design.

Design Goals
^^^^^^^^^^^^

ICaaS was designed to work in a way that would require:

1. minimal resources for the service itself
2. no changes to the Synnefo stack
3. minimal user interaction

In order to achieve the first goal, the service does not use a separate
Identity Management infrastructure. The user needs to provide his Synnefo
credentials and the service will allocate the necessary resources by making
calls to Synnefo on behalf of him.

In a way this is how the second goal is also reached. The Agent VM that does
the actual image creation is deployed by cloning a public predefined image and
is accounted to the user as if he had manually launched it. When the resulting
image is created, the ICaaS Agent will upload and register it to Synnefo on
behalf of the user. Once again, from the Synnefo's perspective, the user
himself has uploaded and registered the image.

The third goal is archived through the simplicity of the interface. The only
required information to create a new image is a source URL and a name.


ICaaS Service
^^^^^^^^^^^^^

The ICaaS service is a RESTful service written in `Flask
<http://flask.pocoo.org/>`_ for manipulating OS image *builds*. A *build* in
the ICaaS context is a way to represent the image creation process. Whenever a
user requests a new image creation, the ICaaS service will create a new *build*
object in its database and will set its state to *CREATING*. If the image
gets created through the process that is already described, the state of the
*build* object that refers to this image creation will turn to *COMPLETED*.
If the user cancels the image creation, the state will be set to *CANCELED*
and if an error occurs, the build state will turn to *ERROR*.

The *builds* associated with a user are managed through the ICaaS REST API,
either by the UI or by any other API client. Through the API, a user may create
new images, view the state of older creation attempts or cancel an image
creation. The UI is written in Javascript/Ember.js and runs entirely on the
client side for maximum responsiveness. All UI operations happen with
asynchronous calls over the API.

For a complete API reference, check :ref:`api-reference`.

ICaaS Agent
^^^^^^^^^^^

The agent is the heart of the ICaaS software stack. It's a `Python
<https://www.python.org>`_ program that will download a source image and will
use `snf-image-creator
<https://www.synnefo.org/docs/snf-image-creator/latest/index.html>`_ in
conjunction with some bitnami-oriented scripts to prepare and register the
image on the Synnefo deployment. During its operation, it will also monitor the
whole process, inform the ICaaS service about the progress as well as upload a
detailed log file on Pithos. The overall progress is computed using heuristics
on the I/O of the system the agent runs on.

The image preparation process will:

* Shrink the file system of the image
* Lock all open accounts
* Add code that will run in the first boot to:

  - Update the image software
  - Regenerate SSH keys
  - Enable Remote access
  - Install network managing software
* Convert it to raw format as needed by Synnefo

The manifest file
-----------------

The agent software expects to receive a configuration file as input that is
typically named `manifest.cfg`. This manifest may look like the one below:

.. code-block:: ini 

  [manifest]
  url = https://icaas.synnefo.org/icaas/builds/1/<random_nonce>

  [service]
  status = https://icaas.synnefo.org/icaas/builds/1
  token = ********************************
  insecure = False
  
  [synnefo]
  url = https://accounts.synnefo.org/identity/v2.0
  token = *******************************************
  
  [image]
  src = https://downloads.bitnami.com/files/stacks/wordpress/4.1.2-0/bitnami-wordpress-4.1.2-0-ubuntu-14.04.zip
  name = WordPress
  container = images
  object = wordpress-4.1.2-0.diskdump
  description = WordPress 4.1.2
  public = False
  
  [log]
  container = icaas
  object = wordpress-4.1.2-0.diskdump.log

For security reasons, in latest versions of ICaaS, only the `manifest` section
is present in the manifest. The agent may use the url provided there to fetch
all the other sections. The `service` section hosts information on how to
contact the ICaaS service to report the status. The Authentication URL of a
Synnefo deployment and the user's token are listed under the `synnefo` section.
The `image` section hosts the source URL as well as information about the
resulting image. Finally, the `log` section points to the Pithos location where
the log file will be uploaded.

The Agent VM
------------

As we have already mentioned, the ICaaS service will execute the agent by
launching the agent VM. On this VM, the agent will start as a daemon during the
boot process and will expect to find the manifest file in
`/etc/icaas/manifest.cfg`. This file is injected there by the service during
the VM creation.
