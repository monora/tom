# -*- coding: utf-8 -*-

"""Main module of Train Object Model."""
from datetime import datetime, timedelta, date
from pathlib import PosixPath
from typing import List, Dict

import networkx as nx
import pandas as pd
import yaml
from pandas import DatetimeIndex


class TomError(ValueError):
    pass


class RouteSection:
    """
    Start of a route section
    """
    travel_time: timedelta
    origin_stop_time: timedelta
    origin: str
    destination: str
    departure_times_at_origin: DatetimeIndex
    section_id: int = 0
    version: int = 1

    def __init__(self, origin: str,
                 destination: str,
                 travel_time: timedelta,
                 departure_timestamps: pd.DatetimeIndex,
                 stop_time: timedelta = pd.Timedelta(0)):
        self.departure_times_at_origin = departure_timestamps
        self.travel_time = travel_time
        self.origin_stop_time = stop_time
        self.origin = origin
        self.destination = destination

    def __str__(self):
        return self.origin + '-' + self.destination

    def __iter__(self):
        return (SectionRun(self, dt) for dt in self.departure_times_at_origin)

    def first_day(self) -> date:
        return datetime.date(self.departure_times_at_origin[0])

    def last_day(self) -> date:
        return datetime.date(self.departure_times_at_origin[-1])

    def departure_at_origin(self) -> pd.Timestamp:
        return self.departure_times_at_origin[0]

    def arrival_at_destination(self) -> pd.Timestamp:
        return self.departure_at_origin() + self.travel_time

    def to_dataframe(self) -> pd.DataFrame:
        df = pd.DataFrame(index=[x.date() for x in self.departure_times_at_origin])
        df[self.origin] = self.departure_times_at_origin
        df[self.destination] = self.arrival_times_at_destination()
        return df

    def arrival_times_at_destination(self) -> pd.DatetimeIndex:
        return self.departure_times_at_origin + self.travel_time

    def section_key(self):
        return ((self.origin, self.departure_at_origin()),
                (self.destination, self.arrival_at_destination()))


class Route:
    sections: List[RouteSection]

    def __init__(self, sections: List[RouteSection]):
        if len(sections) == 0:
            raise TomError("No sections in route")
        # Check if sections form a route
        for prev, curr in zip(sections, sections[1:]):
            if prev.destination != curr.origin:
                raise TomError(f"Route sections do not fit: {prev} != {curr}")
        self.sections = sections

    def __str__(self):
        return ','.join([str(s) for s in self.sections])


SINGLE_SOURCE = 'single-source'
SINGLE_TARGET = 'single-target'


class Train:
    core_id: str
    version: int
    sections: List[RouteSection]
    lead_ru: int = 8350

    def __init__(self, code_id: str, sections: List[RouteSection]):
        self.version = 1
        self.core_id = code_id
        self.sections = sections

        self._check_sections()

    def train_id(self) -> str:
        return f"TR/{self.lead_ru}/{self.core_id}/00"

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
            lg.add_edge(u.origin(), u.destination())
            lg.add_edge(v.origin(), v.destination())
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

    def _locations(self) -> List[str]:
        return list(nx.topological_sort(self.location_graph()))

    def _check_sections(self):
        # Check if section id are unique:
        section_ids = [s.section_id for s in self.sections]
        if len(self.sections) != len(set(section_ids)):
            raise TomError(f"Section IDs of train {self.train_id()} not unique: {section_ids}")

        # Check if section event coordinates are unique:
        section_keys = [s.section_key() for s in self.sections]
        if len(self.sections) != len(set(section_keys)):
            raise TomError(
                f"Section keys of train {self.train_id()} not unique: {section_keys}")


class SectionRun:
    section: RouteSection
    departure_at_origin: datetime

    def __init__(self, section: RouteSection, time: datetime):
        self.section = section
        self.departure_at_origin = time

    def __str__(self):
        ts_origin = self.departure_at_origin.strftime("%F %H:%M")
        ts_destination = self.arrival_at_destination().strftime("%F %H:%M")
        return f"{str(ts_origin)} {self.section} {ts_destination}"

    def section_id(self):
        return self.section.section_id

    def arrival_at_destination(self) -> datetime:
        return self.departure_at_origin + self.section.travel_time

    def arrival_at_origin(self) -> datetime:
        return self.departure_at_origin - self.section.origin_stop_time

    def origin(self) -> str:
        return self.section.origin

    def destination(self) -> str:
        return self.section.destination

    def connects_to(self, other):
        # print(self, '->', other)
        if self.destination() == other.origin():
            return self.arrival_at_destination() == other.arrival_at_origin()
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
        return self.first_run().departure_at_origin.strftime("%F")

    def first_run(self):
        return self.sections_runs[0]

    def time_table(self) -> Dict[str, datetime]:
        fr = self.first_run()
        result = {fr.origin(): fr.departure_at_origin}
        for sr in self.sections_runs:
            result[sr.destination()] = sr.arrival_at_destination()
        return result

    def location_iterator(self):
        yield self.first_run().origin()
        for sr in self.sections_runs:
            yield sr.destination()


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

    result = RouteSection(origin=section['origin'],
                          destination=section['destination'],
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
