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
import xml.etree.ElementTree as ElemTree
from datetime import datetime, timedelta, date
from pathlib import PosixPath
from typing import List, Dict, Tuple, ValuesView

import networkx as nx
import pandas as pd
import yaml
from pandas import DatetimeIndex


class TomError(ValueError):
    """Constraint violation in the TOM Model are signalled using this error"""
    pass


TSI_SCHEMA_VERSION = '2.3.0'
"""
New Schema version proposed for change of element TrainInformation
"""
TSI_LOCATION_TYPE_CODES = {
    'Origin': '01',
    'Handover': '04',
    'Destination': '03',
}


class LocationIdGenerator:
    location_name_to_code = {}
    location_last = 9999

    def map_location_name_to_code(self, name: str) -> str:
        result = self.location_name_to_code.get(name, None)
        if result is None:
            self.location_last += 1
            result = self.location_last
            self.location_name_to_code[name] = result
        return str(result)


__ID_GENERATOR = LocationIdGenerator()


def compute_bitmap_days(calendar: pd.DatetimeIndex) -> str:
    """
    :param calendar:
    :return: Bitmap string containing 1 and 0
    """
    first = calendar[0]
    last = calendar[-1]
    result = ""
    for day in pd.date_range(first, last):
        result += '1' if day in calendar else '0'
    return result


def xml_simple_element(parent: ElemTree.Element, name: str, text: str = None):
    result = ElemTree.SubElement(parent, name)
    if text:
        result.text = str(text)
    return result


def xml_add_calendar(tom_object, parent: ElemTree.Element):
    cal = xml_simple_element(parent, 'PlannedCalendar')
    xml_simple_element(cal, 'BitmapDays',
                       text=compute_bitmap_days(tom_object.calendar))

    period = xml_simple_element(cal, 'ValidityPeriod')
    iso_format = "%Y-%m-%dT00:00:00"
    xml_simple_element(period, 'StartDateTime',
                       tom_object.first_day().strftime(iso_format))
    xml_simple_element(period, 'EndDateTime',
                       tom_object.last_day().strftime(iso_format))


