"""
Example Train Annex 4 v2
========================

Version 2 of example annex 4

"""
from networkx import DiGraph

from tom.util import example, dump_routing_info_as_xml
from tom.tom import make_train_from_yml, TrainRun, RouteSection, Route
from tom.plot import *

# %%
# Load example annex 4 version 2 from yaml specification
pattern = 'annex-4-2'
_, t_spec_file = example('../tests/data', pattern)
print(t_spec_file.read_text())

# %%
#
# Now create train object and show its train id.
t = make_train_from_yml(t_spec_file)
t.train_id()

# %%
# Timetable
# ^^^^^^^^^
#
df = t.to_dataframe()
df

# %%
# Bildfahrplan
# ^^^^^^^^^^^^
# Show timetable
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
print(dump_routing_info_as_xml(t))
