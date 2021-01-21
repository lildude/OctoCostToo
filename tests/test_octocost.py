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
    "gas": {
      "mprn": "54321",
      "gas_serial": "98765",
      "gas_tariff": "FIX-12M-20-09-21",
      "gas_start_date": "2020-12-27"
    },
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

@pytest.mark.usefixtures(
    "mock_elec_consumption_one_day",
    "mock_elec_agile_cost_one_day"
)
def test_calculate_cost_and_usage_agile_elec_only(octocost: OctoCost):
    octocost.yesterday = datetime.date(2021, 1, 18)
    octocost.use_url = octocost.elec_consumption_url
    octocost.cost_url = octocost.agile_cost_url
    start_day = datetime.date(2021, 1, 18)

    usage, cost = octocost.calculate_cost_and_usage(start_day)
    assert usage == 7.701
    assert cost == 108.6035

@pytest.mark.usefixtures(
    "mock_gas_consumption_one_day",
    "mock_gas_rates",
)
def test_calculate_cost_and_usage_standard_unit_rate_gas_only(octocost: OctoCost):
    octocost.yesterday = datetime.date(2021, 1, 18)
    octocost.use_url = octocost.gas_consumption_url
    octocost.cost_url = octocost.gas_cost_url
    start_day = datetime.date(2021, 1, 18)

    usage, cost = octocost.calculate_cost_and_usage(start_day)
    assert usage == 7.701
    assert cost == 246.7063  # Should be (7.701 * 11.1868 * 2.6565) + 17.85

@pytest.mark.usefixtures(
    "mock_elec_consumption_one_day",
    "mock_elec_fixed_rates"
)
def test_calculate_cost_and_usage_standard_unit_rate_elec_only(octocost: OctoCost):
    octocost.yesterday = datetime.date(2021, 1, 18)
    octocost.use_url = octocost.elec_consumption_url
    octocost.cost_url = octocost.elec_cost_url
    start_day = datetime.date(2021, 1, 18)

    usage, cost = octocost.calculate_cost_and_usage(start_day)
    assert usage == 7.701
    assert cost == 143.5038  # Should be (7.701 * 16.0125) + 20.1915

@pytest.mark.usefixtures(
    "mock_elec_consumption_five_days"
)
def test_calculate_cost_and_usage_standard_unit_rate_elec_only_five_days(octocost: OctoCost):
    octocost.yesterday = datetime.date(2021, 1, 18)
    octocost.use_url = octocost.elec_consumption_url
    octocost.cost_url = octocost.elec_cost_url
    start_day = datetime.date(2021, 1, 14)

    usage, cost = octocost.calculate_cost_and_usage(start_day)
    assert usage == 41.168
    assert cost == 760.1601  # Should be (41.168 * 16.0125) + (20.1915 * 5)



