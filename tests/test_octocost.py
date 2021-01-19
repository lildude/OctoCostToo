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
