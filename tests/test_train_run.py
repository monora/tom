#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `Train runs` package."""
from typing import List
from networkx import DiGraph

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

    assert train_runs[0].train_id() == 'TR/8350/12AB/00/0/2021-12-01'
    assert train_runs[-1].train_id() == 'TR/8350/12AB/00/0/2021-12-31'


def test_train_run_iterator(yml_train):
    expected = {
        'TR-12AB-1': {0: 'TR/8350/12AB/00/1/2021-12-01',
                      -1: 'TR/8350/12AB/00/3/2021-12-31'},
        'TR-12AB-2': {0: 'TR/8350/12AB/00/1/2021-12-02',
                      -1: 'TR/8350/12AB/00/3/2021-12-31'},
        'TR-13AB-1': {0: 'TR/8350/13AB/00/0/2020-12-01',
                      -1: 'TR/8350/13AB/00/1/2020-12-26'},
        'TR-13AB-2': {0: 'TR/8350/13AB/00/0/2020-12-03',
                      -1: 'TR/8350/13AB/00/2/2020-12-26'}
    }
    train_runs = list(yml_train.train_run_iterator())
    assert len(train_runs) == 31
    for i in [0, -1]:
        assert train_runs[i].train_id() == expected[yml_train.id()][i]