def xml_add_journey_location(parent: ElemTree.Element,
                             station: str,
                             t: datetime,
                             offset: int = 0,
                             type_code=None):
    """
    Add XML Element PlannedJourneyLocation

    :param parent: RouteSection
    :param station: name of destination or arrival
    :param t: timestamp
    :param offset: in days to departure
    :param type_code: JourneyLocationTypeCode (default ist Handover == 04)
    """
    loc = xml_simple_element(parent, 'PlannedJourneyLocation')
    if type_code:
        # Set this only if really needed, because it can be computed from the successor relation
        loc.set('JourneyLocationTypeCode', type_code)
    xml_simple_element(loc, 'CountryCodeISO', 'DE')  # FIXME
    xml_simple_element(loc, 'LocationPrimaryCode',
                       __ID_GENERATOR.map_location_name_to_code(station))
    xml_simple_element(loc, 'PrimaryLocationName', station)

    time = xml_simple_element(loc, 'TimingAtLocation')
    time = xml_simple_element(time, 'Timing')
    xml_simple_element(time, 'Time', t.strftime("%H:%M:%S"))
    xml_simple_element(time, 'Offset', str(offset))


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
    departure_daytime: timedelta = None
    departure_station: str
    arrival_station: str
    departure_timestamps: DatetimeIndex = DatetimeIndex([])
    calendar: DatetimeIndex = None
    section_id: str = '00'
    version: int = 1
    is_section_complete: bool = False
    is_construction_start: bool = False
    successors: List[str] = []
    color: str = None
    train = None

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
        return f"{self.section_id}.v{self.version}"

    def route_id(self):
        route_id = str(self.section_id).split('.')[:-1]
        if len(route_id) > 0:
            return '.'.join(route_id)
        else:
            return self.section_id

    def description(self, with_bitmap=True) -> str:
        dep = self.departure_time().strftime("%H:%M")
        arr = self.arrival_time().strftime("%H:%M")
        fd = self.first_day().strftime("%d/%m")
        ld = self.last_day().strftime("%d/%m")
        bitmap = ' ' + compute_bitmap_days(self.calendar) if with_bitmap else ''
        result = f"ID        : {self.version_info()}\n"
        result += f"Calender  : {fd} to {ld}{bitmap}\n"
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

    @staticmethod
    def __compute_calendar(dts: pd.DatetimeIndex) -> pd.DatetimeIndex:
        """
        :return: the set of days of my departure times
        """
        return pd.DatetimeIndex([x.date() for x in dts])

    def to_dataframe(self) -> pd.DataFrame:
        """
        :return: pandas dataframe with three columns for
         [section_id, departure_station, arrival_station] and one row for each section run.
        """
        df = pd.DataFrame(index=self.__compute_calendar(self.departure_timestamps))
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

        self.__complete_color_from(pred)
        dts = self.departure_times_from_predecessor(pred)
        self.__adjust_departure_times(dts)

    def departure_times_from_predecessor(self, pred) -> pd.DatetimeIndex:
        return pred.departure_timestamps + pred.travel_time + self.departure_stop_time

    def departures_times_from_successor(self, succ):
        return succ.departure_timestamps - self.travel_time - succ.departure_stop_time

    def complete_from_successor(self, succ):
        if self.is_section_complete:
            return

        self.__complete_color_from(succ)
        dts = self.departures_times_from_successor(succ)
        self.__adjust_departure_times(dts)

    def complete_calender_from_predecessor(self, pred):
        if self.is_section_complete:
            return
        dts = self.departure_times_from_predecessor(pred)
        self.__complete_calendar_dts(dts)

    def complete_calender_from_successor(self, succ):
        if self.is_section_complete:
            return
        dts = self.departures_times_from_successor(succ)
        self.__complete_calendar_dts(dts)

    def __complete_calendar_dts(self, dts):
        computed_calendar = self.__compute_calendar(dts)
        self.__complete_calendar(computed_calendar, dts)

    def __adjust_departure_times(self, dts: DatetimeIndex):
        """
        Only called if calendar or departure_time was not set explicitly: Compute it from neighbor
        :param dts: departure_times computed from travel time to neighbor
        """
        computed_calendar = self.__compute_calendar(dts)
        if self.calendar is None:
            self.calendar = computed_calendar
            self.departure_timestamps = dts
            self.departure_daytime = self.__compute_daytime(dts)
            self.is_section_complete = True
        else:
            self.__complete_calendar(computed_calendar, dts)

    def __complete_calendar(self, computed_calendar, dts):
        intersection = computed_calendar.intersection(self.calendar)
        if len(intersection) == 0:
            return
        dt = self.__compute_daytime(dts)
        if self.departure_daytime is not None:
            if dt != self.departure_daytime:
                raise TomError(f"Inconsistent departure times for section {self}:"
                               f" {dt}!={self.departure_daytime}")

        self.departure_daytime = dt
        dts = intersection + self.departure_daytime
        self.departure_timestamps = self.departure_timestamps.union(dts)
        if len(self.calendar) == len(self.departure_timestamps):
            self.is_section_complete = True

    @staticmethod
    def __compute_daytime(ts: pd.DatetimeIndex):
        t = ts[0].time()
        return pd.Timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)

    def can_connect_to(self, other) -> bool:
        return self.arrival_station == other.departure_station

    def check_invariant(self):
        if len(self.departure_timestamps) == 0:
            raise TomError(f"Empty section not allowed: {self}")

    def adjust_calendar_to_timestamps(self):
        logging.warning("Shorten section calendar of %s %s to real section runs. "
                        "Old: %d "
                        "New: %d.",
                        self, self.version_info(),
                        len(self.calendar), len(self.departure_timestamps))
        self.calendar = self.__compute_calendar(self.departure_timestamps)

    def __complete_color_from(self, other):
        if self.color is None:
            self.color = other.color

    def xml_add_id(self, parent: ElemTree.Element):
        sec_id = xml_simple_element(parent, 'SectionID')
        xml_simple_element(sec_id, 'ObjectType', 'RS')
        xml_simple_element(sec_id, 'Company', self.train.lead_ru)
        ci = "{:>12}".format(self.train.core_id).replace(' ', '-')
        xml_simple_element(sec_id, 'Core', ci)
        xml_simple_element(sec_id, 'Variant', self.section_id)
        xml_simple_element(sec_id, 'TimetableYear', self.train.timetable_year())

    def to_xml(self, root: ElemTree.Element):
        rs = ElemTree.SubElement(root, 'RouteSection', {'SectionVersion': str(self.version)})
        if self.is_construction_start:
            rs.set('HasReferenceCalender', 'true')
        self.xml_add_id(rs)
        xml_add_journey_location(rs,
                                 self.departure_station,
                                 self.departure_time())
        xml_add_journey_location(rs,
                                 self.arrival_station,
                                 self.arrival_time(),
                                 offset=self.arrival_time_offset())
        xml_add_calendar(self, rs)
        if len(self.successors) > 0:
            successors = xml_simple_element(rs, 'Successors')
            for sec_id in self.successors:
                section: RouteSection
                section = self.train.id_to_sec[sec_id]
                section.xml_add_id(successors)

    def arrival_time_offset(self) -> int:
        """
        :return: Offset in days of arrival relativ to departure time (must be positiv)
        """
        return day_offset(self.arrival_time(), self.departure_time())


