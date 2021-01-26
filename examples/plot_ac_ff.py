"""
Example: Train from Amsterdam to Frankfurt
==========================================

Here we investigate the routing specification for example from
`train-ac-ff-v1.yml`.

Given this infrastructure:

.. uml:: ../uml/tom-04-example-ac-ff-infrastructure.puml

This object diagramm shows a szenario for a train from AC to Frankfurt FF which is planned to
operate in december 2021. On Fri-Sun handover is EMM. On Mon-Thu handover is Venlo.

.. uml:: ../uml/tom-04-example-ac-ff.puml

.. _Pandas DataFrame: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html
"""
from tom.plot import plot_train, plot_graph
from tom.tom import make_train_from_yml, TrainRun, RouteSection, Route
from tom.util import example, dump_routing_info_as_xml

# %%
# Load example 4 from yaml specification
pattern = 'ac-ff-v1'
train_specs, t_spec_file = example('../tests/data', pattern)
print(t_spec_file.read_text())

# %%
# Create train object and show its train id.
t = make_train_from_yml(t_spec_file)
t.train_id()

# %%
# Timetable
# ^^^^^^^^^
#
# With :meth:`~tom.tom.Train.to_dataframe` you can create a `Pandas DataFrame`_ which you can
# export to excel.
df = t.to_dataframe()
df

# %%
# Bildfahrplan
# ^^^^^^^^^^^^
# Show timetable as plot
plot_train(t)

# %%
# Show only the first week
plot_train(t, no_of_runs=7)

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
# The section graph is computed using the successor relation:

sg = t.section_graph()
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
