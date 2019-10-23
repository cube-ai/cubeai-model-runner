.. ===============LICENSE_START=======================================================
.. Acumos CC-BY-4.0
.. ===================================================================================
.. Copyright (C) 2017-2018 AT&T Intellectual Property & Tech Mahindra. All rights reserved.
.. ===================================================================================
.. This Acumos documentation file is distributed by AT&T and Tech Mahindra
.. under the Creative Commons Attribution 4.0 International License (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..      http://creativecommons.org/licenses/by/4.0
..
.. This file is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.
.. ===============LICENSE_END=========================================================

=====================================
Acumos Python Model Runner User Guide
=====================================

|Build Status|

.. |Build Status| image:: https://jenkins.acumos.org/buildStatus/icon?job=python-model-runner-tox-verify-master
   :target: https://jenkins.acumos.org/job/python-model-runner-tox-verify-master/

The ``acumos_model_runner`` package installs a command line tool ``acumos_model_runner`` for running models created by the `Acumos Python client library <https://pypi.org/project/acumos/>`__.

The model runner provides an HTTP API for invoking model methods, as well as a `Swagger UI <https://swagger.io/tools/swagger-ui/>`__ for documentation. See the tutorial for more information on usage.

Installation
============

You will need a Python 3.4+ environment in order to install ``acumos_model_runner``.
You can use `Anaconda <https://www.anaconda.com/download/>`__
(preferred) or `pyenv <https://github.com/pyenv/pyenv>`__ to install and
manage Python environments.

The ``acumos_model_runner`` package can be installed with pip:

.. code:: bash

    $ pip install acumos_model_runner

Command Line Usage
==================

.. code:: bash

    usage: acumos_model_runner [-h] [--host HOST] [--port PORT]
                               [--workers WORKERS] [--timeout TIMEOUT]
                               [--cors CORS]
                               model_dir

    positional arguments:
      model_dir          Directory containing a dumped Acumos Python model

    optional arguments:
      -h, --help         show this help message and exit
      --host HOST        The interface to bind to
      --port PORT        The port to bind to
      --workers WORKERS  The number of gunicorn workers to spawn
      --timeout TIMEOUT  Time to wait (seconds) before a frozen worker is
                         restarted
      --cors CORS        Enables CORS if provided. Can be a domain, comma-
                         separated list of domains, or *
