# -*- coding: utf-8 -*-

"""
This module defines the TOM domain model. The main classes are:

* A `Train` defines a set of planned TrainRuns which consist of a sequence of
* `SectionRun`. A SectionRun belongs to exactly one
* `RouteSection`, which has a planned calendar of days the SectionsRuns start. A RouteSection is
  managed by exactly one railway undertaking (RU) and one infrastructure manager (IM).
* Each 'TrainRun` must run exactly once on each location (departure_station, arrival_station) of
  the train.

"""
import logging
from datetime import datetime, timedelta, date
from pathlib import PosixPath
from typing import List, Dict

import networkx as nx
import pandas as pd
import yaml
from pandas import DatetimeIndex


class TomError(ValueError):
    """Constraint violation in the TOM Model are signalled using this error"""
    pass


class RouteSection:
    """
    Section of a route of a train which belongs to exactly one responsible IM
    and applicant RU.

    The departure_times define the calendar of the SectionRuns
    of this RouteSection. The date part of these timestamps are the calender days of the train
    is running is this section.
    """
    travel_time: timedelta
    departure_stop_time: timedelta
    departure_daytime: timedelta
    departure_station: str
    arrival_station: str
    departure_timestamps: DatetimeIndex = DatetimeIndex([])
    calendar: DatetimeIndex = None
    section_id: str = '0'
    version: int = 1
    is_section_complete: bool = False
    is_construction_start: bool = False
    successors: List[str] = []

    def __init__(self, departure_station: str,
                 arrival_station: str,
                 travel_time: timedelta,
                 calendar: pd.DatetimeIndex,
                 departure_daytime: pd.Timedelta = None,
                 stop_time: timedelta = pd.Timedelta(0)):
        """
        Creates a new route section from departure_station to arrival_station at well defined
        timestamps.

        :param calendar: set of calendar days the train starts at departure_station
        :param departure_station: location where the train starts or breaks in
        :param arrival_station: location where the train stops or leaves
        :param travel_time: planned time from departure_station to arrival_station
        :param departure_daytime: timetable daytime at departure_station
        :param stop_time: when station of departure is a train stop the stop_time > 0
        """
        self.travel_time = travel_time
        self.departure_stop_time = stop_time
        self.departure_station = departure_station
        self.arrival_station = arrival_station
        self.calendar = calendar

        if departure_daytime is not None:
            self.departure_daytime = pd.Timedelta(departure_daytime)
            if calendar is None:
                raise TomError(f"Calendar must not be None for construction start section: {self}")
            self.departure_timestamps = calendar + self.departure_daytime
            self.is_section_complete = True
            self.is_construction_start = True

    def __str__(self):
        return self.departure_station + '-' + self.arrival_station

    def __iter__(self):
        """
        Return an iterator over all SectionRuns of this RouteSection
        """
        return (SectionRun(self, dt) for dt in self.departure_timestamps)

    def is_complete(self):
        return self.is_section_complete

    def version_info(self):
        return f"{self.section_id}v{self.version}"

    def route_id(self):
        route_id = str(self.section_id).split('.')[:-1]
        if len(route_id) > 0:
            return '.'.join(route_id)
        else:
            return self.section_id

    def description(self) -> str:
        dep = self.departure_time().strftime("%H:%M")
        arr = self.arrival_time().strftime("%H:%M")
        fd = self.first_day().strftime("%d/%m")
        ld = self.last_day().strftime("%d/%m")
        result = f"ID        : {self.version_info()}\n"
        result += f"Calender  : {fd} to {ld}\n"
        result += f"Start   at: {dep} in {self.departure_station}\n"
        result += f"Arrival at: {arr} in {self.arrival_station}\n"
        result += f"Successors: {self.successors}"
        return result

    def first_day(self) -> date:
        """
        :return: Calendar day of the first train run in this section.
        """
        return datetime.date(self.departure_timestamps[0])

    def last_day(self) -> date:
        """
        :return: Calendar day of the last train run in this section.
        """
        return datetime.date(self.departure_timestamps[-1])

    def validity(self):
        return self.first_day(), self.last_day()

    def departure_time(self) -> pd.Timestamp:
        """
        :return: Timestamp the first train run departs from section departure_station
        """
        return self.departure_timestamps[0]

    def arrival_time(self) -> pd.Timestamp:
        """
        :return: Timestamp the first train run arrives at section station of arrival
        """
        return self.departure_time() + self.travel_time

    def to_dataframe(self) -> pd.DataFrame:
        """
        :return: pandas dataframe with three columns for
         [section_id, departure_station, arrival_station] and one row for each section run.
        """
        df = pd.DataFrame(index=[x.date() for x in self.departure_timestamps])
        df['ID'] = str(self.section_id)
        df[self.departure_station] = self.departure_timestamps
        df[self.arrival_station] = self.arrival_times()
        return df

    def arrival_times(self) -> pd.DatetimeIndex:
        """
        The arrival times are computed from section departure times + travel time.
        """
        return self.departure_timestamps + self.travel_time

    def section_key(self):
        """
        A section of a train is uniquely identified by this quadruple:

          ((departure_station, departure time), (arrival_station, arrival time))

        :return: unique key among all sections of a train
        """
        return ((self.departure_station, str(self.departure_time())),
                (self.arrival_station, str(self.arrival_time())))

    def complete_from_predecessor(self, pred):
        """

        :type pred: RouteSection
        """
        if self.is_section_complete:
            return

        dts = pred.departure_timestamps + pred.travel_time + self.departure_stop_time
        self._adjust_departure_times(dts)

    def complete_from_successor(self, succ):
        if self.is_section_complete:
            return

        dts = succ.departure_timestamps - self.travel_time - succ.departure_stop_time
        self._adjust_departure_times(dts)

    def _adjust_departure_times(self, dts: DatetimeIndex):
        """
        Only called if departure_time was not set explicitly: Compute it from neighbor
        :param dts: departure_times computed from travel time to neighbor
        """
        if self.is_section_complete:
            return

        computed_calendar = pd.DatetimeIndex([x.date() for x in dts])
        if self.calendar is None:
            self.calendar = my_date_set = computed_calendar
        else:
            my_date_set = self.calendar
        intersection = computed_calendar.intersection(my_date_set)
        if len(intersection) == 0:
            # No connected section runs possible
            return
        self.departure_daytime = self._compute_daytime(dts[0])
        dts = intersection + self.departure_daytime
        self.departure_timestamps = self.departure_timestamps.union(dts)
        if len(self.calendar) == len(self.departure_timestamps):
            self.is_section_complete = True

    @staticmethod
    def _compute_daytime(ts: pd.Timestamp):
        t = ts.time()
        return pd.Timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)

    def can_connect_to(self, other) -> bool:
        return self.arrival_station == other.departure_station


