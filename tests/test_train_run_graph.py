#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Graphing Tests for `Train runs` package."""
import networkx as nx
from tom import config

from tom.tom import Train, SectionRun\

def test_train_run_graph_zero(train_ac_to_emm: Train):
    g = train_ac_to_emm.train_run_graph()
    assert isinstance(g, nx.DiGraph)
    assert len(g) == 0


def test_train_run_graph_ac_ff(train_ac_ff: Train):
    t = train_ac_ff
    # 31 runs per 2 RouteSection
    assert len(list(t.section_run_iterator())) == 31 * 2

    g = t.train_run_graph()
    assert isinstance(g, nx.DiGraph)
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
    summe = a_c + b_c + c_e + e_f + e_g
    assert len(list(t.section_run_iterator())) == summe

    g = t.train_run_graph()
    assert len(g) == summe
    # 31 TrainRuns! One for each day. Each TrainRun uses two SectionsRun which are connected
    assert len(g.edges) == 31 * 2


def test_train_run_graph_annex_4(train_annex_4: Train):
    t = train_annex_4
    no_of_calender_days = 2 * 7 + 6
    s = t.section_dataframes()
    section_runs = list(t.section_run_iterator())
    # Per day 2 section runs
    assert len(section_runs) == no_of_calender_days * 2

    g = t.train_run_graph()
    assert len(g) == no_of_calender_days * 2
    assert len(g.edges) == no_of_calender_days


def test_train_run_graph_annex_4_2(train_annex_4_2: Train):
    t = train_annex_4_2
    no_of_calender_days = 2 * 7 + 6
    s = t.section_dataframes()
    section_runs = list(t.section_run_iterator())
    # Per day 2 section runs
    assert len(section_runs) == no_of_calender_days * 2

    g = t.train_run_graph()
    assert len(g) == no_of_calender_days * 2
    assert len(g.edges) == no_of_calender_days


def _graphml_train_run_graph(t: Train, filename: str):
    g = t.extended_train_run_graph()
    for node in g.nodes():
        g.nodes[node]['label'] = str(node)
        if type(node) == SectionRun:
            sr: SectionRun = node
            g.nodes[node]['id'] = sr.section_id()
            g.nodes[node]['route_id'] = sr.section.route_id()
    # nx.readwrite.write_graphml(g, path=(tmpdir / 'train-ac-ff.graphml'))
    nx.readwrite.write_graphml(g, path=config.output_file(filename, 'graphml'))


def test_graphml_train_run_graph(yml_train: Train):
    t = yml_train
    _graphml_train_run_graph(t, f"train-{t.id()}")


def test_location_graph_aa_ff(train_ac_ff):
    lg = train_ac_ff.location_graph()
    assert list(lg.edges) == [('AC', 'EMM'),
                              ('AC', 'Venlo'),
                              ('EMM', 'FF'),
                              ('Venlo', 'FF')]


def test_location_graph_a_f(train_a_f):
    lg = train_a_f.location_graph()
    assert sorted(lg.edges) == [('A', 'C'),
                                ('B', 'C'),
                                ('C', 'E'),
                                ('E', 'F'),
                                ('E', 'G')]
    assert list(nx.topological_sort(lg)) == ['A', 'B', 'C', 'E', 'G', 'F']


def test_location_graph_annex_4(train_annex_4):
    lg = train_annex_4.location_graph()
    assert sorted(lg.edges) == [('D', 'H1'),
                                ('H1', 'T'),
                                ('S', 'H1'),
                                ]
    assert list(nx.topological_sort(lg)) == ['D', 'S', 'H1', 'T']


def _graphml_section_graph(g: nx.DiGraph, filename: str):
    nx.readwrite.write_graphml(g, path=config.output_file(filename, 'graphml'))


def test_section_graph(yml_train):
    t = yml_train
    sg = t.section_graph()
    _graphml_section_graph(sg, f"route-section-graph-{t.id()}")
