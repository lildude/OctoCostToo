# OctoCostToo

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs) [![codecov](https://codecov.io/gh/lildude/OctoCostToo/branch/main/graph/badge.svg?token=OEGCXZNPDX)](https://codecov.io/gh/lildude/OctoCostToo)

Please consider signing up to Octopus Energy with my referral code: <https://share.octopus.energy/mauve-ash-375> to give you and me £50 credit in the mean time.

Want to motivate me to improve this quicker? [Sponsor me](https://github.com/sponsors/lildude) to work on it 😉 💖

---

## Summary

OctoCostToo is an [AppDaemon](https://www.home-assistant.io/docs/ecosystem/appdaemon/) app for [Home Assistant](https://www.home-assistant.io/) which calculates the daily, monthly and yearly cost and usage of the Octopus Energy tariffs.

By default OctoCostToo only gathers usage and cost information for the current (as of Jan 2021) Agile tariff: `AGILE-18-02-21` but can be configured to gather usage and cost information for an another electricity tariff, giving you the opportunity to compare your current tariff to the Agile tariff.

Usage and cost information can also be gathered for a gas tariff.

OctoCostToo creates and sets sensors for daily, monthly and yearly cost (£) and usage (kWh), up to and including yesterday:

```yaml
sensor.octopus_daily_cost
sensor.octopus_daily_usage
sensor.octopus_monthly_cost
sensor.octopus_monthly_usage
sensor.octopus_yearly_cost
sensor.octopus_yearly_usage
```

If a comparison electricity tariff is configured, OctoCostToo will also create the following sensors:

```yaml
sensor.octopus_comparison_daily_cost
sensor.octopus_comparison_monthly_cost
sensor.octopus_comparison_yearly_cost
```

If the gas section is configured, OctoCostToo will also create the following sensors:

```yaml
sensor.octopus_monthly_gas_cost
sensor.octopus_monthly_gas_usage
sensor.octopus_yearly_gas_cost
sensor.octopus_yearly_gas_usage
```

The data is updated once every two hours, although in reality the data Octopus Energy gets only seems to be updated once a day, so this is a compromise between trying to be up-to-date, and not hammering their servers, when the data doesn't update very frequently anyway.

## Installation

Use [HACS](https://github.com/custom-components/hacs) or [download the tarball](https://github.com/lildude/OctoCostToo/releases) and extract the `OctoCostToo` directory from inside the `apps` directory to your local `apps` directory, then add the configuration to enable the OctoCostToo module.

## Apps.yaml Configuration

```yaml
OctoCostToo:
  module: octocosttoo 
  class: OctoCostToo 
  region: H
  mpan: <13 digit MPAN number>
  serial:  <Serial number>
  auth: <Octopus Energy API Key>
  start_date: 2020-02-23
  comparison_tariff: FIX-12M-20-02-12
  gas:
    mprn: <Gas MPRN number>
    gas_serial: <Gas meter serial number>
    gas_tariff: FIX-12M-20-02-12
    gas_start_date: 2020-02-23
```

The module and class sections need to remain as above, other sections should be changed as required. The whole gas section is optional and can be excluded if not required.

| Field             | Changeable | Example          |
| -----             | ---------- | -------          |
| Title             | Yes        | octocosttoo      |
| module            | No         | octocosttoo      |
| class             | No         | OctoCostToo      |
| region            | Yes        | H                |
| mpan              | Yes        | 2000012345678    |
| serial            | Yes        | 20L123456        |
| auth              | Yes        | sk_live_abcdefg  |
| start_date        | Yes        | 2020-02-23       |
| comparison_tariff | Yes        | FIX-12M-20-02-12 |
| gas:              | Yes        |                  |
| mprn              | Yes        | 1234567890       |
| gas_serial        | Yes        | E1S12345678901   |
| gas_tariff        | Yes        | FIX-12M-20-02-12 |
| gas_start_date    | Yes        | 2020-02-23       |

The `start_date` setting should be set to the date you started on the Agile Octopus tariff, not the date you joined Octopus Energy. It is used to adjust the start point if you joined within the current year or month, it should not be left blank if you joined earlier.
`region` is the region letter from the end of `E-1R-AGILE-18-02-21-H` which can be found on the [Octopus Energy developer dashboard](https://octopus.energy/dashboard/developer/) webpage in the Unit Rates section for your account.

## Limitations

- OctoCostToo only caters for single-rate comparison electricity and gas tariffs.

### Lovelace UI Cards

Once the sensors are created, they can be displayed as cards within the Lovelace UI. For example:

```yaml
- entities:
    - entity: sensor.octopus_yearly_usage
      icon: 'mdi:flash'
      name: Yearly Usage (kWh)
    - entity: sensor.octopus_yearly_cost
      icon: 'mdi:cash'
      name: Yearly Cost (£)
    - entity: sensor.octopus_monthly_usage
      icon: 'mdi:flash'
      name: Monthly Usage (kWh)
    - entity: sensor.octopus_monthly_cost
      icon: 'mdi:cash'
      name: Monthly Cost (£)
  show_icon: true
  title: Octopus Usage / Cost
  type: glance
```

![Example Lovelace UI Usage and Cost glance card](https://github.com/lildude/OctoCostToo/blob/main/LovelaceUsageCard.PNG)

## Contributing

Want to contribute to this project? Great! Fork the repo, make your changes (don't forget to add tests 😉) and submit a pull request.

You can install the necessary dependencies and run the tests locally as follows:

```console
$ python -m pip install --upgrade pip
$ pip install -r requirements-test.txt
$ pytest
```

## Credit

OctoCostToo is a fork of the original [octocost](https://github.com/badguy99/octocost).

**NOTE:** The configuration for OctoCostToo is not compatible with the original.
