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
    departure: str
    arrival: str
    departure_times: DatetimeIndex

    def __init__(self, departure: str,
                 arrival: str,
                 travel_time: timedelta,
                 departure_timestamps: pd.DatetimeIndex):
        self.departure_times = departure_timestamps
        self.travel_time = travel_time
        self.departure = departure
        self.arrival = arrival

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


class Train:
    core_id: str
    route_sections: List[RouteSection]

    def __init__(self, code_id: str, sections: List[RouteSection]):
        self.core_id = code_id
        self.route_sections = sections


def make_section_from_dict(section: dict) -> RouteSection:
    tt = pd.Timedelta(section['travel_time'])
    spec = section['calendar']
    start = spec['start']
    end = spec['end']
    mask = CustomBusinessDay(weekmask=spec['mask'])
    dts = pd.date_range(start, end, freq=mask)
    result = RouteSection(departure=section['departure'],
                          arrival=section['arrival'],
                          travel_time=tt,
                          departure_timestamps=dts)
    return result


def make_train_from_yml(file: PosixPath) -> Train:
    td = yaml.safe_load(file.read_text())
    sections = [make_section_from_dict(d) for d in td['sections']]
    result = Train(td['coreID'], sections=sections)
    return result