class SingleSource:
    """Used as sentinel object in `Train.extended_train_run_graph`.

    .. seealso:: https://www.revsys.com/tidbits/sentinel-values-python/
    """

    def __repr__(self):
        return 'single-source'


class SingleTarget:
    def __repr__(self):
        return 'single-target'


class Train:
    core_id: str
    version: int
    sections: List[RouteSection] = []
    id_to_sec: Dict[str, RouteSection] = {}
    lead_ru: int = 8350

    def __init__(self, core_id: str, sections: List[RouteSection]):
        self.version = 1
        self.core_id = core_id
        self.sections = sections

        sg: nx.DiGraph = self.__repair_incomplete_sections()
        # After repair all sections must have a departure time
        for section in self.sections:
            self.id_to_sec[section.section_id] = section
            section.train = self
            if section.departure_daytime is None:
                raise TomError(f"Could not compute departure time for section "
                               f"{section}: {section.version_info()}.")
        self.__complete_section_calenders(sg)

        self.__check_invariant()

    def __complete_section_calenders(self, sg):
        for u, v in sg.edges:
            u: RouteSection
            v: RouteSection
            v.complete_calender_from_predecessor(u)
            u.complete_calender_from_successor(v)
        # Check if calendars are complete
        for rs in self.sections:
            if not rs.is_complete():
                rs.adjust_calendar_to_timestamps()

    def __str__(self):
        return self.train_id()

    def train_id(self, variant='00') -> str:
        """
        **Attention:**

        in the ECM the *variant* part is only used to identify TrainRuns, not the train.
        the TimetableYear is only unique, when the start dates of all RouteSections belong to
        the TimetableYear.
        (This is currently not valid for the test examples used. Why? Because it is not
        necessary, that the  TimetableYear should be part of the TrainID)

        :return: Unique ID of this train (LeadRU/CoreID/TimetableYear)
        """
        return f"TR/{self.lead_ru}/{self.core_id}/{variant}/{self.timetable_year()}"

    def id(self):
        return f"TR-{self.core_id}-{self.version}"

    def section_run_iterator(self):
        for section in self.sections:
            for sr in section:
                yield sr

    def train_run_graph(self) -> nx.DiGraph:
        result = nx.DiGraph()
        section_runs = list(self.section_run_iterator())
        for v in section_runs:
            result.add_node(v)
            # vi = v.section.version_info()
            result.nodes[v]['fillcolor'] = v.section.color or 'white'
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
            sg.nodes[vi]['label'] = v.section.description(with_bitmap=False)
            sg.nodes[vi]['route_id'] = v.section.route_id()
            sg.nodes[vi]['fillcolor'] = v.section.color or 'white'
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

    def __repair_incomplete_sections(self) -> nx.DiGraph:
        """
        Try to repair incomplete sections. A section can be under specified either:

        * departure time is not specified or
        * calender is not set

        In this method at least the departure time is calculated from the construction
        begins using a BFS search in the section graph from these.

        :return: basic section graph (see Train.basis_section_graph)
        """
        construction_begins = list(filter(RouteSection.is_complete, self.sections))
        sg = self.basic_section_graph()
        for cb in construction_begins:
            for pred, successors in nx.bfs_successors(sg, cb):
                succ: RouteSection
                for succ in successors:
                    succ.complete_from_predecessor(pred)
        sg_reversed = sg.reverse()
        for cb in construction_begins:
            for pred, successors in nx.bfs_successors(sg_reversed, cb):
                succ: RouteSection
                for succ in successors:
                    succ.complete_from_successor(pred)
        return sg

    def extended_train_run_graph(self, use_sections=True) -> nx.DiGraph:
        g = self.train_run_graph()
        nodes: List[SectionRun] = list(g.nodes)
        for v in nodes:
            if g.in_degree(v) == 0:
                in_node = v.section if use_sections else SingleSource
                g.add_edge(in_node, v)
            if g.out_degree(v) == 0:
                out_node = v.section if use_sections else SingleTarget
                g.add_edge(v, out_node)
        return g

    def train_run_iterator(self):
        """Iterate over all `TrainRuns` of this train.

        :return: Iterator[TrainRun]
        """
        g = self.extended_train_run_graph(use_sections=False)
        if len(g.edges) == 0:
            for sr in self.section_run_iterator():
                yield TrainRun(self, [sr])
            return

        for path in nx.all_simple_paths(g, source=SingleSource, target=SingleTarget):
            yield TrainRun(self, path[1:-1])

    def to_dataframe(self, format_time=True) -> pd.DataFrame:
        train_runs = sorted(self.train_run_iterator(), key=TrainRun.start_date)
        train_ids = list(map(TrainRun.train_id, train_runs))
        result = pd.DataFrame(index=train_ids,
                              columns=self.__time_table_columns())
        result.index.name = 'Daily Train ID'
        for tr in train_runs:
            result.loc[tr.train_id()] = tr.time_table(format_time=format_time)
        if format_time:
            result = result.fillna('')
        return result

    def section_dataframes(self) -> List[pd.DataFrame]:
        return [sec.to_dataframe() for sec in self.sections]

    def calender(self):
        result = pd.DatetimeIndex([])
        for section in self.sections:
            result = result.union(section.calendar)
        return result

    def __time_table_columns(self) -> List[str]:
        col_graph = nx.DiGraph()
        trg = self.train_run_graph()
        for u in trg:
            dep = u.departure_column()
            arr = u.arrival_column()
            col_graph.add_edge(dep, arr)
        for u, v in trg.edges:
            col_graph.add_edge(u.arrival_column(), v.departure_column())
        return list(nx.topological_sort(col_graph))

    def __check_sections(self):
        # Check if section id are unique:
        section_ids = [s.section_id for s in self.sections]
        if len(section_ids) == 0:
            raise TomError(f"Train {self.train_id()} must contain at least one RouteSection")

        if len(self.sections) != len(set(section_ids)):
            raise TomError(f"Section IDs of train {self.train_id()} not unique: {section_ids}")

        # Check if section event coordinates are unique:
        key2section = dict()
        for s in self.sections:
            s.check_invariant()
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

    def __check_invariant(self):
        self.__check_sections()
        self.__check_train_run_graph()

    def __check_train_run_graph(self):
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

    def routes(self) -> ValuesView['Route']:
        route_key_to_route = {}
        for tr in self.train_run_iterator():
            route_key = tr.route_key()
            route = route_key_to_route.get(route_key, None)
            if route is None:
                route = Route(list(map(lambda sr: sr.section, tr.sections_runs)))
                route_key_to_route[route_key] = route
            route.add_date(tr.start_date())
        return route_key_to_route.values()

    def all_stations(self) -> List[str]:
        """
        :return: list of all stations of the train
        """
        return self.location_graph().nodes

    def routing_info_to_xml(self, schema: str) -> ElemTree.Element:
        jsg = "http://taf-jsg.info/schemes"
        result = ElemTree.Element('TrainInformation', attrib={
            'xmlns': jsg,
            'xmlns:xsi': "http://www.w3.org/2001/XMLSchema-instance",
            'xsi:schemaLocation': f"{jsg} {schema}/taf_cat_complete_sector.xsd",
            'RouteInfoVersion': str(self.version),
        })

        for sec in self.sections:
            sec.to_xml(result)
        for route in self.routes():
            route.to_xml(result)
        return result


