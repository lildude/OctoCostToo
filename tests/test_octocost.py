from appdaemon_testing.pytest import automation_fixture
from apps.octocost.octocost import OctoCost

import pytest
import datetime
import json

@automation_fixture(
  OctoCost,
  args= {
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