SINGLE_SOURCE = 'single-source'
SINGLE_TARGET = 'single-target'


class Train:
    core_id: str
    version: int
    sections: List[RouteSection] = []
    lead_ru: int = 8350

    def __init__(self, core_id: str, sections: List[RouteSection]):
        self.version = 1
        self.core_id = core_id
        self.sections = sections

        self._repair_incomplete_sections()
        self._check_invariant()

    def __str__(self):
        return self.train_id()

    def train_id(self) -> str:
        """
        **Attention:**

        in the ECM the *variant* part is only used to identify TrainRuns, not the train.
        the TimetableYear is only unique, when the start dates of all RouteSections belong to
        the TimetableYear.
        (This is currently not valid for the test examples used. Why? Because it is not
        necessary, that the  TimetableYear should be part of the TrainID)

        :return: Unique ID of this train (LeadRU/CoreID/TimetableYear)
        """
        return f"TR/{self.lead_ru}/{self.core_id}/{self.timetable_year()}"

    def id(self):
        return f"TR-{self.core_id}-{self.version}"

    def section_run_iterator(self):
        for section in self.sections:
            for sr in section:
                yield sr

    def train_run_graph(self) -> nx.DiGraph:
        result = nx.DiGraph()

        section_runs = list(self.section_run_iterator())
        for u in section_runs:
            for v in section_runs:
                if u.connects_to(v):
                    result.add_edge(u, v)
        return result

    def location_graph(self) -> nx.DiGraph:
        trg = self.train_run_graph()
        lg = nx.DiGraph()
        for u, v in trg.edges:
            u: SectionRun
            v: SectionRun
            lg.add_edge(u.departure_station(), u.arrival_station())
            lg.add_edge(v.departure_station(), v.arrival_station())
        return lg

    def section_graph(self) -> nx.DiGraph:
        trg = self.train_run_graph()
        sg = nx.DiGraph()
        for v in trg.nodes:
            vi = v.section.version_info()
            sg.add_node(vi)
            sg.nodes[vi]['id'] = vi
            sg.nodes[vi]['label'] = v.section.description()
            sg.nodes[vi]['route_id'] = v.section.route_id()
        for u, v in trg.edges:
            u: SectionRun
            v: SectionRun
            vi = v.section.version_info()
            ui = u.section.version_info()
            sg.add_edge(ui, vi)
        return sg

    def basic_section_graph(self) -> nx.DiGraph:
        sg = nx.DiGraph()
        id2section = dict()
        for u in self.sections:
            id2section[u.section_id] = u
            sg.add_node(u)
        for u in self.sections:
            for v_id in u.successors:
                v = id2section.get(v_id, None)
                if v is None:
                    logging.warning(f"Invalid successor for section {u} ignored")
                else:
                    if not u.can_connect_to(v):
                        logging.warning(f"Section {u} can not connect to successor {v}. "
                                        "Edge is ignored")
                    sg.add_edge(u, v)
        return sg

    def _repair_incomplete_sections(self):
        construction_begins = list(filter(RouteSection.is_complete, self.sections))
        sg = self.basic_section_graph()
        for cb in construction_begins:
            for pred, successors in nx.bfs_successors(sg, cb):
                succ: RouteSection
                for succ in successors:
                    succ.complete_from_predecessor(pred)
        sg = sg.reverse()
        for cb in construction_begins:
            for pred, successors in nx.bfs_successors(sg, cb):
                succ: RouteSection
                for succ in successors:
                    succ.complete_from_successor(pred)

    def extended_train_run_graph(self, use_sections=True) -> nx.DiGraph:

        g = self.train_run_graph()
        nodes: List[SectionRun] = list(g.nodes)
        for v in nodes:
            if g.in_degree(v) == 0:
                in_node = v.section if use_sections else SINGLE_SOURCE
                g.add_edge(in_node, v)
            if g.out_degree(v) == 0:
                out_node = v.section if use_sections else 'single-target'
                g.add_edge(v, out_node)
        return g

    def train_run_iterator(self):
        """

        :return: Iterator[TrainRun]
        """
        g = self.extended_train_run_graph(use_sections=False)
        if len(g.edges) == 0:
            for sr in self.section_run_iterator():
                yield TrainRun(self, [sr])
            return

        for path in nx.all_simple_paths(g, source=SINGLE_SOURCE, target=SINGLE_TARGET):
            yield TrainRun(self, path[1:-1])

    def to_dataframe(self) -> pd.DataFrame:
        train_runs = sorted(self.train_run_iterator(), key=TrainRun.start_date)
        train_ids = list(map(TrainRun.train_id, train_runs))
        result = pd.DataFrame(index=train_ids, columns=self._locations())
        for tr in train_runs:
            result.loc[tr.train_id()] = tr.time_table()
        return result

    def section_dataframes(self) -> List[pd.DataFrame]:
        return [sec.to_dataframe() for sec in self.sections]

    def _locations(self) -> List[str]:
        return list(nx.topological_sort(self.location_graph()))

    def _check_sections(self):
        # Check if section id are unique:
        section_ids = [s.section_id for s in self.sections]
        if len(section_ids) == 0:
            raise TomError(f"Train {self.train_id()} must contain at least one RouteSection")

        if len(self.sections) != len(set(section_ids)):
            raise TomError(f"Section IDs of train {self.train_id()} not unique: {section_ids}")

        # Check if section event coordinates are unique:
        key2section = dict()
        for s in self.sections:
            k = s.section_key()
            v = key2section.get(k, [])
            v.append(s)
            key2section[k] = v
        if len(self.sections) != len(key2section):
            raise TomError(
                f"Section keys of train {self.train_id()} not unique: {key2section}")

    def timetable_year(self) -> int:
        """
        :rtype: year of departure_time of first section
        """
        return self.sections[0].departure_time().year

    def _check_invariant(self):
        self._check_sections()
        self._check_train_run_graph()

    def _check_train_run_graph(self):
        trg = self.train_run_graph()
        for v in trg.nodes:
            out_degree = trg.out_degree(v)
            in_degree = trg.in_degree(v)
            if out_degree > 1 or in_degree > 1:
                logging.error("Section run %s departs %d times and arrives %d times", v, out_degree,
                              in_degree)
                if out_degree > 1:
                    out_neighbors = list(map(str, trg.successors(v)))
                    logging.error("Departures: %s", out_neighbors)
                if in_degree > 1:
                    in_neighbors = list(map(str, trg.predecessors(v)))
                    logging.error("Arrivals: %s", in_neighbors)
                raise TomError(f"Invalid section run design for: {v}")


