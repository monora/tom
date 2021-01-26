.. toctree::
   :maxdepth: 4

.. include:: references.rst

.. _routing-process:

========================
Routing Planning Process
========================

--------
Overview
--------

The routing planning process starts with a first version of a `RoutingInfo` of a train. For each
version and each section the `Path Planning Process` between `ApplicantRU` and `ResponseIM` of the
section is carried out until the section is completely *covered* with allocated paths. We use an
`UML sequence diagram`_ to describe the message flow:

.. uml:: uml/rp-05-basic-msg-exchange-pattern.puml
   :caption: Basis message exchange pattern between involved parties

If in between the participants find out, that a planned version of a RoutingInfo cannot be
constructed, a new version is created and communicated by the `LeadRU` to the `ApplicantRUs`
(Harmonisation). These in turn inform their `ResponseIMs` with each `PathRequest` containing also
the new version of the `RoutingInfo`.

The `Path Planning Process` for each defined section has then to start over again. This must only be
done for sections with a new version or totally new sections.

.. _example-annex-4-2:

----------------------------------------
Example: Route Planning of Train Annex 4
----------------------------------------

.. _Example Train Annex 4: auto_examples/plot_annex_4.html#bildfahrplan

The initial planned routing of Train `ID1` is shown in `Example Train Annex 4`_.

Planning Process for version 1
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following messages have to be exchanged by the involved companies to begin the planning process
for this train.

.. uml:: uml/rp-10-initial-setup.puml
   :caption: Initial message flow to build path consistent with routing info

For various reasons this process could not be finished. A second RoutingInfo version RI-v2 for the
train must now be communicated by the lead RU, which is specified in the next chapter.

RoutingInfo of example Annex 4 v2
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. _Example Train Annex 4 Version 2: auto_examples/plot_annex_4_v2.html#bildfahrplan
.. _section graph version 2: auto_examples/plot_annex_4_v2.html##section-graph

The updated routing info specification describes the planned final status. You can download it here:
:download:`../tests/data/train-annex-4-2.yml`.
See `Example Train Annex 4 Version 2`_ for details.

Look at the resulting new section graph to see the differences (marked in yellow):

.. figure:: examples/example-annex-4-2-section-graph.png
   :alt: Section graph Annex 4 version 2

   Section graph Annex 4 version 2

Planning Process for version 2
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following messages have to be exchanged by the involved companies to reach the state defined by
version 2 of the routing info:

.. uml:: uml/rp-20-route-update.puml
   :caption: Message flow to build path consistent with routing info version 2

The updated routing info specification describes the planned final status. You can download it here:
:download:`../tests/data/train-annex-4-2.yml`.

--------------------------------------
RoutingInformation as TrainInformation
--------------------------------------

As stated in the `JS Sector Handbook`_ chapter 8.2.3.1 the routing info of a train should contain
the minimum information of the routes of a train:

  The train object first comes into existence at the earliest planning phase when the RA starts to
  develop plans to run a train. The Lead RU creates the identification for the train at this
  stage. The Lead RU will then go through a harmonisation process with all RAs involved in the
  particular business case. They will then apply for paths to run the trains. The attributes of the
  object Train are:

  * Train route (geography, journey sections / locations, timing, indication of responsible RU
    and IM) The locations to be defined for the train route shall be at least:
    * origin of the train route
    * border points (Handover points, Interchange points)
    * destination of train route
  * Train parameters (weight, length)
  * Train calendar

   Shown here is the minimum requirement from the technical point of view. The technical details of
   the object Train are given in the XSD structure (see the current TAF/TAP XSD Schema / data
   catalogue see JSG web site http://taf_jsg.info/) within the element TrainInformation.

With the ECM we propose to fill the *TrainInformation* with the information contained in the
*RoutingInformation*. The minimum required information is contained in the set of sections. They
are mandatory. The routes computed from the sections can also be included in the
*TrainInformation* for information purpose.

Not necessary for the route planning phase are the *train parameters (weight, length)* as stated
in the SHB. A calendar can not be specified for the train but only at the route level.

.. _XSD Element TrainInformation: xsd/taf_cat_complete_sector_TrainInformation.html
.. _XSD Element TrainInformation 2.2.4: xsd/taf_cat_complete_sector_TrainInformationOld.html

Download the proposal for a new version 2.x of the XSD here:
:download:`../tests/data/xml/taf_cat_complete_sector.xsd`.

Have a look at the `XSD Element TrainInformation`_ and compare it to new previous version
`XSD Element TrainInformation 2.2.4`_. The main difference is that the calendars are attached to
the *RouteSection* and *Route* elements.

.. figure:: taf_cat_complete_sector.v2.3.0.png
   :alt: TrainInformation XSD

   XSD TrainInformation containing Routes and RouteSections

.. _TrainInformation Example Annex 4 V1: auto_examples/plot_annex_4.html#routinginformation-as-traininformation
.. _TrainInformation Example Annex 4 V2: auto_examples/plot_annex_4_2.html#routinginformation-as-traininformation

We have generated the new train information structures for the two version of the example above.
See

* `TrainInformation Example Annex 4 V1`_ the first version of the example above
* `TrainInformation Example Annex 4 V2`_ the update version 2

