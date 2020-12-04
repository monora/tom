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


@pytest.fixture
def train_ac_ff(shared_datadir):
    f = (shared_datadir / 'train-ac-ff.yml')
    return make_train_from_yml(f)
