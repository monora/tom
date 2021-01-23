#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `Train runs` package."""
from typing import List

from tom.tom import RouteSection, Train, SectionRun, TrainRun, Route


def test_routes_ac_ff(train_ac_ff: Train):
    t = train_ac_ff
    routes = list(t.routes())  # AC - EMM
    assert len(routes) == 2

    r: Route
    r = routes[0]
    assert str(r) == 'AC-EMM-FF'
    assert r.route_key() == '10-11'

    assert len(r.calendar) == 18
    assert str(r.calendar[0]) == '2021-12-01 00:00:00'
    assert str(r.calendar[-1]) == '2021-12-30 00:00:00'

    r = routes[1]
    assert str(r) == 'AC-Venlo-FF'
    assert r.route_key() == '20-21'

    assert len(r.calendar) == 13
    assert str(r.calendar[0]) == '2021-12-03 00:00:00'
    assert str(r.calendar[-1]) == '2021-12-31 00:00:00'


def test_routes_a_f(train_a_f: Train):
    t = train_a_f
    routes = list(t.routes())  # AC - EMM
    assert len(routes) == 3
    assert list(map(str, routes)) == ['B-C-E-F', 'B-C-E-G', 'A-C-E-F']
    # assert routes[0].description() == ''