def day_offset(departure: datetime, arrival: datetime) -> int:
    """
    Return number of night shifts between two timestamps
    """
    return abs(arrival.date().day - departure.date().day)


class SectionRun:
    section: RouteSection
    departure_time: datetime
    """
    -1: < RCS
    0: = RCS
    +1: > RCS
    """

    def __init__(self, section: RouteSection, time: datetime):
        self.section = section
        self.departure_time = time
        # Set to self as long as not computed in TrainRun
        self.construction_start_section_run = self
        self.position_relative_to_construction_start = 0 if section.is_construction_start else -1

    def __str__(self):
        dep = self.departure_time.strftime(f"%F %H:%M OTR={self.otr_at_departure()}")
        arr = self.arrival_time().strftime(f"%F %H:%M OTR={self.otr_at_arrival()}")
        return f"{self.section.version_info()}:{dep} {self.section} {arr}"

    def __otr_at(self, timestamp):
        dep_time_at_rcs = self.construction_start_section_run.departure_time
        pos = self.position_relative_to_construction_start
        otr = day_offset(dep_time_at_rcs, timestamp)
        return otr if pos == 0 else pos * otr

    def otr_at_arrival(self):
        return self.__otr_at(self.arrival_time())

    def otr_at_departure(self):
        return self.__otr_at(self.departure_time)

    def section_id(self):
        return str(self.section.section_id)

    def arrival_time(self) -> datetime:
        return self.departure_time + self.section.travel_time

    def arrival_formatted(self) -> str:
        return self.__format_time(self.arrival_time(), self.otr_at_arrival())

    def departure_formatted(self) -> str:
        return self.__format_time(self.departure_time, self.otr_at_departure())

    @staticmethod
    def __format_time(t, otr):
        return t.strftime(f"%a %d.%m.%y %H:%M")

    def arrival_at_departure_station(self) -> datetime:
        """:return: the timestamp when the train will arrive in the departure station

        result = departure_time - departure_stop_time
        """
        return self.departure_time - self.section.departure_stop_time

    def block_timedelta(self) -> timedelta:
        return self.section.departure_stop_time + self.section.travel_time

    def departure_station(self) -> str:
        return self.section.departure_station

    def arrival_station(self) -> str:
        return self.section.arrival_station

    def arrival_column(self) -> str:
        return f"Arrival {self.arrival_station()}"

    def departure_column(self) -> str:
        return f"Departure {self.departure_station()}"

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

        cs = list(filter(lambda x: x.section.is_construction_start, section_runs))
        if len(cs) == 0:
            raise TomError(f"No route construction start for train run {self}.")
        rcs, *rest = cs
        if len(rest) > 1:
            raise TomError(f"Can only have one construction begin in train run {self}. "
                           f"List of construction begins: {cs}.")
        pos = -1
        for sr in section_runs:
            sr.construction_start_section_run = rcs
            if sr.position_relative_to_construction_start == 0:
                pos = 1
            else:
                sr.position_relative_to_construction_start = pos

    def __str__(self):
        return self.train_id()

    def train_id(self):
        return f"{self.train.train_id(variant=self.first_run().section_id())}/{self.start_date()}"

    def route_key(self):
        return '-'.join(map(SectionRun.section_id, self.sections_runs))

    def start_date(self):
        return self.first_run().departure_time.strftime("%F")

    def first_run(self):
        return self.sections_runs[0]

    def time_table(self, format_time=True) -> Dict[str, str]:
        result = {}
        for sr in self.sections_runs:
            arr = sr.arrival_formatted() if format_time else sr.arrival_time()
            dep = sr.departure_formatted() if format_time else sr.departure_time
            result[sr.arrival_column()] = arr
            result[sr.departure_column()] = dep
        return result

    def time_table_events(self) -> Tuple[List[str], List[datetime]]:
        stations: List[str] = []
        timestamps: List[datetime] = []
        for station, ts in self.time_table_event_iterator():
            stations.append(station)
            timestamps.append(ts)
        return stations, timestamps

    def location_iterator(self):
        yield self.first_run().departure_station()
        for sr in self.sections_runs:
            yield sr.arrival_station()

    def time_table_event_iterator(self):
        sr: SectionRun
        for sr in self.sections_runs:
            yield sr.departure_station(), sr.departure_time
            yield sr.arrival_station(), sr.arrival_time()

    def time_table_event_iterator2(self):
        sr: SectionRun
        zero_delta = pd.Timedelta(0)
        for sr in self.sections_runs:
            ds = sr.departure_station()
            dt = sr.departure_time
            section = sr.section
            stop_time = section.departure_stop_time
            if stop_time > zero_delta:
                yield [ds, ds], \
                      [dt, dt - stop_time], section
            yield [ds, sr.arrival_station()], \
                  [dt, sr.arrival_time()], section


