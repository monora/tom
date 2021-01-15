"""
Example Train Annex 4
=====================

Here we investigate the routing specification for example from
`train-annex-4.yml`
"""
from tom.util import example
from tom.tom import make_train_from_yml, TrainRun, RouteSection, Route
from tom.plot import plot_train

# %%
# Load example annex 4 from yaml specification
# Notice the route sections which have a departure time.
# These are considered as route construction starts
# Only one section in a route may be a construction start.
pattern = 'annex-4.yml'
train_specs, t_spec_file = example('../tests/data', pattern)
print(t_spec_file.read_text())

# %%
# Create train object and show its train id.
t = make_train_from_yml(t_spec_file)
t.train_id()

# %%
# Timetable
# ^^^^^^^^^
# Show timetable as dataframe
df = t.to_dataframe()
df

# %%
# .. _Bildfahrplan: https://de.wikipedia.org/wiki/Bildfahrplan
# `Bildfahrplan`_
# ^^^^^^^^^^^^^^
# Show timetable as plot
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
# The section graph is computed using the successor relation:

sg = t.section_graph()
print(sg.edges)

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
