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