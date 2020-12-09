#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Graphing Tests for `Train runs` package."""
import networkx as nx

from tom.tom import Train


def _graphml_train_run_graph(t: Train, filename: str):
    g = t.extended_train_run_graph()
    for node in g.nodes():
        g.nodes[node]['label'] = str(node)
    # nx.readwrite.write_graphml(g, path=(tmpdir / 'train-ac-ff.graphml'))
    nx.readwrite.write_graphml(g, path=(filename + '.graphml'))


def test_graphml_train_run_graph_ac_ff(train_ac_ff: Train):
    _graphml_train_run_graph(train_ac_ff, 'train-ac-ff')


def test_graphml_train_run_graph_a_f(train_a_f: Train):
    _graphml_train_run_graph(train_a_f, 'train-a-f')
