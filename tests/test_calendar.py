#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `tom` package."""
from typing import Any, Union

import pytest

from tom import tom
import pandas as pd

from tom.tom import Train


def test_route_section_instance(ac_to_emm):
    isinstance(ac_to_emm, tom.RouteSection)
    assert str(ac_to_emm.first_day()) == "2021-12-01"
    assert str(ac_to_emm.last_day()) == "2021-12-31"

    assert ac_to_emm.departure == "AC"
    assert ac_to_emm.arrival == "EMM"

    assert str(ac_to_emm.departure_time()) == '2021-12-01 23:50:00'
    assert str(ac_to_emm.arrival_time()) == '2021-12-02 02:00:00'


def test_to_dataframe(ac_to_emm):
    df = ac_to_emm.to_dataframe()
    assert df['AC'][0] == ac_to_emm.departure_time()
    assert df['EMM'][0] == ac_to_emm.arrival_time()


def test_train_from_yml(train_ac_ff):
    t: Union[Train, Any] = train_ac_ff
    assert isinstance(t, Train)
    assert t.core_id == '12AB'

    r = t.routes[0]
    rs = r.sections[0]  # AC - EMM
    assert rs.departure == 'AC'
    assert rs.arrival == 'EMM'
    assert str(rs) == 'AC->EMM'
    assert str(r) == 'AC->EMM,EMM->FF'

    assert str(rs.departure_time()) == '2021-12-01 23:50:00'
    assert str(rs.arrival_time()) == '2021-12-02 02:00:00'

    assert str(rs.first_day()) == '2021-12-01'
    assert str(rs.last_day()) == '2021-12-30'

    r = t.routes[1]
    rs = r.sections[0]
    assert rs.departure == 'AC'
    assert rs.arrival == 'Venlo'
    assert str(rs) == 'AC->Venlo'
    assert str(r) == 'AC->Venlo,Venlo->FF'

    assert str(rs.departure_time()) == '2021-12-03 23:50:00'
    assert str(rs.arrival_time()) == '2021-12-04 02:00:00'

    assert str(rs.first_day()) == '2021-12-03'
    assert str(rs.last_day()) == '2021-12-31'


def test_route_to_df(train_ac_ff):
    df = train_ac_ff.routes[0].to_dataframe()
    assert len(df) == 18
    assert list(df.columns) == ['AC', 'EMM']


def test_section_to_df(train_ac_ff):
    df = train_ac_ff.routes[0].sections[0].to_dataframe()
    assert len(df) == 18
    assert list(df.columns) == ['AC', 'EMM']

    df = train_ac_ff.routes[0].sections[1].to_dataframe()
    assert len(df) == 18
    assert list(df.columns) == ['EMM', 'FF']

    df = train_ac_ff.routes[1].sections[0].to_dataframe()
    assert len(df) == 13
    assert list(df.columns) == ['AC', 'Venlo']

    df = train_ac_ff.routes[1].sections[1].to_dataframe()
    assert len(df) == 13
    assert list(df.columns) == ['Venlo', 'FF']

def test_train_a_f(train_a_f):
    assert len(train_a_f.routes) == 3
