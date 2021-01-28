"""
Example: Night Train from Amsterdam to Zürich
=============================================

*Standard schedule* 2021/22 from Amsterdam over Emmerich, Basel to Zürich (a single route) on
fridays, saturdays and sundays::

    Route     : XNAC-EEM-RXBA-XSZH
    Calendar  : 12/12/2021 to 12/12/2022 Fri, Sat, Sun
    Start   at: 20:00 in XNAC
    Arrival at: 21:30 in EEM
    Arrival at: 03:30 in RXBA
    Arrival at: 04:30 in XSZH

*Update schedule* due to construction work between Amsterdam and Utrecht on sundays from
12/04/2022 on:

The train on sundays starts in Utrecht with destination Basel and handover Venlo.
Therefore we need to routes from April on: ::

    Route     : XNAC-EEM-RXBA-XSZH
    Calendar  : 12/04/2022 to 12/12/2022 Fri, Sat
    Start   at: 20:00 in XNAC
    Arrival at: 21:30 in EEM
    Arrival at: 03:30 in RXBA
    Arrival at: 04:30 in XSZH

    Route     : XNU-XNVL-RXBA
    Calendar  : 12/04/2022 to 12/12/2022 Sun
    Start   at: 20:30 in XNU
    Arrival at: 22:00 in XNVL
    Arrival at: 04:00 in RXBA
"""
from tom.plot import plot_train, plot_graph
from tom.tom import make_train_from_yml, TrainRun, RouteSection, Route
from tom.util import example, dump_routing_info_as_xml

# %%
# Standard schedule (version 1)
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# Load example night train 2021/22 standard schedule (version 1) from yaml specification
_, t_spec_file = example('../tests/data', 'ac-zue-1')
print(t_spec_file.read_text())

# %%
# Create train object and show its train id
t = make_train_from_yml(t_spec_file)
t.train_id()

# %%
# Timetable V1
# ^^^^^^^^^^^^
# Show timetable as dataframe
df = t.to_dataframe()
df

# %%
# Bildfahrplan
# ^^^^^^^^^^^^
# Show timetable as plot.
# No sections from Utrecht over Venlo here.
stations = ['XNAC', 'XNU', 'EEM', 'XNVL', 'RXBA', 'XSZH']
plot_train(t, all_stations=stations)

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
# Version 1 has only one route with three sections.
route: Route
for route in t.routes():
    print(route.description(), "\n")

# %%
# Section runs
# ^^^^^^^^^^^^
# For each day of the calendar of a section a `SectionRun` is created.
# The section runs are the rows of RouteSection.to_dataframe.
# We only show the section run in december here.
for section in t.sections:
    print(f"{section.section_id}: {section}")
    print(section.to_dataframe(), "\n")

# %%
# TrainRuns
# ^^^^^^^^^
# Each `TrainRun` defines a row in the timetable of the train above.
tr: TrainRun
for tr in t.train_run_iterator():
    print(tr)
    for sr in tr.sections_runs:
        print(sr)
    print("\n")

# %%
# RoutingInformation as TrainInformation
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# An XML Dump of the routing information of version 1
print(dump_routing_info_as_xml(t))

# %%
# Update schedule (version 2)
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# Version 2 of the train contains the update from april on.
_, t_spec_file = example('../tests/data', 'ac-zue-2')
print(t_spec_file.read_text())
t = make_train_from_yml(t_spec_file)

# %%
# Timetable V2
# ^^^^^^^^^^^^
# Version 2 has train runs on sundays from Utrecht to Basel.
df = t.to_dataframe()
df

# %%
# Bildfahrplan
# ^^^^^^^^^^^^
# On sundays the trains only go to Basel from Utrecht over Venlo.
plot_train(t, all_stations=stations)

# %%
# Route Sections
# ^^^^^^^^^^^^^^
# To realize the schedule we need two new section (with ID 20 and 40)
# All oteher section have a new version 2, because the calender had to
# shortened by sunday.
section: RouteSection
for section in t.sections:
    print(section.description(), "\n")

# %%
# Section graph
# ^^^^^^^^^^^^^
# The section graph now has two new sections, which define the second route.
sg = t.section_graph()
plot_graph(sg)

# %%
# Routes
# ^^^^^^
# From april on we have one new route:
route: Route
for route in t.routes():
    print(route.description(), "\n")

# %%
# Section runs
# ^^^^^^^^^^^^
for section in t.sections:
    print(f"{section.section_id}: {section}")
    print(section.to_dataframe(), "\n")

# %%
# TrainRuns
# ^^^^^^^^^
tr: TrainRun
for tr in t.train_run_iterator():
    print(tr)
    for sr in tr.sections_runs:
        print(sr)
    print("\n")

# %%
# RoutingInformation as TrainInformation
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# An XML Dump of the routing information of version 1
print(dump_routing_info_as_xml(t))

