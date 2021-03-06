import pytest

from tom.tom import *


@pytest.fixture()
def ac_to_emm():
    begin = '2021-12-01'
    cal = pd.date_range(begin, periods=31, freq='D')
    travel_time = timedelta(hours=2, minutes=10)
    r = RouteSection(departure_station="AC",
                     arrival_station="EMM",
                     travel_time=travel_time,
                     calendar=cal,
                     departure_daytime='23:50:00'
                     )
    return r


@pytest.fixture()
def train_ac_to_emm(ac_to_emm):
    return Train('12AB', sections=[ac_to_emm])


def _make_train(d: PosixPath, yml: str) -> Train:
    f = (d / (yml + '.yml'))
    return make_train_from_yml(f)


@pytest.fixture
def train_ac_ff(shared_datadir):
    return _make_train(shared_datadir, 'train-ac-ff-v1')


@pytest.fixture
def train_a_f(shared_datadir):
    return _make_train(shared_datadir, 'train-a-f')


@pytest.fixture
def train_annex_4(shared_datadir):
    return _make_train(shared_datadir, 'train-annex-4')


@pytest.fixture
def train_annex_4_2(shared_datadir):
    return _make_train(shared_datadir, 'train-annex-4-2')


@pytest.fixture
def train_condensed(shared_datadir):
    return _make_train(shared_datadir, 'train-condensed-2')


@pytest.fixture
def train_otr(shared_datadir):
    return _make_train(shared_datadir, 'train-otr-test-1')


ALL_TEST_TRAINS = ["train-ac-ff-v1",
                   "train-a-f",
                   "train-ac-ff-v2",
                   "train-a-f-v2",
                   "train-annex-4",
                   "train-annex-4-2",
                   "train-annex-4-3",
                   "train-condensed-1",
                   "train-condensed-2",
                   "train-otr-test-1",
                   ]

ALL_TRAINS = ALL_TEST_TRAINS + ["train-ac-zue-1",
                                "train-ac-zue-2",
                                "train-ac-ff-without-timing",
                                ]


@pytest.fixture(params=ALL_TEST_TRAINS)
def yml_train(shared_datadir, request) -> Train:
    return _make_train(shared_datadir, request.param)


@pytest.fixture(params=ALL_TRAINS)
def all_trains(shared_datadir, request) -> Train:
    return _make_train(shared_datadir, request.param)
