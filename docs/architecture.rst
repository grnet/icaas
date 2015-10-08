.. _architecture:

Architecture
^^^^^^^^^^^^

ICaaS was designed to work in a way that:

    * would require minimal changes to the Synnefo software
    * would impact a Synnefo installation as little as possible
    * would require minimal user interaction

The following figure shows a detailed flow for creating an image using ICaaS.

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


The above procedure in more detail:

    1) Using either the web UI or the Kamaki client, a POST request is made on the ICaaS server with a temporary user token.
    2) The ICaaS service, using the Kamaki library, enquires Astakos for the validity of the token.
    3) Astakos either verifies the user or denies him access.
    4) The ICaaS server, using the Kamaki lirabary once again and the aforementioned token, instructs Cyclades to create a new VM -billed and accounted to the owner of the token- and inject into the VM the needed `ICaaS-Agent <https://github.com/grnet/icaas-agent>`_ manifest file.
    5) Cyclades spawn the VM.
    6) The ICaaS-Agent running inside the newly creted VM, reads the manifest file, downloads the image from the user provided url and runs `snf-image-creator <https://www.synnefo.org/docs/snf-image-creator/latest/>`_ on it.
    7) snf-image-creator, creates the image locally, uploads it to Pithos and registers it to Plankton.
    8) The VM uses a special ICaaS token found in the manifest to inform the ICaaS server that the build is over.
    9) The ICaaS server instructs Cyclades to destroy the VM. Image creation has finished successfully.