class SectionRun:
    section: RouteSection
    departure_time: datetime

    def __init__(self, section: RouteSection, time: datetime):
        self.section = section
        self.departure_time = time

    def __str__(self):
        dep = self.departure_time.strftime("%F %H:%M")
        arr = self.arrival_time().strftime("%F %H:%M")
        return f"{self.section.version_info()}:{dep} {self.section} {arr}"

    def section_id(self):
        return self.section.section_id

    def arrival_time(self) -> datetime:
        return self.departure_time + self.section.travel_time

    def arrival_at_departure_station(self) -> datetime:
        """:return: the timestamp when the train will arrive in the departure station

        result = departure_time - departure_stop_time
        """
        return self.departure_time - self.section.departure_stop_time

    def departure_station(self) -> str:
        return self.section.departure_station

    def arrival_station(self) -> str:
        return self.section.arrival_station

    def connects_to(self, other):
        """
        Checks if to two section `self` and `other` fit together`. This is only if

        (self.arrival_station(), self.arrival_time())
           = [other.departure_station(), other.arrival_at_departure_station())

        :param other: SectionRun
        :return: True if both section fit together.
        """
        # print(self, '->', other)
        if self.arrival_station() == other.departure_station():
            return self.arrival_time() == other.arrival_at_departure_station()
        else:
            return False


