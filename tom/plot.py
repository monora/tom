import matplotlib.colors as mcolors
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import networkx as nx

from tom.tom import Train, TrainRun


def get_color_for_section(section):
    cmap = mcolors.CSS4_COLORS
    return cmap.get(section.color,
                    cmap['black'])


def annotate_train_run(ax: plt.Axes, tr: TrainRun):
    x = tr.first_run().departure_station()
    y = tr.first_run().departure_time
    text = y.strftime("%H:%M")
    ax.annotate(text, xy=(x, y))


def plot_train(t: Train, no_of_runs=-1, plot_all=True, all_stations=None):
    plt.rcParams["xtick.bottom"] = plt.rcParams["xtick.labelbottom"] = False
    plt.rcParams["xtick.top"] = plt.rcParams["xtick.labeltop"] = True
    # Set figure size in inches
    plt.rcParams['figure.figsize'] = 24 / 2.54, 20 / 2.54

    ax: plt.Axes
    fig, ax = plt.subplots()
    plt.grid(True, which='both')
    if all_stations is None:
        all_stations = list(nx.topological_sort(t.location_graph()))

    plt.gca().invert_yaxis()
    ax.set_title(f"Timetable {t.train_id()} v{t.version}")
    ax.set_ylabel("Time")
    ax.set_xlabel("From Origins over Handovers to Destinations")
    # Plot invisible line to get the complete x-axis
    first_date = t.calender()[0]
    all_ts = [first_date for s in all_stations]
    ax.plot(all_stations, all_ts, linestyle='None')

    trs = sorted(list(t.train_run_iterator()), key=TrainRun.start_date)
    no_of_runs = len(trs) if no_of_runs < 0 else no_of_runs
    tr: TrainRun
    for tr in trs[:no_of_runs]:
        for stations, tt, section in tr.time_table_event_iterator2():
            c = get_color_for_section(section)
            marker = 'D' if section.is_construction_start else '.'
            ax.plot(stations, tt, marker=marker, color=c)
        annotate_train_run(ax, tr)
    # format y-axis
    week_locator = mdates.WeekdayLocator(byweekday=mdates.SUNDAY)
    week_formatter = mdates.DateFormatter("%a %d/%m/%Y")
    day_locator = mdates.DayLocator()
    day_formatter = mdates.DateFormatter("%a %d")

    ax.yaxis.set_major_locator(week_locator)
    ax.yaxis.set_major_formatter(week_formatter)
    ax.yaxis.set_minor_locator(day_locator)
    ax.yaxis.set_minor_formatter(day_formatter)

    plt.show()


from io import BytesIO
import matplotlib.image as mimg


def plot_graph(g: nx.DiGraph):
    # convert from networkx -> pydot
    g = nx.DiGraph(g)
    # Set defaults for pydot
    g.graph['graph'] = {
        # 'fontname': 'helvetia',
        'rankdir': 'LR'
    }
    g.graph['node'] = {
        'shape': 'box',
        'style': 'filled',
        'fontname': 'fixed',
        'fillcolor': 'white'
    }
    for k in g.nodes.keys():
        attr = g.nodes[k]
        s = attr.get('label', None)
        if s is not None:
            attr['label'] = s.replace("\n", "\l") + "\l"

    pydot_graph = nx.nx_pydot.to_pydot(g)
    # render pydot by calling dot, no file saved to disk
    png_str = pydot_graph.create_png()

    # treat the dot output string as an image file
    sio = BytesIO()
    sio.write(png_str)
    sio.seek(0)
    img = mimg.imread(sio)

    # plot the image
    plt.imshow(img)
    plt.axis("off")
    plt.show(block=False)
