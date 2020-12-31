==================
Train Object Model
==================

.. _TOM Jupyter Notebook: https://mybinder.org/v2/gh/monora/tom/master?filepath=notebooks%2Ftom.ipynb
.. _Gitpod: https://gitpod.io/#https://github.com/monora/tom

.. ..image:: https://img.shields.io/pypi/v/tom.svg
        :target: https://pypi.python.org/pypi/tom

.. ..image:: https://img.shields.io/travis/monora/tom.svg
        :target: https://travis-ci.org/monora/tom

.. ..image:: https://readthedocs.org/projects/tom/badge/?version=latest
        :target: https://monora.github.io/tom
        :alt: Documentation Status

.. image:: https://mybinder.org/badge_logo.svg
   :target: `TOM Jupyter Notebook`_

.. image:: https://img.shields.io/badge/Gitpod-ready--to--code-blue?logo=gitpod
   :target: `Gitpod`_
   :alt: Gitpod Ready-to-Code

.. _JSG: http://taf-jsg.info/
.. _Route Domain Model: https://monora.github.io/tom/domainmodel.html
.. _Example 1: https://monora.github.io/tom/domainmodel.html#example-train-from-amsterdam-to-frankfurt
.. _Example 2: https://monora.github.io/tom/domainmodel.html#example-train-with-three-ims
.. _Example 3: https://monora.github.io/tom/domainmodel.html#example-train-annex-4

This repository contains a proposition to extend the *Combined Route Model* of the JSG_ *Train Object
Model*. See `Route Domain Model`_.

We provide examples which can be tested and investigated. See

* `Example 1`_ Train from Amsterdam to Frankfurt over two different handovers
* `Example 2`_ Train with three IMs involved
* `Example 3`_ Train example of Working Group Annex 4

License
~~~~~~~

Free software: MIT license

Installation:
-------------

.. warning::
   This project is not yet released to PyPi

.. code-block:: console

    $ pip install tom

Features
--------

You can try out the library with:

* `TOM Jupyter Notebook`_ (no account necessary)
* `Gitpod`_ Github account needed. You get a VS-Code workspace with all libraries installed.

Credits
-------

This package was created with Cookiecutter_ and the `monora/cookiecutter-pypackage-poetry`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`monora/cookiecutter-pypackage-poetry`: https://github.com/monora/cookiecutter-pypackage-poetry
