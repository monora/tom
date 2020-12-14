.. highlight:: shell

============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every little bit
helps, and credit will always be given.

You can contribute in many ways:

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/monora/tom/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help
wanted" is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

Train Object Model could always use more documentation, whether as part of the
official Train Object Model docs, in docstrings, or even on the web in blog posts,
articles, and such.

The documentation is created using PlantUml_ with the help of the Sphinx_ extension
sphinxcontrib-plantuml_. See configuration in :file:`/conf.py`:

.. literalinclude:: /conf.py
   :start-after: @begin sphinx-extensions
   :end-before: @end sphinx-extensions
   :emphasize-lines: 5

See also:

* `Why Sphinx and RST are the best`_
* `PlantUML dev workflow`_

.. _sphinxcontrib-plantuml: https://pypi.org/project/sphinxcontrib-plantuml
.. _PlantUml: https://plantuml.com/en/class-diagram
.. _Sphinx: https://pythonhosted.org/an_example_pypi_project/sphinx.html
.. _Why Sphinx and RST are the best: https://evaparish.com/blog/2018/10/19/why-sphinx-and-rst-are-the-best
.. _PlantUML dev workflow: https://docs-as-co.de/news/plantuml-markdown-code-gitlab-github-integration


Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at https://github.com/monora/tom/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Get Started!
------------

Ready to contribute? Here's how to set up `Train Object Model` for local development.

1. Fork the `Train Object Model` repo on GitHub.
2. Clone your fork locally::

    $ git clone git@github.com:your_name_here/Train Object Model.git

3. Install your local copy into a virtualenv using poetry. Assuming you have poetry installed, this is how you set up your fork for local development::

    $ cd tom/
    $ poetry install
    $ poetry shell

4. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

5. When you're done making changes, check that your changes pass flake8 and the
   tests, including testing other Python versions with tox::

    $ flake8 tom tests
    $ tox

   To get flake8 and tox, just pip install them into your virtualenv.

6. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in README.rst.
3. The pull request should work for Python 2.7, 3.4, 3.5 and 3.6, and for PyPy. Check
   
   
   and make sure that the tests pass for all supported Python versions.

Tips
----

To run a subset of tests::

$ poetry run pytest tests/


Deploying
---------

A reminder for the maintainers on how to deploy.
Make sure all your changes are committed (including an entry in HISTORY.rst).
Then run::

$ bump2version patch # possible: major / minor / patch
$ git push
$ git push --tags

Travis will then deploy to PyPI if tests pass.

Deploying Documentation
-----------------------

For now we deploy the documention manually to GitHub pages:

.. code-block:: console

   cd $TOM_DIR # where tom project ist cloned
   make clean docs
   cd ..
   git clone https://github.com/monora/tom.git --branch gh-pages --single-branch gh-pages
   cp -r $TOM_DIR/docs/_build/html/* gh-pages
   cd gh-pages
   git add .
   git ci -m'Update documentation'
   git push
   
   
