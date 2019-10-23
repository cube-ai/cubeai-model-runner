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

===================================
Acumos Python Model Runner Tutorial
===================================

This tutorial demonstrates how to use the Acumos Python model runner with an example model.

Creating A Model
================

An Acumos model must first be defined using the `Acumos Python client library <https://pypi.org/project/acumos/>`__. For illustrative purposes, a simple model with deterministic methods is defined below.

.. code:: python

    # example_model.py
    from collections import Counter

    from acumos.session import AcumosSession
    from acumos.modeling import Model, List, Dict

    def add(x: int, y: int) -> int:
        '''Adds two numbers'''
        return x + y

    def count(strings: List[str]) -> Dict[str, int]:
        '''Counts the occurrences of words in `strings`'''
        return Counter(strings)

    model = Model(add=add, count=count)

    session = AcumosSession()
    session.dump(model, 'example-model', '.')

Executing ``example_model.py`` results in the following directory:

.. code:: python

    .
    ├── example_model.py
    └── example-model


Running A Model
===============

Now the ``acumos_model_runner`` command line tool can be used to run the saved model.

.. code:: bash

    $ acumos_model_runner example-model/
    [2018-08-08 12:16:57 -0400] [61113] [INFO] Starting gunicorn 19.9.0
    [2018-08-08 12:16:57 -0400] [61113] [INFO] Listening at: http://0.0.0.0:3330 (61113)
    [2018-08-08 12:16:57 -0400] [61113] [INFO] Using worker: sync
    [2018-08-08 12:16:57 -0400] [61151] [INFO] Booting worker with pid: 61151

Using A Model
=============

The model HTTP API can be explored via its generated Swagger UI. The Swagger UI of ``example-model`` above can be accessed by navigating to ``http://localhost:3330`` in your web browser.

Below are some screenshots of the Swagger UI for ``example-model``.

Model APIs
----------

The Swagger UI enumerates model method APIs, as well as APIs for accessing model artifacts. Below, the APIs corresponding to the ``add`` and ``count`` methods are listed under the ``methods`` tag.

|Model APIs|

.. |Model APIs| image:: https://gerrit.acumos.org/r/gitweb?p=python-model-runner.git;a=blob_plain;f=docs/tutorial/example-model-apis.png;hb=HEAD

Count Method API
----------------

Expanding the documentation for the ``count`` method reveals more information on how to invoke the API.

|Model Method|

.. |Model Method| image:: https://gerrit.acumos.org/r/gitweb?p=python-model-runner.git;a=blob_plain;f=docs/tutorial/example-model-method.png;hb=HEAD

Count Method Request
--------------------

The Swagger UI provides an input form that can be used to try out the ``count`` API with sample data.

|Model Method Request|

.. |Model Method Request| image:: https://gerrit.acumos.org/r/gitweb?p=python-model-runner.git;a=blob_plain;f=docs/tutorial/example-model-request.png;hb=HEAD

Count Method Response
---------------------

The response from the ``count`` API shows that everything is working as expected!

|Model Method Response|

.. |Model Method Response| image:: https://gerrit.acumos.org/r/gitweb?p=python-model-runner.git;a=blob_plain;f=docs/tutorial/example-model-response.png;hb=HEAD
