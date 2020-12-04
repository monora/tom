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
    c = t.route_sections[0]
    assert c.departure == 'AC'
    assert c.arrival == 'EMM'

    assert str(c.departure_time()) == '2021-12-01 23:50:00'
    assert str(c.arrival_time()) == '2021-12-02 02:00:00'

    assert str(c.first_day()) == '2021-12-01'
    assert str(c.last_day()) == '2021-12-31'


def test_train_to_df(train_ac_ff):
    df = train_ac_ff.route_sections[0].to_dataframe()
    assert len(df) == 31
    assert list(df.columns) == ['AC', 'EMM']
