"""
Example Train Annex 4 v1
========================

A train with three routes each composed of two sections.

Given this infrastructure:

.. uml:: ../uml/tom-06-example-annex-4-infrastructure.puml

The following routing specification describes the initial planned routes for the rain with
`ID1`.  As
you can see, there is no route section needed which mentions Station `M`. This station does not play
a role in the routing planning process because it is no origin, destination or handover.

"""
from networkx import DiGraph

from tom.util import example, dump_routing_info_as_xml
from tom.tom import make_train_from_yml, TrainRun, RouteSection, Route
from tom.plot import *

# %%
# Load example annex 4 from yaml specification
#
_, t_spec_file = example('../tests/data', 'annex-4.yml')
print(t_spec_file.read_text())

# %%
# Notice the route sections which have a departure time.
# These are considered as *route construction starts*.
# Only one section in a route may be a construction start.
#
# Now create train object and show its train id.
t = make_train_from_yml(t_spec_file)
t.train_id()

# %%
# Timetable
# ^^^^^^^^^
#
# This is the timetable of version 1 of TR-ID1. Notice the two train runs with ID
# `TR/8350/ID1/10/2021/2021-02-07` and `TR/8350/ID1/20/2021/2021-02-07`. They both start on
# `07/02`. To make the daily train ID unique on this operating day, we propose to add the
# `section_id` to be
# part of `TrainRun.train_id()`. Here `10` for the train starting at `00:10` and `20` for the
# train departing at `23:50` at station `S`.
df = t.to_dataframe()
df

# %%
# Bildfahrplan
# ^^^^^^^^^^^^
# Show timetable as `Bildfahrplan <https://de.wikipedia.org/wiki/Bildfahrplan`>_.
plot_train(t)

# %%
# Route Sections
# ^^^^^^^^^^^^^^
# From which sections the train is composed?
section: RouteSection
for section in t.sections:
    print(section.description(), "\n")

# %%
# Section graph
# ^^^^^^^^^^^^^
# The section graph is computed using the successor relation.
sg: DiGraph = t.section_graph()
plot_graph(sg)

# %%
# Routes
# ^^^^^^
# Print all possible routes.
# Routes are calculated from all possible paths in the section graph.
route: Route
for route in t.routes():
    print(route.description(), "\n")

# %%
# Section runs
# ^^^^^^^^^^^^
# For each day of the calendar of a section a `SectionRun` is created.
# The section runs are the rows of RouteSection.to_dataframe:
for section in t.sections:
    print(f"{section.section_id}: {section}")
    print(section.to_dataframe(), "\n")

# %%
# TrainRuns
# ^^^^^^^^^
# Each `TrainRun` defines a row in the timetable of the train above
tr: TrainRun
for tr in t.train_run_iterator():
    print(tr)
    for sr in tr.sections_runs:
        print(sr)
    print("\n")

# %%
# RoutingInformation as TrainInformation
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# An XML Dump of the routing information of this example according a new version of the TSI XSD.
#
# See `Routing planning <../routing-planning-process.html#routininformation-as-traininformation>`_
# for more details.
dump_routing_info_as_xml(t)
