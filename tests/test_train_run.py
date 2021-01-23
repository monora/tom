#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `Train runs` package."""
from typing import List

from tom.tom import RouteSection, Train, SectionRun, TrainRun


def test_route_section_run(ac_to_emm: RouteSection):
    section_runs: List[SectionRun] = list(ac_to_emm)
    assert len(section_runs) == 31


def test_route_section_run_ac_ff(train_ac_ff: Train):
    t = train_ac_ff
    r = list(t.sections[0])  # AC - EMM
    assert len(r) == 18

    first_run: SectionRun = r[0]
    last_run: SectionRun = r[17]

    assert str(first_run.departure_time) == '2021-12-01 23:50:00'
    assert str(last_run.departure_time) == '2021-12-30 23:50:00'


def test_train_section_run_iterator(train_ac_to_emm):
    section_runs = list(train_ac_to_emm.section_run_iterator())
    assert len(section_runs) == 31


def test_train_run_iterator_simple(train_ac_to_emm):
    train_runs: List[TrainRun] = list(train_ac_to_emm.train_run_iterator())
    assert len(train_runs) == 31

    assert train_runs[0].train_id() == 'TR/8350/12AB/00/2021/2021-12-01'
    assert train_runs[-1].train_id() == 'TR/8350/12AB/00/2021/2021-12-31'


def test_train_run_iterator(yml_train):
    expected = {
        'TR-30AB-1': {0: 'TR/8350/30AB/10/2020/2020-12-01',
                      -1: 'TR/8350/30AB/10/2020/2020-12-02'},
        'TR-23AB-1': {0: 'TR/8350/23AB/10/2020/2020-12-01',
                      -1: 'TR/8350/23AB/10/2020/2020-12-02'},
        'TR-23AB-2': {0: 'TR/8350/23AB/11/2020/2020-12-01',
                      -1: 'TR/8350/23AB/12/2020/2020-12-02'},
        'TR-ID1-1': {0: 'TR/8350/ID1/10/2021/2021-02-01',
                     -1: 'TR/8350/ID1/30/2021/2021-02-20'},
        'TR-ID1-2': {0: 'TR/8350/ID1/10/2021/2021-02-01',
                     -1: 'TR/8350/ID1/30/2021/2021-02-20'},
        'TR-ID1-3': {0: 'TR/8350/ID1/10/2021/2021-02-01',
                     -1: 'TR/8350/ID1/30/2021/2021-02-20'},
        'TR-12AB-1': {0: 'TR/8350/12AB/10/2021/2021-12-01',
                      -1: 'TR/8350/12AB/20/2021/2021-12-31'},
        'TR-12AB-2': {0: 'TR/8350/12AB/10/2021/2021-12-02',
                      -1: 'TR/8350/12AB/20/2021/2021-12-31'},
        'TR-13AB-1': {0: 'TR/8350/13AB/10/2020/2020-12-01',
                      -1: 'TR/8350/13AB/10/2020/2020-12-31'},
        'TR-13AB-2': {0: 'TR/8350/13AB/10/2020/2020-12-01',
                      -1: 'TR/8350/13AB/10/2020/2020-12-31'},
    }
    t = yml_train
    train_runs = sorted(t.train_run_iterator(), key=TrainRun.start_date)
    if t.id() in ['TR-ID1-1', 'TR-ID1-2', 'TR-ID1-3']:
        assert len(train_runs) == 20
    elif t.id() in ['TR-23AB-1', 'TR-23AB-2', 'TR-30AB-1']:
        assert len(train_runs) == 2
    else:
        assert len(train_runs) == 31

    for i in [0, -1]:
        assert train_runs[i].train_id() == expected[yml_train.id()][i]


def test_otr(train_otr):
    train_runs: List[TrainRun] = list(train_otr.train_run_iterator())
    assert len(train_runs) == 2

    t_12_01 = train_runs[0]
    otrs = [(sr.otr_at_departure(), sr.otr_at_arrival()) for sr in t_12_01.sections_runs]
    assert otrs == [(-1, 0), (0, 0), (0, 1)]

    t_12_02 = train_runs[1]
    otrs = [(sr.otr_at_departure(), sr.otr_at_arrival()) for sr in t_12_02.sections_runs]
    assert otrs == [(-2, -1), (0, 0), (0, 1)]
