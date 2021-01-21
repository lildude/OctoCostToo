import pytest
import requests

# Prevent accidental outgoing network requests - we should be mocking these
@pytest.fixture(autouse=True)
def no_http_requests(monkeypatch):
    def urlopen_mock(self, method, url, *args, **kwargs):
        raise RuntimeError(
            f"The test was about to {method} {self.scheme}://{self.host}{url}"
        )

    monkeypatch.setattr(
        "urllib3.connectionpool.HTTPConnectionPool.urlopen", urlopen_mock
    )

@pytest.fixture(name="mock_elec_meter_points")
def fixture_mock_elec_meter_points(requests_mock):
  """
  Mock response for getting meter points used to determine the region
  """
  requests_mock.get(
    "https://api.octopus.energy/v1/electricity-meter-points/12345",
    text= open("tests/fixtures/elec-meter-points.json", "r").read()
  )

@pytest.fixture(name="mock_elec_consumption_one_day")
def fixture_mock_elec_consumption_one_day(requests_mock):
  """
  Mock response for a single day's electricity usage
  """
  requests_mock.get(
    "https://api.octopus.energy/v1/electricity-meter-points/12345/meters/67890/consumption/?order_by=period&period_from=2021-01-18T00:00:00Z&period_to=2021-01-18T23:59:59Z&page_size=47",
    text= open("tests/fixtures/elec-one-day-usage.json", "r").read()
  )

@pytest.fixture(name="mock_elec_agile_cost_one_day")
def fixture_mock_elec_agile_cost_one_day(requests_mock):
  """
  Mock response for a single day's Agile electricity prices
  """
  requests_mock.get(
    "https://api.octopus.energy/v1/products/AGILE-18-02-21/electricity-tariffs/E-1R-AGILE-18-02-21-H/standard-unit-rates/?period_from=2021-01-18T00:00:00Z&period_to=2021-01-18T23:59:59Z",
    text= open("tests/fixtures/agile-cost-one-day.json", "r").read()
  )

@pytest.fixture(name="mock_elec_fixed_rates")
def fixture_mock_elec_fixed_rates(requests_mock):
  """
  Mock response for electricity standard unit rates & standing charge
  """
  requests_mock.get(
    "https://api.octopus.energy/v1/products/FIX-12M-20-09-21/electricity-tariffs/E-1R-FIX-12M-20-09-21-H/standard-unit-rates/?period_from=2021-01-18T00:00:00Z&period_to=2021-01-18T23:59:59Z",
    text= open("tests/fixtures/elec-standard-rate.json", "r").read()
  )
  requests_mock.get(
    "https://api.octopus.energy/v1/products/FIX-12M-20-09-21/electricity-tariffs/E-1R-FIX-12M-20-09-21-H/standing-charges/?period_from=2021-01-18T00:00:00Z&period_to=2021-01-18T23:59:59Z",
    text= open("tests/fixtures/elec-standing-charges.json", "r").read()
  )

@pytest.fixture(name="mock_gas_consumption_one_day")
def fixture_mock_gas_consumption_one_day(requests_mock):
  """
  Mock response for a single day's gas usage
  """
  requests_mock.get(
    "https://api.octopus.energy/v1/gas-meter-points/54321/meters/98765/consumption/?order_by=period&period_from=2021-01-18T00:00:00Z&period_to=2021-01-18T23:59:59Z&page_size=47",
    text= open("tests/fixtures/elec-one-day-usage.json", "r").read()
  )

@pytest.fixture(name="mock_gas_rates")
def fixture_mock_gas_rates(requests_mock):
  """
  Mock response for gas standard unit rates & standing charge
  """
  requests_mock.get(
    "https://api.octopus.energy/v1/products/FIX-12M-20-09-21/gas-tariffs/G-1R-FIX-12M-20-09-21-H/standard-unit-rates/?period_from=2021-01-18T00:00:00Z&period_to=2021-01-18T23:59:59Z",
    text= open("tests/fixtures/gas-standard-rate.json", "r").read()
  )
  requests_mock.get(
    "https://api.octopus.energy/v1/products/FIX-12M-20-09-21/gas-tariffs/G-1R-FIX-12M-20-09-21-H/standing-charges/?period_from=2021-01-18T00:00:00Z&period_to=2021-01-18T23:59:59Z",
    text= open("tests/fixtures/gas-standing-charges.json", "r").read()
  )

@pytest.fixture(name="mock_elec_consumption_five_days")
def fixture_mock_elec_consumption_five_days(requests_mock):
  """
  Mock responses for five days' electricity usage
  """
  requests_mock.get(
    "https://api.octopus.energy/v1/electricity-meter-points/12345/meters/67890/consumption/?order_by=period&period_from=2021-01-14T00:00:00Z&period_to=2021-01-18T23:59:59Z&page_size=239",
    text= open("tests/fixtures/elec-five-day-usage.json", "r").read()
  )
  requests_mock.get(
    "https://api.octopus.energy/v1/products/FIX-12M-20-09-21/electricity-tariffs/E-1R-FIX-12M-20-09-21-H/standard-unit-rates/?period_from=2021-01-14T00:00:00Z&period_to=2021-01-18T23:59:59Z",
    text= open("tests/fixtures/elec-standard-rate.json", "r").read()
  )
  requests_mock.get(
    "https://api.octopus.energy/v1/products/FIX-12M-20-09-21/electricity-tariffs/E-1R-FIX-12M-20-09-21-H/standing-charges/?period_from=2021-01-14T00:00:00Z&period_to=2021-01-18T23:59:59Z",
    text= open("tests/fixtures/elec-standing-charges.json", "r").read()
  )