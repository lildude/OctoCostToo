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
