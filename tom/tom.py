# -*- coding: utf-8 -*-

"""Main module of Train Object Model."""
from datetime import datetime, timedelta, date
from pathlib import PosixPath

import pandas as pd
import yaml
from pandas import DatetimeIndex
from pandas.tseries.offsets import CustomBusinessDay
from typing import List


class RouteSection:
    """
    Start of a route section
    """
    travel_time: timedelta
    stop_time: timedelta
    departure: str
    arrival: str
    departure_times: DatetimeIndex

    def __init__(self, departure: str,
                 arrival: str,
                 travel_time: timedelta,
                 departure_timestamps: pd.DatetimeIndex,
                 stop_time: timedelta = 0):
        self.departure_times = departure_timestamps
        self.travel_time = travel_time
        self.stop_time = stop_time
        self.departure = departure
        self.arrival = arrival

    def __str__(self):
        return self.departure + '->' + self.arrival

    def first_day(self) -> date:
        return datetime.date(self.departure_times[0])

    def last_day(self) -> date:
        return datetime.date(self.departure_times[-1])

    def departure_time(self) -> pd.Timestamp:
        return self.departure_times[0]

    def arrival_time(self) -> pd.Timestamp:
        return self.departure_time() + self.travel_time

    def to_dataframe(self) -> pd.DataFrame:
        df = pd.DataFrame(index=[x.date() for x in self.departure_times])
        df[self.departure] = self.departure_times
        df[self.arrival] = self.arrival_times()
        return df

    def arrival_times(self) -> pd.DatetimeIndex:
        return self.departure_times + self.travel_time


class Route:
    sections: List[RouteSection]

    def __init__(self, sections: List[RouteSection]):
        if len(sections) == 0:
            raise ValueError("No sections in route")
        # Check if sections form a route
        for prev, curr in zip(sections, sections[1:]):
            if prev.arrival != curr.departure:
                raise ValueError(f"Route sections do not fit: {prev} != {curr}")
        self.sections = sections

    def __str__(self):
        return ','.join([str(s) for s in self.sections])

    def to_dataframe(self) -> pd.DataFrame:
        result = pd.concat([x.to_dataframe() for x in self.sections])
        return result


class Train:
    core_id: str
    routes: List[Route]

    def __init__(self, code_id: str, routes: List[Route]):
        self.core_id = code_id
        self.routes = routes


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
        mask = CustomBusinessDay(weekmask=mask)
    dts = pd.date_range(begin, end, freq=mask) + departure_time

    result = RouteSection(departure=section['departure'],
                          arrival=section['arrival'],
                          travel_time=tt,
                          stop_time=stop_time,
                          departure_timestamps=dts)
    return result


def _make_route_from_dict(route: dict):
    sections = [_make_section_from_dict(d) for d in route['route']]
    result = Route(sections=sections)
    return result


def make_train_from_yml(file: PosixPath) -> Train:
    try:
        td = yaml.safe_load(file.read_text())
    except yaml.YAMLError as e:
        print(f'Error reading train from {file.name}.')
        raise e

    routes = [_make_route_from_dict(d) for d in td['routes']]
    result = Train(td['coreID'], routes=routes)
    return result
