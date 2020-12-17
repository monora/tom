# -*- coding: utf-8 -*-

"""
This module defines the TOM domain model. The main classes are:

* Train defines a set of planned TrainRuns which consist of a sequence of
* SectionRun. A SectionRun belongs to exactly one
* RouteSection, which has a planned calendar of days the SectionsRuns start. A RouteSection is
  managed by exactly one railway undertaking (RU) and one infrastructure manager (IM).
* Each TrainRun must run exactly once on each location (departure_station, arrival_station) of the train.
"""
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
    departure_station: str
    arrival_station: str
    departure_timestamps: DatetimeIndex
    section_id: int = 0
    version: int = 1

    def __init__(self, departure_station: str,
                 arrival_station: str,
                 travel_time: timedelta,
                 departure_timestamps: pd.DatetimeIndex,
                 stop_time: timedelta = pd.Timedelta(0)):
        """
        Creates a new route section from departure_station to arrival_station at well defined timestamps.

        :param departure_station: location where the train starts or breaks in
        :param arrival_station: location where the train stops or leaves
        :param travel_time: planned time from departure_station to arrival_station
        :param departure_timestamps: timestamps at departure_station (must be same at each day)
        :param stop_time: when station of departure is a train stop the stop_time > 0
        """
        self.departure_timestamps = departure_timestamps
        self.travel_time = travel_time
        self.departure_stop_time = stop_time
        self.departure_station = departure_station
        self.arrival_station = arrival_station

    def __str__(self):
        return self.departure_station + '-' + self.arrival_station

    def __iter__(self):
        """
        Return an iterator over all SectionRuns of this RouteSection
        """
        return (SectionRun(self, dt) for dt in self.departure_timestamps)

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
        :return: pandas dataframe with two columns for [departure_station, arrival_station] and
                one row for each section run.
        """
        df = pd.DataFrame(index=[x.date() for x in self.departure_timestamps])
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
        return ((self.departure_station, self.departure_time()),
                (self.arrival_station, self.arrival_time()))


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

        self._check_sections()

    def __str__(self):
        return self.train_id()

    def train_id(self) -> str:
        """
        **Attention:**

         * in the ECM the *variant* part is only used to identify TrainRuns, not Train.
         * the TimetableYear is only unique, when the start dates of all RouteSections belong to
         the TimetableYear. (This is currently not valid for the test examples used. Why?
        Because it is not nessary, that the  TimetableYear should be part of the TrainID)
        :return: Unique ID of this train (LeadRU/CoreID/TimetableYear)
        """
        return f"TR/{self.lead_ru}/{self.core_id}/{self.timetable_year()}"

    def id(self):
        return f"TR-{self.core_id}-{self.version}"

    def section_run_iterator(self):
        for section in self.sections:
            for sr in section:
                yield sr

    def train_run_graph(self):
        result = nx.DiGraph()

        section_runs = list(self.section_run_iterator())
        for u in section_runs:
            for v in section_runs:
                if u.connects_to(v):
                    result.add_edge(u, v)
        return result

    def location_graph(self):
        trg = self.train_run_graph()
        lg = nx.DiGraph()
        for u, v in trg.edges:
            u: SectionRun
            v: SectionRun
            lg.add_edge(u.departure_station(), u.arrival_station())
            lg.add_edge(v.departure_station(), v.arrival_station())
        return lg

    def extended_train_run_graph(self, use_sections=True):
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
        section_keys = [s.section_key() for s in self.sections]
        if len(self.sections) != len(set(section_keys)):
            raise TomError(
                f"Section keys of train {self.train_id()} not unique: {section_keys}")

    def timetable_year(self) -> int:
        """
        :rtype: year of departuretime of first section
        """
        return self.sections[0].departure_time().year


class SectionRun:
    section: RouteSection
    departure_time: datetime

    def __init__(self, section: RouteSection, time: datetime):
        self.section = section
        self.departure_time = time

    def __str__(self):
        ts_departure_station = self.departure_time.strftime("%F %H:%M")
        ts_arrival_station = self.arrival_time().strftime("%F %H:%M")
        return f"{str(ts_departure_station)} {self.section} {ts_arrival_station}"

    def section_id(self):
        return self.section.section_id

    def arrival_time(self) -> datetime:
        return self.departure_time + self.section.travel_time

    def arrival_at_departure_station(self) -> datetime:
        """:return: the timestamp at which the train arrived in this station. i.e. `departure_time -
        departure_stop_time`
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
    spec: dict = section['calendar']
    begin = spec['begin']
    end = spec['end']
    mask = spec.get('mask', 'D')
    departure_time = pd.Timedelta(section.get('departure_time', 0))
    stop_time = pd.Timedelta(section.get('stop_time', 0))
    if mask != 'D':
        dis = list(map(lambda x: pd.date_range(begin, end, freq=('W-' + x.upper())), mask.split()))
        dts = dis[0]
        for di in dis[1:]:
            dts = dts.union(di)
    else:
        dts = pd.date_range(begin, end)
    dts = dts + departure_time

    result = RouteSection(departure_station=section['departure_station'],
                          arrival_station=section['arrival_station'],
                          travel_time=tt,
                          stop_time=stop_time,
                          departure_timestamps=dts)
    result.section_id = section.get('id', None)
    result.version = section.get('version', result.version)
    return result


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
