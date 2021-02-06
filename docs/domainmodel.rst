.. toctree::
   :maxdepth: 4

.. include:: references.rst
.. _routedomainmodel:

==================
Route Domain Model
==================

.. _Sector Handbook: http://taf-jsg.info/wp-content/uploads/2019/10/190604_js_handbook_2.0_with_xsd_2.2.3_0.pdf
.. _JSG: http://taf-jsg.info/

--------
Overview
--------

Each international train has to be split into sections when the train crosses a border.  The split
locations are called handover points. At each handover the responsibility for the train planning
changes from IM to IM and RU to RU. The planning process is coordinated by the `RoutingInfo
.lead_ru`.

This `UML class diagram`_ [#f1]_ shows the main concepts involved:

.. uml:: uml/tom-01-overview.puml
   :caption: Overview Routing Model

An international :class:`~tom.tom.Train` [#f2]_ must at least have two sections. All
`RouteSections` of a train are bundled in a `RoutingInfo`. The *Lead RU* is responsible for
the correctness and communication of this information to all involved companies. The
following constraint must hold for each :class:`~tom.tom.RouteSection`:

.. admonition:: Rule SEC-JL Journey Locations

   - `RouteSection.departure_station` is a *Origin* or *Handover*
   - `RouteSection.arrival_station` is a *Handover* or *Destination*

For each `RouteSection` the `planning_im` and `applicant_ru` exchange *PathRequest* and
*PathDetails* to plan the detailed route within a `RouteSection`. This process is described in
detail in the `Sector Handbook`_ of the RU/IM Telematrics JSG_.  As long as borders of a section
both in location and time are unchanged no other participant in the planning of the whole train has
to be informed. See also `Routing Planning Process <routing-planning-process.html#routing-process>`_.

The following paragraph describes the minimal information which all companies involved must know
about the `RoutingInfo`. Changes to this information have to be propagated by the lead RU.

-----------------------------------
Train, RoutingInfo and RouteSection
-----------------------------------

The following diagramm shows the three main classes of our proposition for the Route Domain Model. It
describes the minimum information needed for a valid route information of an international train:

.. uml:: uml/tom-02-section.puml
   :caption: RoutingInfo and RouteSection

A train has zero or one `RoutingInfo` which bundles the information in `RouteSections`. The version
is incremented each time one or more RouteSections have changed.

Timestamps
~~~~~~~~~~

This model completely describes a planned set of *train runs*. Each train run is a sequence of
*section runs* which have to connect properly in time at handover points. The timing attributes of
a `RouteSection` serve this purpose:

- `calendar` is a set of calendar days where the train starts at `RouteSection.departure_station`
- `departure_time` is the day time the train starts each day in `calendar`
- `departure_stop_time` planned stop time at a section handover station of departure
- `travel_time` travel time from section station of departure to section station
  of arrival. This attribute is used to calculate the arrival time at station of arrival.

Only RouteSections have a calendar.  This is the set of starting days at the departure_station of a section.
All timestamps in Train, TrainRun and SectionRuns (see next chapter) are calculated from these timing
attributes.

.. admonition:: Rule SEC-CAL RouteSection Calendar must be subset of timetable year

   The `RouteSection.calendar` must be a subset of the timetable year of its train.

.. _Example with three IMs: auto_examples/plot_a_f.html

Because a train can have several starting RouteSections (i.e. different departure stations and
dates) it makes no sense to assign a calender to a train. A calender must always be relativ to a fixed
start location. `Example with three IMs`_ explains such a situation with an overnight train in the
starting sections.

Working with only timestamps also avoids the difficulties with overnight trains. No OTR (*Offset To
Reference*) is needed!

Calendars
~~~~~~~~~

In our model these classes have a calendar:

* A RouteSection defines the planned daily runs of a train
* A PathRequest is planned for a RouteSection
* A Path is created in response to a PathRequest of an RU to an IM

.. uml:: uml/tom-02-calendars.puml
   :caption: Calendars of RouteSection, PathRequest and Path

The following rules must hold for a consistent set of paths of a train:

.. admonition:: Rule SEC-CAL Section-PathRequest-Path calendar relationships

   * The calendar of a PathRequest must be a subset of the calendar of the section it is planned for.
   * The calendar of a Path must be a subset of the calendar the PathRequest it is a response.
   * The calendars of two different PathRequests of a RouteSection must be pairwise disjoint.
   * The calendars of two different Paths of a PathRequest must be pairwise disjoint.
   * The calender of a RouteSection must be the union of the calendars of its PathRequests.
   * The calender of a PathRequest must be the union of the calendars of its Paths.

The last two rules must hold when the path allocation process is finished. The other must always
hold. Objects that violate these conditions must not be communicated among partners. Such messages
have to be answered with an `ErrorMessage`.

Identifiers
~~~~~~~~~~~

The method Train :meth:`~tom.tom.Train.train_id` computes the unique trainID from `core_id`, `lead_ru` and
`timetable_year`.

.. admonition:: Rule SEC-UID Unique Section ID

   :meth:`RouteSection.section_id <tom.tom.RouteSection.section_id>` must be unique within the set
   of sections of a train.

The `section_id` is used to make the daily train IDs unique in case of overnight trains. Using the
start date of a train results in duplicate train IDs. See example below.

.. admonition:: Rule SEC-UFK Unique functional key of sections

   A route section of a train is uniquely identified by this quadruple:

   `((section.departure_station, section.departure_time), (section.arrival_station, section.arrival_time))`

Therefore, if on some day in the calendar of a section the train from section station of departure
`AC` to section station of arrival `EMM`
should arrive at at different time at `EMM`, the RU has to define a new RouteSection for
this day. If `EMM` is a handover, the lead RU must ask the applicant RU of the following section to
create fitting route section with section station of departure `EMM`.

section_id can be considered as a technical id to identify the section easily among the sections of a train.
The quatruble (=section_key()) is a functional key, which ensures the consistency of the model (Rule SEC-UFK).
There must be a 1:1 correspondence between section_key() and section_id.

Versioning
~~~~~~~~~~

We suggest *versioning* of trains and sections to support the synchronisation of the domain model
between the systems of the cooperating companies. If the lead RU changes a section its
`RouteSection.version` is incremented. Same with the `RoutingInfo.version`. The receiver of a message
containing the RoutingInfo [#f3]_ can use this information to identify the change and act
accordingly.

-----------------------
TrainRun and SectionRun
-----------------------

In this section we describe, how the daily train (i.e. a `TrainRun`) and section runs are computed
from the routing info of a `Train` described in the previous section.

- A :class:`~tom.tom.SectionRun` is derived for each day in the calendar of its `RouteSection`
- A :class:`~tom.tom.TrainRun` is computed from SectionRuns that *fit* together. Two sections `s, t`
  fit together if `s.connects_to(t) == True` (see :meth:`~tom.tom.SectionRun.connects_to`).

.. uml:: uml/tom-03-section-run.puml

SectionRun
~~~~~~~~~~

For each day in day in `RouteSection.calendar` a section run is created. All `SectionRuns` of a
section differ only in the value of :meth:`~tom.tom.SectionRun.departure_time`, which is the only
information stored in a SectionRun. All other values shown can be computed from this timestamp and
the attributes of the section the run belongs to.

TrainRun
~~~~~~~~

Whereas the section runs can easily computed from information in its RouteSection (mainly calendar
and departure time at section station of departure), the train runs must be computed from all
possible SectionRun sequences that fit together.

We use a graph algorithm to compute all train runs. The graph used is best described by the examples
shown below. The central methods are:

* :meth:`~tom.tom.Train.train_run_graph` which computes a directed Graph G = (SectionRun, E), where
  (s,t) in E <=> s.connects_to(t).
* :meth:`~tom.tom.Train.extended_train_run_graph` which adds to synthetic vertices to G, one at the
  beginning (`START`) connecting to departure stations of SectionRuns and one at the end (`END`)
  which connects to all stations of arrival of SectionRuns.
* :meth:`~tom.tom.Train.train_run_iterator` which computes all TrainRuns out of all path in G from
  `START` to `END`.


.. rubric:: Footnotes

.. [#f1] We use PlantUML_ as modeling tool. See explanations there.
.. [#f2] Click on the link to see the python source code for the code element
.. [#f3] Train and RouteSections could be transported in the TAF/TAP `TrainInformation` message
         structure.
