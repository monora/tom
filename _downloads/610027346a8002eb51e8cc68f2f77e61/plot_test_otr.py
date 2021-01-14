"""
Example showing OTR anomalie
============================

Here we investigate the routing specification for a train
with interesting OTRs.
"""
from tom.util import example
from tom.tom import make_train_from_yml, TrainRun, RouteSection
from tom.plot import plot_train

# %%
# Load example from yaml specification
pattern = 'otr-test'
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