class Route:
    """
    A Route is a sequence of RouteSection where consecutive section must fit together:

    If (prev, next) is a tuple in the sections, then

       prev.arrival_station == next.departure_station

    NOTE: The here proposed TOM model does not need routes! They are instead modeled as TrainRuns
    which are computed from RouteSection (see Train.train_run_iterator)

    """
    sections: List[RouteSection]
    calendar: DatetimeIndex = DatetimeIndex([])

    def __init__(self, sections: List[RouteSection]):
        if len(sections) == 0:
            raise TomError("No sections in route")
        # Check if sections form a route
        for prev, curr in zip(sections, sections[1:]):
            if prev.arrival_station != curr.departure_station:
                raise TomError(f"Route sections do not fit: {prev} != {curr}")
        self.sections = sections

    def __str__(self):
        return self.sections[0].departure_station + \
               '-' + \
               '-'.join([s.arrival_station for s in self.sections])

    def add_date(self, d: str):
        self.calendar = self.calendar.union(DatetimeIndex([d]))

    def route_key(self):
        return '-'.join(map(lambda s: str(s.section_id), self.sections))

    def description(self, with_bitmap=True) -> str:
        first_section = self.sections[0]
        dep = first_section.departure_time().strftime("%H:%M")
        fd = self.first_day().strftime("%d/%m")
        ld = self.last_day().strftime("%d/%m")
        bitmap = ' ' + compute_bitmap_days(self.calendar) if with_bitmap else ''
        result = f"Route     : {self}\n"
        result += f"Key       : {self.route_key()}\n"
        result += f"Calendar  : {fd} to {ld} {bitmap}\n"
        result += f"Start   at: {dep} in {first_section.departure_station}\n"
        for sec in self.sections:
            arr = sec.arrival_time().strftime("%H:%M")
            result += f"Arrival at: {arr} in {sec.arrival_station}\n"
        return result

    def first_day(self):
        return datetime.date(self.calendar[0])

    def last_day(self):
        return datetime.date(self.calendar[-1])

    def to_xml(self, parent: ElemTree.Element):
        route = ElemTree.SubElement(parent, 'Route', {'key': self.route_key()})
        xml_add_calendar(self, route)
        for loc, t, tc, offset in self.journey_location_iter():
            xml_add_journey_location(route, loc, t, type_code=tc, offset=offset)

    def journey_location_iter(self):
        first_section = self.sections[0]
        last_section = self.sections[-1]
        yield first_section.departure_station, \
              first_section.departure_time(), \
              TSI_LOCATION_TYPE_CODES['Origin'], 0

        for sec in self.sections:
            tc_arrival = 'Destination' if last_section == sec else 'Handover'
            yield sec.arrival_station, \
                  sec.arrival_time(), \
                  TSI_LOCATION_TYPE_CODES[tc_arrival], \
                  day_offset(sec.arrival_time(), sec.departure_time())


def __make_section_from_dict(section: dict) -> RouteSection:
    try:
        tt = pd.Timedelta(section['travel_time'])
    except TypeError as e:
        raise e
    stop_time = pd.Timedelta(section.get('stop_time', 0))
    cal = __make_calendar(section.get('calendar', None))
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
    result.color = section.get('color', None)
    return result


def __make_calendar(spec: dict):
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

    sections = [__make_section_from_dict(d) for d in td['sections']]
    # Give each sections a unique section id:
    for i in range(0, len(sections)):
        s = sections[i]
        if s.section_id is None:
            s.section_id = i

    result = Train(td['coreID'], sections=sections)
    result.version = td.get('version', 1)
    return result