class TrainRun:
    train: Train
    sections_runs: List[SectionRun]

    def __init__(self, t: Train, section_runs: List[SectionRun]):

        self.train = t
        self.sections_runs = section_runs

        for prev, curr in zip(self.sections_runs, self.sections_runs[1:]):
            if not prev.connects_to(curr):
                raise TomError(f"Section run {prev} must connect to {curr}")

    def __str__(self):
        return self.train_id()

    def train_id(self):
        return f"{self.train.train_id()}/{self.train_run_id()}"

    def train_run_id(self):
        return f"{self.first_run().section_id()}/{self.start_date()}"

    def start_date(self):
        return self.first_run().departure_time.strftime("%F")

    def first_run(self):
        return self.sections_runs[0]

    def time_table(self) -> Dict[str, datetime]:
        fr = self.first_run()
        result = {fr.departure_station(): fr.departure_time}
        for sr in self.sections_runs:
            result[sr.arrival_station()] = sr.arrival_time()
        return result

    def location_iterator(self):
        yield self.first_run().departure_station()
        for sr in self.sections_runs:
            yield sr.arrival_station()


class Route:
    """
    A Route is a sequence of RouteSection where consecutive section must fit together:

    If (prev, next) is a tuple in the sections, then

       prev.arrival_station == next.departure_station

    NOTE: The here proposed TOM model does not need routes! They are instead modeled as TrainRuns
    which are computed from RouteSection (see Train.train_run_iterator)

    """
    sections: List[RouteSection]

    def __init__(self, sections: List[RouteSection]):
        if len(sections) == 0:
            raise TomError("No sections in route")
        # Check if sections form a route
        for prev, curr in zip(sections, sections[1:]):
            if prev.arrival_station != curr.departure_station:
                raise TomError(f"Route sections do not fit: {prev} != {curr}")
        self.sections = sections

    def __str__(self):
        return ','.join([str(s) for s in self.sections])


def _make_section_from_dict(section: dict) -> RouteSection:
    try:
        tt = pd.Timedelta(section['travel_time'])
    except TypeError as e:
        raise e
    stop_time = pd.Timedelta(section.get('stop_time', 0))
    cal = _make_calendar(section.get('calendar', None))
    departure_daytime = section.get('departure_time', None)
    result = RouteSection(departure_station=section['departure_station'],
                          arrival_station=section['arrival_station'],
                          travel_time=tt,
                          stop_time=stop_time,
                          calendar=cal,
                          departure_daytime=departure_daytime
                          )

    result.section_id = section.get('id', None)
    result.version = section.get('version', result.version)
    result.successors = section.get('succ', [])
    return result


def _make_calendar(spec: dict):
    if not spec:
        return None

    begin = spec['begin']
    end = spec['end']
    mask = spec.get('mask', 'D')
    if mask != 'D':
        dis = list(map(lambda x: pd.date_range(begin, end, freq=('W-' + x.upper())), mask.split()))
        cal = dis[0]
        for di in dis[1:]:
            cal = cal.union(di)
    else:
        cal = pd.date_range(begin, end)
    return cal


def make_train_from_yml(file: PosixPath) -> Train:
    try:
        td = yaml.safe_load(file.read_text())
    except yaml.YAMLError as e:
        print(f'Error reading train from {file.name}.')
        raise e

    sections = [_make_section_from_dict(d) for d in td['sections']]
    # Give each sections a unique section id:
    for i in range(0, len(sections)):
        s = sections[i]
        if s.section_id is None:
            s.section_id = i

    result = Train(td['coreID'], sections=sections)
    result.version = td.get('version', 1)
    return result
