# -*- coding: utf-8 -*-

"""Main module of Train Object Model."""
import itertools
from datetime import datetime, timedelta, date
from pathlib import PosixPath

import pandas as pd
import networkx as nx

import yaml
from pandas import DatetimeIndex
from pandas.tseries.offsets import CustomBusinessDay
from typing import List


class RouteSection:
    """
    Start of a route section
    """
    travel_time: timedelta
    origin_stop_time: timedelta
    origin: str
    destination: str
    departure_times_at_origin: DatetimeIndex

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


class Route:
    sections: List[RouteSection]

    def __init__(self, sections: List[RouteSection]):
        if len(sections) == 0:
            raise ValueError("No sections in route")
        # Check if sections form a route
        for prev, curr in zip(sections, sections[1:]):
            if prev.destination != curr.origin:
                raise ValueError(f"Route sections do not fit: {prev} != {curr}")
        self.sections = sections

    def __str__(self):
        return ','.join([str(s) for s in self.sections])

    def to_dataframe(self) -> pd.DataFrame:
        result = pd.concat([x.to_dataframe() for x in self.sections])
        return result


class Train:
    core_id: str
    sections: List[RouteSection]

    def __init__(self, code_id: str, sections: List[Route]):
        self.core_id = code_id
        self.sections = sections

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

    def extended_train_run_graph(self):
        g = self.train_run_graph()
        nodes: List[SectionRun] = list(g.nodes)
        for v in nodes:
            if g.in_degree(v) == 0:
                g.add_edge(v.section, v)
            if g.out_degree(v) == 0:
                g.add_edge(v, v.section)
        return g


class SectionRun:
    section: RouteSection
    departure_at_origin: datetime

    def __init__(self, section: RouteSection, time: datetime):
        self.section = section
        self.departure_at_origin = time

    def __str__(self):
        ts_origin = self.departure_at_origin.strftime("%F %H:%M")
        ts_dest = self.arrival_at_destination().strftime("%F %H:%M")
        return f"{str(ts_origin)} {self.section} {ts_dest}"

    def arrival_at_destination(self):
        return self.departure_at_origin + self.section.travel_time

    def arrival_at_origin(self):
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
                raise ValueError(f"Section run {prev} must connect to {curr}")


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
        for x in dis[1:]:
            dts = dts.union(x)
    else:
        dts = pd.date_range(begin, end)
    dts = dts + departure_time

    result = RouteSection(origin=section['origin'],
                          destination=section['destination'],
                          travel_time=tt,
                          stop_time=stop_time,
                          departure_timestamps=dts)
    return result


def make_train_from_yml(file: PosixPath) -> Train:
    try:
        td = yaml.safe_load(file.read_text())
    except yaml.YAMLError as e:
        print(f'Error reading train from {file.name}.')
        raise e

    sections = [_make_section_from_dict(d) for d in td['sections']]
    result = Train(td['coreID'], sections=sections)
    return result
