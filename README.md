# OctoCost

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs) [![codecov](https://codecov.io/gh/lildude/octocost/branch/main/graph/badge.svg?token=OEGCXZNPDX)](https://codecov.io/gh/lildude/octocost)

🚧 WIP: I'm in the process of improving this fork of the original source now it has been archived to keep it alive and to make it more useful and reliable.

Please consider signing up to Octopus Energy with my referral code: <https://share.octopus.energy/mauve-ash-375> to give you and me £50 credit in the mean time.

Want to motivate me to improve this quicker? [Sponsor me](https://github.com/sponsors/lildude) to work on it 😉 💖

---

## Summary

Octocost is an [AppDaemon](https://www.home-assistant.io/docs/ecosystem/appdaemon/) app for [Home Assistant](https://www.home-assistant.io/) which calculates the daily, monthly and yearly cost and usage of the Octopus Energy tariffs.

It creates and sets sensors for daily, monthly and yearly cost (£) and usage (kWh), up to and including yesterday:

```yaml
sensor.octopus_daily_cost
sensor.octopus_daily_usage
sensor.octopus_monthly_cost
sensor.octopus_monthly_usage
sensor.octopus_yearly_cost
sensor.octopus_yearly_usage
```

If can also pull monthly and yearly gas cost and usage, and have sensors for them set up, if the gas section is included in the yaml configuration:

```yaml
sensor.octopus_monthly_gas_cost
sensor.octopus_monthly_gas_usage
sensor.octopus_yearly_gas_cost
sensor.octopus_yearly_gas_usage
```

The data is updated once every two hours, although in reality the data Octopus Energy gets only seems to be updated once a day, so this is a compromise between trying to be up-to-date, and not hammering their servers, when the data doesn't update very frequently anyway.

## Installation

Use [HACS](https://github.com/custom-components/hacs) or [download the tarball](https://github.com/lildude/octocost/releases) and extract the `octocost` directory from inside the `apps` directory to your local `apps` directory, then add the configuration to enable the OctoCost module.

## Apps.yaml Configuration

```yaml
octocost:
  module: octocost 
  class: OctoCost 
  region: H
  mpan: <13 digit MPAN number>
  serial:  <Serial number>
  auth: <Octopus Energy API Key>
  start_date: 2020-02-23
  gas:
    mprn: <Gas MPRN number>
    gas_serial: <Gas meter serial number>
    gas_tariff: FIX-12M-20-02-12
    gas_start_date: 2020-02-23
```

The module and class sections need to remain as above, other sections should be changed as required. The whole gas section is optional and can be excluded if not required.

| Field          | Changeable | Example          |
| -----          | ---------- | -------          |
| Title          | Yes        | octocost         |
| module         | No         | octocost         |
| class          | No         | OctoCost         |
| region         | Yes        | H                |
| mpan           | Yes        | 2000012345678    |
| serial         | Yes        | 20L123456        |
| auth           | Yes        | sk_live_abcdefg  |
| start_date     | Yes        | 2020-02-23       |
| gas:           | Yes        |                  |
| mprn           | Yes        | 1234567890       |
| gas_serial     | Yes        | E1S12345678901   |
| gas_tariff     | Yes        | FIX-12M-20-02-12 |
| gas_start_date | Yes        | 2020-02-23       |

The `start_date` setting should be set to the date you started on the Agile Octopus tariff, not the date you joined Octopus Energy. It is used to adjust the start point if you joined within the current year or month, it should not be left blank if you joined earlier.
`region` is the region letter from the end of `E-1R-AGILE-18-02-21-H` which can be found on the [Octopus Energy developer dashboard](https://octopus.energy/dashboard/developer/) webpage in the Unit Rates section for your account.

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

![Example Lovelace UI Usage and Cost glance card](https://github.com/lildude/octocost/blob/main/LovelaceUsageCard.PNG)

---

## Changes

- Add support for fixed tariff for easy comparison
- Include standing charge in gas costing and fixed leccy
- Added unit testing from https://pypi.org/project/appdaemon-testing/
- Gas m3 is converted to kWh at assuming: the volume correction factor is 1.02264 and calorific value is 40 giving a formula of  X m3 * 11.1868 = Y kWh

## Limitations

- Only accounts for single-rate electicity on fixed rate plans


