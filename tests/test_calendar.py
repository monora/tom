#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `tom` package."""
from typing import Any, Union

from tom import tom
import pandas as pd

from tom.tom import Train


def test_route_section_instance(ac_to_emm):
    isinstance(ac_to_emm, tom.RouteSection)
    assert str(ac_to_emm.first_day()) == "2021-12-01"
    assert str(ac_to_emm.last_day()) == "2021-12-31"

    assert ac_to_emm.departure_station == "AC"
    assert ac_to_emm.arrival_station == "EMM"

    assert str(ac_to_emm.departure_time()) == '2021-12-01 23:50:00'
    assert str(ac_to_emm.arrival_time()) == '2021-12-02 02:00:00'
    assert ac_to_emm.departure_stop_time == pd.Timedelta(0)


def test_to_dataframe(ac_to_emm):
    df = ac_to_emm.to_dataframe()
    assert df['AC'][0] == ac_to_emm.departure_time()
    assert df['EMM'][0] == ac_to_emm.arrival_time()


def test_train_from_yml(train_ac_ff):
    t: Union[Train, Any] = train_ac_ff
    assert isinstance(t, Train)
    assert t.core_id == '12AB'

    rs = t.sections[0]  # AC - EMM
    assert rs.departure_station == 'AC'
    assert rs.arrival_station == 'EMM'
    assert str(rs) == 'AC-EMM'

    assert str(rs.departure_time()) == '2021-12-01 23:50:00'
    assert str(rs.arrival_time()) == '2021-12-02 02:00:00'

    assert str(rs.first_day()) == '2021-12-01'
    assert str(rs.last_day()) == '2021-12-30'

    rs = t.sections[2]
    assert rs.departure_station == 'AC'
    assert rs.arrival_station == 'Venlo'
    assert str(rs) == 'AC-Venlo'

    assert str(rs.departure_time()) == '2021-12-03 23:50:00'
    # 0 is default stop time
    assert rs.departure_stop_time == pd.Timedelta(0)
    assert str(rs.arrival_time()) == '2021-12-04 01:55:00'

    assert str(rs.first_day()) == '2021-12-03'
    assert str(rs.last_day()) == '2021-12-31'

    rs = t.sections[3]
    assert rs.departure_stop_time == pd.Timedelta('00:05:00')


def _check_to_df(t: Train, index: int, size: int, cols):
    df = t.sections[index].to_dataframe()[cols]
    assert len(df) == size
    assert list(df.columns) == cols


def test_section_to_df_aa_ff(train_ac_ff):
    assert len(train_ac_ff.sections) == 4
    _check_to_df(train_ac_ff, 0, 18, ['AC', 'EMM'])
    _check_to_df(train_ac_ff, 1, 18, ['EMM', 'FF'])
    _check_to_df(train_ac_ff, 2, 13, ['AC', 'Venlo'])
    _check_to_df(train_ac_ff, 3, 13, ['Venlo', 'FF'])


def test_section_to_df_a_f(train_a_f: Train):
    assert len(train_a_f.sections) == 5
    _check_to_df(train_a_f, 0, 31 - 4, ['B', 'C'])
    _check_to_df(train_a_f, 1, 4, ['A', 'C'])
    _check_to_df(train_a_f, 2, 31, ['C', 'E'])
    # Section E-F starts at 2.12. and ends on 1.1. (=> also 31 days)
    _check_to_df(train_a_f, 3, 31 - 4, ['E', 'F'])
    _check_to_df(train_a_f, 4, 4, ['E', 'G'])


def test_train_to_df(yml_train):
    expected = {
        'TR-ID1-1': 2 * 7 + 6,
        'TR-ID1-2': 2 * 7 + 6,
        'TR-ID1-3': 2 * 7 + 6,
        'TR-12AB-1': 31,
        'TR-12AB-2': 31,
        'TR-13AB-1': 31,
        'TR-13AB-2': 31,
    }
    t = yml_train
    df = t.to_dataframe()
    # sec_dfs = t.section_dataframes()
    # if t.id() == 'TR-ID1-3':
    assert len(df) == expected[t.id()]
    df.to_excel(f"train-{t.id()}.xlsx")
    _to_csv(df, t)


def _fmt_timestamp(x):
    try:
        return x.strftime("``%a %d.%m.%y %H:%M``")
    except ValueError:
        return ''


def _to_csv(df: pd.DataFrame, t: Train):
    for c in df.columns:
        df[c] = df[c].apply(_fmt_timestamp)
    df.to_csv(f"train-{t.id()}.csv")
