.. toctree::
   :maxdepth: 4

.. include:: references.rst
.. _routeplanningprocess:

========================
Routing Planning Process
========================

--------
Overview
--------


----------------------------------------
Example: Route Planning of Train Annex 4
----------------------------------------

The initial planned routing of Train `ID1` was described in `example-annex-4-1`_

Specification with YAML
~~~~~~~~~~~~~~~~~~~~~~~

The following routing specification describes the planned final status.

.. literalinclude:: ../tests/data/train-annex-4-2.yml
   :language: yaml

.. _example-annex-4-2:

TrainRun Graph
~~~~~~~~~~~~~~

.. figure:: examples/example-annex-4-2-train-run-graph.png
   :alt: Example train run graph Annex 4 final state

   TrainRun graph of example Annex 4 final planning status.

You can download this graph as GraphML_ here: :download:`examples/train-TR-ID1-2.graphml`.


Timetable as Excel-Sheet
~~~~~~~~~~~~~~~~~~~~~~~~

Download the time table for `Train-13AB` here: :download:`examples/train-TR-ID1-2.xlsx`.

.. rubric:: Footnotes
