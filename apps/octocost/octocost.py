import datetime
import json

import dateutil.parser
import pytz
import requests
from appdaemon.plugins.hass import hassapi as hass


class OctoCost(hass.Hass):
    def initialize(self):
        self.auth = self.args["auth"]
        self.mpan = self.args["mpan"]
        self.serial = self.args["serial"]
        # We probably shouldn't be making API calls when initialising
        #self.region = self.args.get("region", self.find_region(self.mpan))
        self.region = self.args["region"].upper()
        self.elec_start_date = datetime.date.fromisoformat(str(self.args["start_date"]))
        self.gas = self.args.get("gas", None)
        if self.gas:
            self.gas_tariff = self.gas.get("gas_tariff", None)
            self.mprn = self.gas.get("mprn", None)
            self.gas_serial = self.gas.get("gas_serial", None)
            self.gas_start_date = datetime.date.fromisoformat(str(self.gas.get("gas_start_date")))

        self.elec_consumption_url = (
            "https://api.octopus.energy/"
            + "v1/electricity-meter-points/"
            + str(self.mpan)
            + "/meters/"
            + str(self.serial)
            + "/consumption/"
        )
        self.agile_cost_url = (
            "https://api.octopus.energy/v1/products/"
            + "AGILE-18-02-21/electricity-tariffs/E-1R-AGILE-18-02-21-"
            + str(self.region)
            + "/standard-unit-rates/"
        )
        self.gas_consumption_url = (
            "https://api.octopus.energy/"
            + "v1/gas-meter-points/"
            + str(self.mprn)
            + "/meters/"
            + str(self.gas_serial)
            + "/consumption/"
        )
        self.gas_cost_url = (
            "https://api.octopus.energy/v1/products/"
            + self.gas_tariff
            + "/gas-tariffs/G-1R-"
            + self.gas_tariff
            + "-"
            + str(self.region)
            + "/standard-unit-rates/"
        )
        self.gas_std_chg_url = (
            "https://api.octopus.energy/v1/products/"
            + self.gas_tariff
            + "/gas-tariffs/G-1R-"
            + self.gas_tariff
            + "-"
            + str(self.region)
            + "/standing-charges/"
        )
        # Assumes gas and comparison leccy are on same tariff
        self.fixed_cost_url = (
            "https://api.octopus.energy/v1/products/"
            + self.gas_tariff
            + "/electricity-tariffs/E-1R-"
            + self.gas_tariff
            + "-"
            + str(self.region)
            + "/standard-unit-rates/"
        )
        self.fixed_std_chg_url = (
            "https://api.octopus.energy/v1/products/"
            + self.gas_tariff
            + "/electricity-tariffs/E-1R-"
            + self.gas_tariff
            + "-"
            + str(self.region)
            + "/standard-charges/"
        )

        self.run_in(
            self.cost_and_usage_callback,
            5,
            use=self.elec_consumption_url,
            cost=self.agile_cost_url,
            date=self.elec_start_date,
        )
        if self.gas:
            self.run_in(
                self.cost_and_usage_callback,
                65,
                use=self.gas_consumption_url,
                cost=self.gas_cost_url,
                date=self.gas_start_date,
                gas=True,
            )

        for hour in [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]:
            self.run_daily(
                self.cost_and_usage_callback,
                datetime.time(hour, 5, 0),
                use=self.elec_consumption_url,
                cost=self.agile_cost_url,
                date=self.elec_start_date,
            )

            if self.gas:
                self.run_daily(
                    self.cost_and_usage_callback,
                    datetime.time(hour, 7, 0),
                    use=self.gas_consumption_url,
                    cost=self.gas_cost_url,
                    date=self.gas_start_date,
                    gas=True,
                    gas_price=self.gas_std_chg_url,
                )

    @classmethod
    def find_region(cls, mpan):
        url = "https://api.octopus.energy/v1/electricity-meter-points/" + str(mpan)
        meter_details = requests.get(url)
        json_meter_details = json.loads(meter_details.text)
        region = str(json_meter_details["gsp"][-1])
        return region

    def cost_and_usage_callback(self, **kwargs):
        self.use_url = kwargs.get("use")
        self.cost_url = kwargs.get("cost")
        self.startdate = kwargs.get("date")
        self.gas = kwargs.get("gas", False)
        #if self.gas:
        #    self.gas_price_url = kwargs.get("gas_price")
        today = datetime.date.today()
        self.yesterday = today - datetime.timedelta(days=1)
        startyear = datetime.date(today.year, 1, 1)
        startmonth = datetime.date(today.year, today.month, 1)
        startday = self.yesterday

        if today == startmonth:
            if today.month == 1:
                startmonth = datetime.date(today.year - 1, 12, 1)
            else:
                startmonth = datetime.date(today.year, today.month - 1, 1)
        if today == startyear:
            startyear = datetime.date(today.year - 1, 1, 1)

        if self.startdate > startmonth:
            startmonth = self.startdate

        if self.startdate > startyear:
            startyear = self.startdate

        dayusage, daycost = self.calculate_cost_and_usage(start=startday)
        self.log("Yesterday usage: {}".format(dayusage), level="INFO")
        self.log("Yesterday cost: {} p".format(daycost), level="INFO")

        monthlyusage, monthlycost = self.calculate_cost_and_usage(start=startmonth)
        self.log("Total monthly usage: {}".format(monthlyusage), level="INFO")
        self.log("Total monthly cost: {} p".format(monthlycost), level="INFO")

        yearlyusage, yearlycost = self.calculate_cost_and_usage(start=startyear)
        self.log("Total yearly usage: {}".format(yearlyusage), level="INFO")
        self.log("Total yearly cost: {} p".format(yearlycost), level="INFO")

        if not self.gas:
            self.set_state(
                "sensor.octopus_yearly_usage",
                state=round(yearlyusage, 2),
                attributes={"unit_of_measurement": "kWh", "icon": "mdi:flash"},
            )
            self.set_state(
                "sensor.octopus_yearly_cost",
                state=round(yearlycost / 100, 2),
                attributes={"unit_of_measurement": "£", "icon": "mdi:cash"},
            )
            self.set_state(
                "sensor.octopus_monthly_usage",
                state=round(monthlyusage, 2),
                attributes={"unit_of_measurement": "kWh", "icon": "mdi:flash"},
            )
            self.set_state(
                "sensor.octopus_monthly_cost",
                state=round(monthlycost / 100, 2),
                attributes={"unit_of_measurement": "£", "icon": "mdi:cash"},
            )
            self.set_state(
                "sensor.octopus_day_usage",
                state=round(dayusage, 2),
                attributes={"unit_of_measurement": "kWh", "icon": "mdi:flash"},
            )
            self.set_state(
                "sensor.octopus_day_cost",
                state=round(daycost / 100, 2),
                attributes={"unit_of_measurement": "£", "icon": "mdi:cash"},
            )
        else:
            self.set_state(
                "sensor.octopus_yearly_gas_usage",
                state=round(yearlyusage, 2),
                attributes={"unit_of_measurement": "m3", "icon": "mdi:fire"},
            )
            self.set_state(
                "sensor.octopus_yearly_gas_cost",
                state=round(yearlycost / 100, 2),
                attributes={"unit_of_measurement": "£", "icon": "mdi:cash"},
            )
            self.set_state(
                "sensor.octopus_monthly_gas_usage",
                state=round(monthlyusage, 2),
                attributes={"unit_of_measurement": "m3", "icon": "mdi:fire"},
            )
            self.set_state(
                "sensor.octopus_monthly_gas_cost",
                state=round(monthlycost / 100, 2),
                attributes={"unit_of_measurement": "£", "icon": "mdi:cash"},
            )

    def calculate_count(self, start):
        numberdays = self.yesterday - start
        numberdays = numberdays.days
        return ((numberdays + 1) * 48) - 1

    # TODO: this doesn't include standing charges
    def calculate_cost_and_usage(self, start):
        expected_count = self.calculate_count(start=start)
        self.log("period_from: {}T00:00:00Z".format(start.isoformat()), level="DEBUG")
        self.log("period_to: {}T23:59:59Z".format(self.yesterday.isoformat()), level="DEBUG")

        consump_resp = requests.get(
            url=self.use_url
            + "?order_by=period&period_from="
            + start.isoformat()
            + "T00:00:00Z&period_to="
            + self.yesterday.isoformat()
            + "T23:59:59Z&page_size="
            + str(expected_count),
            auth=(self.auth, ""),
        )

        cost_resp = requests.get(
            url=self.cost_url
            + "?period_from="
            + start.isoformat()
            + "T00:00:00Z&period_to="
            + self.yesterday.isoformat()
            + "T23:59:59Z"
        )

        #rgasprice = requests.get(
        #    url=self.gas_price_url
        #    + "?period_from="
        #    + start.isoformat()
        #    + "T00:00:00Z&period_to="
        #    + self.yesterday.isoformat()
        #    + "T23:59:59Z"
        #)

        if consump_resp.status_code != 200:
            self.log(
                "Error {} getting consumption data: {}".format(
                    consump_resp.status_code, consump_resp.text
                ),
                level="ERROR",
            )
        if cost_resp.status_code != 200:
            self.log(
                "Error {} getting cost data: {}".format(cost_resp.status_code, cost_resp.text),
                level="ERROR",
            )

        consump_json = json.loads(consump_resp.text)
        cost_json = json.loads(cost_resp.text)

        usage = 0
        price = 0
        cost = []
        utc = pytz.timezone("UTC")

        results = consump_json[u"results"]

        #if rgasprice.status_code == 200:
        #    price = results[0][u"value_inc_vat"]

        while cost_json[u"next"]:
            cost.extend(cost_json[u"results"])
            cost_resp = requests.get(url=cost_json[u"next"])
            cost_json = json.loads(cost_resp.text)

        cost.extend(cost_json[u"results"])
        cost.reverse()

        for period in results:
            curridx = results.index(period)
            usage = usage + (results[curridx][u"consumption"])
            if not self.gas:
                if (results[curridx][u"interval_start"]) != (
                    cost[curridx][u"valid_from"]
                ):
                    # Daylight Savings?
                    consumption_date = results[curridx][u"interval_start"]
                    if consumption_date.endswith("+01:00"):
                        date_time = dateutil.parser.parse(consumption_date)
                        utc_datetime = date_time.astimezone(utc)
                        utc_iso = utc_datetime.isoformat().replace("+00:00", "Z")
                        if utc_iso == (cost[curridx][u"valid_from"]):
                            (results[curridx][u"interval_start"]) = utc_iso
                        else:
                            self.log(
                                "UTC Unmatched consumption {}".format(
                                    results[curridx][u"interval_start"]
                                )
                                + " / cost {}".format(cost[curridx][u"valid_from"]),
                                level="ERROR",
                            )
                    else:
                        self.log(
                            "Unmatched consumption {}".format(
                                results[curridx][u"interval_start"]
                            )
                            + " / cost {}".format(cost[curridx][u"valid_from"]),
                            level="ERROR",
                        )
                price = price + (
                    (cost[curridx][u"value_inc_vat"])
                    * (results[curridx][u"consumption"])
                )
            else:
                # Only dealing with gas price which doesn't vary at the moment
                if cost_json["count"] == 1:
                    cost = cost_json["results"][0][u"value_inc_vat"]
                    price = price + (cost * results[curridx][u"consumption"])
                else:
                    self.log("Error: can only process fixed price gas", level="ERROR")
                    price = 0

        return usage, price
