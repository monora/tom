#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `Train runs` package."""
from typing import List
from networkx import DiGraph
from tom.tom import RouteSection, Train, SectionRun


def test_route_section_run(ac_to_emm: RouteSection):
    section_runs: List[SectionRun] = list(ac_to_emm)
    assert len(section_runs) == 31


def test_route_section_run_ac_ff(train_ac_ff: Train):
    t = train_ac_ff
    r = list(t.sections[0])  # AC - EMM
    assert len(r) == 18

    first_run: SectionRun = r[0]
    last_run: SectionRun = r[17]

    assert str(first_run.departure_at_origin) == '2021-12-01 23:50:00'
    assert str(last_run.departure_at_origin) == '2021-12-30 23:50:00'

def test_train_run_iterator(tr_ac_to_emm):
    truns = list(tr_ac_to_emm.section_run_iterator())
    assert len(truns) == 31

def test_train_run_graph_zero(tr_ac_to_emm: Train):
    g = tr_ac_to_emm.train_run_graph()
    assert isinstance(g, DiGraph)
    assert len(g) == 0

def test_train_run_graph_ac_ff(train_ac_ff: Train):
    t = train_ac_ff
    # 31 runs per 2 RouteSection
    assert len(list(t.section_run_iterator())) == 31 * 2

    g = t.train_run_graph()
    assert isinstance(g, DiGraph)
    # g.nodes == set(t.section_run_iterator())
    assert len(g) == 31 * 2
    # 31 TrainRuns! One for each day
    assert len(g.edges) == 31

def test_train_run_graph_a_f(train_a_f: Train):
    t = train_a_f
    a_c = 4
    b_c = 31 - a_c
    c_e = 31
    e_g = 4
    e_f = 31 - e_g
    sum = a_c + b_c + c_e + e_f + e_g
    assert len(list(t.section_run_iterator())) == sum

    g = t.train_run_graph()
    assert len(g) == sum
    # 31 TrainRuns! One for each day. Each TrainRun uses two SectionsRun which are connected
    assert len(g.edges) == 31*2

