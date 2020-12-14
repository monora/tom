.. toctree::
   :maxdepth: 4

==================
Route Domain Model
==================

.. _Sector Handbook: http://taf-jsg.info/wp-content/uploads/2019/10/190604_js_handbook_2.0_with_xsd_2.2.3_0.pdf
.. _JSG: http://taf-jsg.info/

--------
Overview
--------

Each international train has to be split into sections when the train crosses a border.  The split
locations are called handover points. At each handover the responsiblity for the train planning
changes from IM to IM and RU to RU. The planning process is coordinated by the `Train.lead_ru`.

.. uml:: tom-overview.puml

An international :class:`~tom.tom.Train` [#f1]_ must at least have two sections. The
following constraint must hold for each :class:`~tom.tom.RouteSection`:

.. admonition:: Rule SEC-01 Journey Locations

   - `RouteSection.origin` is a *Origin* or *Handover*
   - `RouteSection.destination` is a *Handover* or *Destination*

For each `RouteSection` the `responsible_im` and `applicant_ru` exchange *PathRequest* and
*PathDetails* to plan the detailed route within a `RouteSection`. This process is described in
detail in the `Sector Handbook`_ of the RU/IM Telematrics JSG_.  As long as borders of a section
both in location and time are unchanged no other participant in the planning of the whole train has
to be informed.

The following paragraph describes the minimal information which all companies involved must know
about the whole train. Changes to this information have to be propagated by the lead RU.

----------------------
Train and RouteSection
----------------------

The following diagramm shows the two main classes of our proposition for the TOM. It describes the
minimum information needed for a valid route information of an international train:

.. uml:: tom-section.puml

Timestamps
~~~~~~~~~~

This model completely describes a planned set of *train runs*. Each train run is a sequence of
*sections runs* which have to connect properly in time at handover points. The timing attributes of
a `RouteSection` serve this purpose:

- `calendar` is a set of calendar days where the train starts at `RouteSection.origin`
- `origin_departure_time` is the day time the train starts each day in `calendar`
- `origin_stop_time` planned stop time at a section handover origin
- `travel_time_to_destination` travel time from origin to destination. This attribute is used to
  calculate the arrival time at destination.

Only RouteSections have a calendar.  This is the set of starting days at the origin of a section.
All timestamps in Train, TrainRun and SectionRuns (see next chapter) are calculated from the timing
attributes.

.. :admonition:: Rule SEC-02 RouteSection Calendar must be subset of timetable year

   The `RouteSection.calendar` must be a subset of the timetable year of its train.

Because a train can have several starting RouteSections (i.e. different start locations and dates)
it makes no sense to assign a calender to it. A calender must always be relativ to a fixed start
location. :ref:`example-ac-ff` explains such a situation with an overnight train in the starting
sections.

Working with only timestamps also avoids the difficulties with overnight trains. No OTR (*Offset To
Reference*) is needed!

Identifiers
~~~~~~~~~~~

The method Train :meth:`~tom.tom.Train.train_id` computes the unique trainID from `core_id`, `lead_ru` and
`timetable_year`.

.. admonition:: Rule SEC-03 Unique Section ID

   :meth:`RouteSection.section_id <tom.tom.RouteSection.section_id>` must be unique within the set
         of sections of a train.

The `section_id` is used to make the daily train IDs unique in case of overnight trains. Using the
start date of a train results in duplicate train IDs. See example below.

.. admonition:: Rule SEC-04 Unique functional key of sections

   A route section of a train is uniquely identified by this quadruple:

   `((origin, departure time), (destination, arrival time))`

Therefor, if on some day in the calendar of a section the train from `origin `AC` to destination `EMM`
should arrive at at different time at `EMM`, the RU has to define a new RouteSection for
this day. If `EMM` is a handover, the lead RU must ask the RU of the following section to create
fitting route section with origin `EMM`.

Versioning
~~~~~~~~~~

We suggest *Versioning* of trains and sections to support the synchronsisation of the domain model
between the systems of the cooperating companies. If a company make a change of section its
`RouteSection.version` is incremented. Same with the `Train.version`. The receiver of a message
containing the RoutingInfo [#f2] can use this information to identify the change and act accordingly.

-----------------------
TrainRun and SectionRun
-----------------------

In this section we describe, how the daily train and section runs are computed from the routing
info of a `Train` described in the previous section.

- A :class:`~tom.tom.SectionRun` is derived for each day in the calendar of its `RouteSection`
- A :class:`~tom.tom.TrainRun` is computed from SectionRuns that *fit* together. Two sections `s, t`
  fit together if `s.connects_to(t) == True` (see :meth:`~tom.tom.SectionRun.connects_to`).

.. uml:: tom-section-run.puml

SectionRun
~~~~~~~~~~

For each day in day in `RouteSection.calendar` a section run is created. All `SectionRuns` of a
section differ only in the value of :meth:`~tom.tom.SectionRun.departure_at_origin`, which is the
only information stored in the SectionRun. All other values shown can be computed from this an the
section the run belongs to.

TrainRun
~~~~~~~~

Whereas the section runs can easily computed from information in its RouteSection (mainly calendar
and departure time at section origin), the train runs must be computed from all possible SectionRun
sequences that fit together.

We use a graph algorithm to compute all train runs. The graph used is best described by the examples
shown below. The central methods are:

* :meth:`~tom.tom.Train.train_run_graph` which computes a directed Graph G = (SectionRun,E), where
  (s,t) in E <=> s.connects_to(t).
* :meth:`~tom.tom.Train.extended_train_run_graph` which adds to synthetic vertices to G, one at the
  beginning (`START` connecting origin SectionRuns and one at the end `END` which connects to all
  destination SectionRuns.
* :meth:`~tom.tom.Train.train_run_iterator` which computes all TrainRuns out of all path in G from
  `START` to `END`.

.. _example-ac-ff:

------------------------------------------
Example: Train from Amsterdam to Frankfurt
------------------------------------------

This object diagramm shows a szenario for a train vom Ammsterdam Central (AC) to Frankfurt (FF)
which is planned to operate in december 2012. On Fri-Sun handover is Emmerich (EMM). On Mon-Thu
handover is Venlo.

.. uml:: tom-example.puml


YAML-Example
~~~~~~~~~~~~

The following YAML-file is a machine readable specification of the route sections of the example:

.. literalinclude:: ../tests/data/train-ac-ff.yml
   :language: yaml
   :linenos:

TrainRun Graph
~~~~~~~~~~~~~~

The resulting *TrainRun-Graph* can be calculated with
:meth:`~tom.tom.Train.extended_train_run_graph` and looks like this:

.. figure:: /example-ac-ff-train-run-graph.png
   :alt: Example train run graph

With :meth:`~tom.tom.Train.to_dataframe` you can create an pandas dataframe which you can export to
execl. See :download:`/train-TR-12AB-1.xlsx`.

.. rubric:: Footnotes

.. [#f1] Click on the link to see the python source code for the code element
.. [#f2] Train and RouteSections could be transported in the TAF/TAP `TrainInformation` message
         structure.
