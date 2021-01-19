from appdaemon_testing.pytest import automation_fixture
from apps.octocost.octocost import OctoCost

import pytest
import datetime
import json

@automation_fixture(
  OctoCost,
  args= {
    "auth": "sk_live_abcdefghijklmnopqrstuvwxyz",
    "mpan": "12345",
    "region": "H",
    "serial": "67890",
    "start_date": "2020-12-27",
  },
  initialize=True
)

def octocost() -> OctoCost:
    pass

@pytest.mark.usefixtures("mock_elec_meter_points")
def test_find_region(octocost: OctoCost):
    assert "H" == octocost.find_region("12345")

def test_calculate_count(octocost: OctoCost):
    octocost.yesterday = datetime.date(2020, 1, 19)
    start_day = datetime.date(2020, 1, 19)
    # One day's worth of 30 minute windows between start and end of the same day
    assert 47 == octocost.calculate_count(start_day)
    start_day = datetime.date(2020, 1, 18)
    # Two day's worth of 30 minute windows between start and end of the same day
    assert 95 == octocost.calculate_count(start_day)

@pytest.mark.usefixtures("mock_elec_consumption_one_day", "mock_elec_agile_cost_one_day")
def test_calculate_cost_and_usage(octocost: OctoCost):
    octocost.yesterday = datetime.date(2021, 1, 18)
    octocost.use_url = octocost.elec_consumption_url
    octocost.gas = False
    start_day = datetime.date(2021, 1, 18)

    usage, cost = octocost.calculate_cost_and_usage(start_day)
    assert usage == 7.700999999999998
    assert cost == 108.60350550000001


