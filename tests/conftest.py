from datetime import timedelta

import pytest
import tom
import yaml
import pandas as pd

from tom.tom import *


@pytest.fixture()
def ac_to_emm():
    begin = '2021-12-01 23:50:00'
    cal = pd.date_range(begin, periods=31, freq='D')
    travel_time = timedelta(hours=2, minutes=10)
    r = RouteSection(departure="AC",
                     arrival="EMM",
                     travel_time=travel_time,
                     departure_timestamps=cal)
    return r


def _make_train(d: PosixPath, yml: str):
    f = (d / (yml + '.yml'))
    return make_train_from_yml(f)


@pytest.fixture
def train_ac_ff(shared_datadir):
    return _make_train(shared_datadir, 'train-ac-ff')


@pytest.fixture
def train_a_f(shared_datadir):
    return _make_train(shared_datadir, 'train-a-f')
