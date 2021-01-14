import matplotlib.pyplot as plt
import networkx as nx

from tom.tom import Train, TrainRun

plt.rcParams["xtick.bottom"] = plt.rcParams["xtick.labelbottom"] = False
plt.rcParams["xtick.top"] = plt.rcParams["xtick.labeltop"] = True
# Set figure size in inches
plt.rcParams['figure.figsize'] = 24 / 2.54, 20 / 2.54


class SectionColorChooser:
    no_colors = len(plt.rcParams['axes.prop_cycle'])
    section2color = {}
    last_section = -1

    def get_color_for_section(self, section):
        result = self.section2color.get(section, None)
        if result is None:
            self.last_section += 1
            self.section2color[section] = result = self.last_section
        return f"C{result}"


def plot_train(t: Train, no_of_runs=-1, plot_all=True):
    sc_chooser = SectionColorChooser()
    fig, ax = plt.subplots()
    plt.grid(True)
    all_stations = list(nx.topological_sort(t.location_graph()))
    first_date = t.calender()[0]
    all_ts = [first_date for s in all_stations]
    plt.gca().invert_yaxis()
    ax.set_title(f"Timetable {t.train_id()} v{t.version}")
    ax.set_ylabel("Timestamps")
    ax.set_xlabel("From Origins over Handovers to Destinations")
    ax.plot(all_stations, all_ts, linestyle='None')
    trs = sorted(list(t.train_run_iterator()), key=TrainRun.start_date)
    no_of_runs = len(trs) if no_of_runs < 0 else no_of_runs
    last_section = None
    tr: TrainRun
    for tr in trs[:no_of_runs]:
        stations, tt = tr.time_table_events()
        current_section = tr.first_run().section
        if plot_all or current_section != last_section:
            c = sc_chooser.get_color_for_section(current_section)
            marker = 'D' if current_section.is_construction_start else '.'
            ax.plot(stations, tt, marker=marker, color=c)
        last_section = current_section
    plt.show()
