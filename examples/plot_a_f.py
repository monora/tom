"""
Example: Train with three IMs
=============================

Here we investigate the routing specification for example from
`train-a-f.yml`
"""
from tom.plot import plot_train, plot_graph
from tom.tom import make_train_from_yml, TrainRun, RouteSection, Route
from tom.util import example

# %%
# Load example 4 from yaml specification
pattern = 'a-f.yml'
_, t_spec_file = example('../tests/data', pattern)
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
# Bildfahrplan
# ^^^^^^^^^^^^
# Show timetable as plot
stations = sorted(t.all_stations())
plot_train(t, all_stations=stations)

# %%
# Show only the first week
plot_train(t, no_of_runs=7, all_stations=stations)

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
# Each `TrainRun` defines a row in the timetable of the train above.
tr: TrainRun
for tr in t.train_run_iterator():
    print(tr)
    for sr in tr.sections_runs:
        print(sr)
    print("\n")
