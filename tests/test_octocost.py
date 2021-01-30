import datetime
import json
from unittest.mock import Mock

import pytest
from appdaemon_testing.pytest import automation_fixture
from freezegun import freeze_time

from apps.octocost.octocost import OctoCost


@automation_fixture(
    OctoCost,
    args={
        "auth": "sk_live_abcdefghijklmnopqrstuvwxyz",
        "mpan": "12345",
        "region": "H",
        "serial": "67890",
        "start_date": "2020-12-27",
        "comparison_tariff": "FIX-12M-20-09-21",
        "gas": {
            "mprn": "54321",
            "gas_serial": "98765",
            "gas_tariff": "FIX-12M-20-09-21",
            "gas_start_date": "2020-12-27",
        },
    },
    initialize=True,
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


def test_tariff_url(octocost: OctoCost):
    default_url = octocost.tariff_url()
    gas_tariff_std_chg_url = octocost.tariff_url(
        energy="gas", tariff="FIX-12M-20-09-21", units="standing-charges"
    )

    assert (
        default_url
        == "https://api.octopus.energy/v1/products/AGILE-18-02-21/electricity-tariffs/E-1R-AGILE-18-02-21-H/standard-unit-rates/"
    )
    assert (
        gas_tariff_std_chg_url
        == "https://api.octopus.energy/v1/products/FIX-12M-20-09-21/gas-tariffs/G-1R-FIX-12M-20-09-21-H/standing-charges/"
    )


def test_consumption_url(octocost: OctoCost):
    default_url = octocost.consumption_url()
    gas_consumption_url = octocost.consumption_url("gas")

    assert (
        default_url
        == "https://api.octopus.energy/v1/electricity-meter-points/12345/meters/67890/consumption/"
    )
    assert (
        gas_consumption_url
        == "https://api.octopus.energy/v1/gas-meter-points/54321/meters/98765/consumption/"
    )


@pytest.mark.usefixtures(
    "mock_elec_consumption_one_day", "mock_elec_agile_cost_one_day"
)
def test_calculate_cost_and_usage_agile_elec_only(octocost: OctoCost):
    octocost.yesterday = datetime.date(2021, 1, 18)
    octocost.use_url = octocost.consumption_url()
    octocost.cost_url = octocost.tariff_url()
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
    octocost.use_url = octocost.consumption_url("gas")
    octocost.cost_url = octocost.tariff_url(energy="gas", tariff=octocost.gas_tariff)
    start_day = datetime.date(2021, 1, 18)

    usage, cost = octocost.calculate_cost_and_usage(start_day)
    assert usage == 7.701
    assert cost == 246.7063  # Should be (7.701 * 11.1868 * 2.6565) + 17.85


@pytest.mark.usefixtures("mock_elec_consumption_one_day", "mock_elec_fixed_rates")
def test_calculate_cost_and_usage_standard_unit_rate_elec_only(octocost: OctoCost):
    octocost.yesterday = datetime.date(2021, 1, 18)
    octocost.use_url = octocost.consumption_url()
    octocost.cost_url = octocost.tariff_url(tariff=octocost.comparison_tariff)
    start_day = datetime.date(2021, 1, 18)

    usage, cost = octocost.calculate_cost_and_usage(start_day)
    assert usage == 7.701
    assert cost == 143.5038  # Should be (7.701 * 16.0125) + 20.1915


@pytest.mark.usefixtures("mock_elec_consumption_five_days")
def test_calculate_cost_and_usage_standard_unit_rate_elec_only_five_days(
    octocost: OctoCost,
):
    octocost.yesterday = datetime.date(2021, 1, 18)
    octocost.use_url = octocost.consumption_url()
    octocost.cost_url = octocost.tariff_url(tariff=octocost.gas_tariff)
    start_day = datetime.date(2021, 1, 14)

    usage, cost = octocost.calculate_cost_and_usage(start_day)
    assert usage == 41.168
    assert cost == 760.1601  # Should be (41.168 * 16.0125) + (20.1915 * 5)


def test_callbacks_run_in(hass_driver, octocost: OctoCost):
    run_in = hass_driver.get_mock("run_in")
    run_in.assert_any_call(
        octocost.cost_and_usage_callback,
        65,
        use="https://api.octopus.energy/v1/gas-meter-points/54321/meters/98765/consumption/",
        cost="https://api.octopus.energy/v1/products/FIX-12M-20-09-21/gas-tariffs/G-1R-FIX-12M-20-09-21-H/standard-unit-rates/",
        date=datetime.date(2020, 12, 27),
    )
    run_in.assert_any_call(
        octocost.cost_and_usage_callback,
        5,
        use="https://api.octopus.energy/v1/electricity-meter-points/12345/meters/67890/consumption/",
        cost="https://api.octopus.energy/v1/products/AGILE-18-02-21/electricity-tariffs/E-1R-AGILE-18-02-21-H/standard-unit-rates/",
        date=datetime.date(2020, 12, 27),
    )
    run_in.assert_any_call(
        octocost.cost_and_usage_callback,
        6,
        use="https://api.octopus.energy/v1/electricity-meter-points/12345/meters/67890/consumption/",
        cost="https://api.octopus.energy/v1/products/FIX-12M-20-09-21/electricity-tariffs/E-1R-FIX-12M-20-09-21-H/standard-unit-rates/",
        date=datetime.date(2020, 12, 27),
    )


def test_callbacks_run_daily(hass_driver, octocost: OctoCost):
    run_daily = hass_driver.get_mock("run_daily")
    run_daily.assert_any_call(
        octocost.cost_and_usage_callback,
        datetime.time(0, 5),
        use="https://api.octopus.energy/v1/electricity-meter-points/12345/meters/67890/consumption/",
        cost="https://api.octopus.energy/v1/products/AGILE-18-02-21/electricity-tariffs/E-1R-AGILE-18-02-21-H/standard-unit-rates/",
        date=datetime.date(2020, 12, 27),
    )
    run_daily.assert_any_call(
        octocost.cost_and_usage_callback,
        datetime.time(0, 6),
        use="https://api.octopus.energy/v1/electricity-meter-points/12345/meters/67890/consumption/",
        cost="https://api.octopus.energy/v1/products/FIX-12M-20-09-21/electricity-tariffs/E-1R-FIX-12M-20-09-21-H/standard-unit-rates/",
        date=datetime.date(2020, 12, 27),
    )
    run_daily.assert_any_call(
        octocost.cost_and_usage_callback,
        datetime.time(0, 7),
        use="https://api.octopus.energy/v1/gas-meter-points/54321/meters/98765/consumption/",
        cost="https://api.octopus.energy/v1/products/FIX-12M-20-09-21/gas-tariffs/G-1R-FIX-12M-20-09-21-H/standard-unit-rates/",
        date=datetime.date(2020, 12, 27),
    )


@freeze_time("2021-02-01")
def test_callback_sets_electricity_states(hass_driver, octocost: OctoCost):
    set_state = hass_driver.get_mock("set_state")
    octocost.calculate_cost_and_usage = Mock(return_value=[7.7, 109.0])

    octocost.cost_and_usage_callback(
        {
            "use": octocost.consumption_url(),
            "cost": octocost.tariff_url(),
            "date": datetime.date(2020, 12, 27),
        }
    )

    set_state.assert_any_call(
        "sensor.octopus_yearly_usage",
        state=7.7,
        attributes={"unit_of_measurement": "kWh", "icon": "mdi:flash"},
    )
    set_state.assert_any_call(
        "sensor.octopus_yearly_cost",
        state=1.09,
        attributes={"unit_of_measurement": "£", "icon": "mdi:cash"},
    )
    set_state.assert_any_call(
        "sensor.octopus_monthly_usage",
        state=7.7,
        attributes={"unit_of_measurement": "kWh", "icon": "mdi:flash"},
    )
    set_state.assert_any_call(
        "sensor.octopus_monthly_cost",
        state=1.09,
        attributes={"unit_of_measurement": "£", "icon": "mdi:cash"},
    )
    set_state.assert_any_call(
        "sensor.octopus_daily_usage",
        state=7.7,
        attributes={"unit_of_measurement": "kWh", "icon": "mdi:flash"},
    )
    set_state.assert_any_call(
        "sensor.octopus_daily_cost",
        state=1.09,
        attributes={"unit_of_measurement": "£", "icon": "mdi:cash"},
    )


@freeze_time("2021-02-01")
def test_callback_sets_comparison_electricity_states(hass_driver, octocost: OctoCost):
    set_state = hass_driver.get_mock("set_state")
    octocost.calculate_cost_and_usage = Mock(return_value=[7.7, 109.0])

    octocost.cost_and_usage_callback(
        {
            "use": octocost.consumption_url(),
            "cost": octocost.tariff_url(
                energy="electricity", tariff=octocost.comparison_tariff
            ),
            "date": datetime.date(2020, 12, 27),
        }
    )

    set_state.assert_any_call(
        "sensor.octopus_yearly_usage",
        state=7.7,
        attributes={"unit_of_measurement": "kWh", "icon": "mdi:flash"},
    )
    set_state.assert_any_call(
        "sensor.octopus_monthly_usage",
        state=7.7,
        attributes={"unit_of_measurement": "kWh", "icon": "mdi:flash"},
    )
    set_state.assert_any_call(
        "sensor.octopus_comparison_yearly_cost",
        state=1.09,
        attributes={"unit_of_measurement": "£", "icon": "mdi:cash"},
    )
    set_state.assert_any_call(
        "sensor.octopus_daily_usage",
        state=7.7,
        attributes={"unit_of_measurement": "kWh", "icon": "mdi:flash"},
    )
    set_state.assert_any_call(
        "sensor.octopus_comparison_monthly_cost",
        state=1.09,
        attributes={"unit_of_measurement": "£", "icon": "mdi:cash"},
    )
    set_state.assert_any_call(
        "sensor.octopus_comparison_daily_cost",
        state=1.09,
        attributes={"unit_of_measurement": "£", "icon": "mdi:cash"},
    )


@freeze_time("2020-01-01")
def test_callback_sets_gas_states(hass_driver, octocost: OctoCost):
    set_state = hass_driver.get_mock("set_state")
    octocost.calculate_cost_and_usage = Mock(return_value=[7.7, 150.8])

    octocost.cost_and_usage_callback(
        {
            "use": octocost.consumption_url("gas"),
            "cost": octocost.tariff_url(energy="gas", tariff=octocost.gas_tariff),
            "date": datetime.date(2020, 12, 27),
        }
    )

    set_state.assert_any_call(
        "sensor.octopus_yearly_gas_usage",
        state=7.7,
        attributes={"unit_of_measurement": "m3", "icon": "mdi:fire"},
    )
    set_state.assert_any_call(
        "sensor.octopus_yearly_gas_cost",
        state=1.51,
        attributes={"unit_of_measurement": "£", "icon": "mdi:cash"},
    )
    set_state.assert_any_call(
        "sensor.octopus_monthly_gas_usage",
        state=7.7,
        attributes={"unit_of_measurement": "m3", "icon": "mdi:fire"},
    )
    set_state.assert_any_call(
        "sensor.octopus_monthly_gas_cost",
        state=1.51,
        attributes={"unit_of_measurement": "£", "icon": "mdi:cash"},
    )
