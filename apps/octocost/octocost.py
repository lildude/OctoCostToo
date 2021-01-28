import datetime
import json
import re

import dateutil.parser
import pytz
import requests
from appdaemon.plugins.hass import hassapi as hass

BASEURL = "https://api.octopus.energy/v1"


class OctoCost(hass.Hass):
    def initialize(self):
        self.auth = self.args["auth"]
        self.mpan = self.args["mpan"]
        self.serial = self.args["serial"]
        # We probably shouldn't be making API calls when initialising
        # self.region = self.args.get("region", self.find_region(self.mpan))
        self.region = self.args["region"].upper()
        self.elec_start_date = datetime.date.fromisoformat(str(self.args["start_date"]))
        self.comparison_tariff = self.args.get("comparison_tariff", None)
        self.gas = self.args.get("gas", None)
        if self.gas:
            self.gas_tariff = self.gas.get("gas_tariff", None)
            self.mprn = self.gas.get("mprn", None)
            self.gas_serial = self.gas.get("gas_serial", None)
            self.gas_start_date = datetime.date.fromisoformat(
                str(self.gas.get("gas_start_date"))
            )

        self.run_in(
            self.cost_and_usage_callback,
            5,
            use=self.consumption_url(),
            cost=self.tariff_url(),
            date=self.elec_start_date,
        )

        if self.comparison_tariff:
            self.run_in(
                self.cost_and_usage_callback,
                6,
                use=self.consumption_url(),
                cost=self.tariff_url(
                    energy="electricity", tariff=self.comparison_tariff
                ),
                date=self.elec_start_date,
            )

        if self.gas:
            self.run_in(
                self.cost_and_usage_callback,
                65,
                use=self.consumption_url("gas"),
                cost=self.tariff_url(energy="gas", tariff=self.gas_tariff),
                date=self.gas_start_date,
            )

        for hour in [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]:
            self.run_daily(
                self.cost_and_usage_callback,
                datetime.time(hour, 5, 0),
                use=self.consumption_url(),
                cost=self.tariff_url(),
                date=self.elec_start_date,
            )

            self.run_daily(
                self.cost_and_usage_callback,
                datetime.time(hour, 6, 0),
                use=self.consumption_url(),
                cost=self.tariff_url(
                    energy="electricity", tariff=self.comparison_tariff
                ),
                date=self.elec_start_date,
            )

            if self.gas:
                self.run_daily(
                    self.cost_and_usage_callback,
                    datetime.time(hour, 7, 0),
                    use=self.consumption_url("gas"),
                    cost=self.tariff_url(energy="gas", tariff=self.gas_tariff),
                    date=self.gas_start_date,
                )

    @classmethod
    def find_region(cls, mpan):
        url = BASEURL + "/electricity-meter-points/" + str(mpan)
        meter_details = requests.get(url)
        json_meter_details = json.loads(meter_details.text)
        region = str(json_meter_details["gsp"][-1])
        return region

    def tariff_url(self, **kwargs):
        energy = kwargs.get("energy", "electricity")
        tariff = kwargs.get("tariff", "AGILE-18-02-21")
        units = kwargs.get("units", "standard-unit-rates")
        url = f"{BASEURL}/products/{tariff}/{energy}-tariffs/{energy[0].upper()}-1R-{tariff}-{self.region}/{units}/"
        return url

    def consumption_url(self, energy="electricity"):
        meter_point = self.mprn if energy == "gas" else self.mpan
        serial = self.gas_serial if energy == "gas" else self.serial
        url = f"{BASEURL}/{energy}-meter-points/{meter_point}/meters/{serial}/consumption/"
        return url

    def cost_and_usage_callback(self, kwargs):
        self.use_url = kwargs.get("use")
        self.cost_url = kwargs.get("cost")
        self.start_date = kwargs.get("date")
        today = datetime.date.today()
        self.gas = True if "gas" in self.use_url else False
        self.yesterday = today - datetime.timedelta(days=1)
        start_year = datetime.date(today.year, 1, 1)
        start_month = datetime.date(today.year, today.month, 1)
        start_day = self.yesterday

        if today == start_month:
            if today.month == 1:
                start_month = datetime.date(today.year - 1, 12, 1)
            else:
                start_month = datetime.date(today.year, today.month - 1, 1)
        if today == start_year:
            start_year = datetime.date(today.year - 1, 1, 1)

        if self.start_date > start_month:
            start_month = self.start_date

        if self.start_date > start_year:
            start_year = self.start_date

        energy = "gas" if self.gas else "electricity"
        tariff = re.search(r"products/([^/]+)/", self.cost_url).group(1)
        cost_usage = {}
        for period, start in {
            "daily": start_day,
            "monthly": start_month,
            "yearly": start_year,
        }.items():
            # Skip API calls etc if gas and daily as this info isn't available (yet?)
            if self.gas and period == "daily":
                continue

            # Get the usage and calculate the cost
            (
                cost_usage[f"{period}_usage"],
                cost_usage[f"{period}_cost"],
            ) = self.calculate_cost_and_usage(start=start)
            # Log results for debugging
            self.log(
                "{} {} {} usage: {}".format(
                    period.capitalize(), tariff, energy, cost_usage[f"{period}_usage"]
                ),
                level="INFO",
            )
            self.log(
                "{} {} {} cost: {} p".format(
                    period.capitalize(), tariff, energy, cost_usage[f"{period}_cost"]
                ),
                level="INFO",
            )
            # Set the states
            if self.gas:
                self.set_state(
                    f"sensor.octopus_{period}_gas_usage",
                    state=round(cost_usage[f"{period}_usage"], 2),
                    attributes={"unit_of_measurement": "m3", "icon": "mdi:fire"},
                )
                self.set_state(
                    f"sensor.octopus_{period}_gas_cost",
                    state=round(cost_usage[f"{period}_cost"] / 100, 2),
                    attributes={"unit_of_measurement": "£", "icon": "mdi:cash"},
                )
            else:
                self.set_state(
                    f"sensor.octopus_{period}_usage",
                    state=round(cost_usage[f"{period}_usage"], 2),
                    attributes={"unit_of_measurement": "kWh", "icon": "mdi:flash"},
                )
                if "AGILE" in tariff:
                    self.set_state(
                        f"sensor.octopus_{period}_cost",
                        state=round(cost_usage[f"{period}_cost"] / 100, 2),
                        attributes={"unit_of_measurement": "£", "icon": "mdi:cash"},
                    )
                else:
                    self.set_state(
                        f"sensor.octopus_comparison_{period}_cost",
                        state=round(cost_usage[f"{period}_cost"] / 100, 2),
                        attributes={"unit_of_measurement": "£", "icon": "mdi:cash"},
                    )

    def calculate_count(self, start):
        numberdays = self.yesterday - start
        numberdays = numberdays.days
        return ((numberdays + 1) * 48) - 1

    def calculate_cost_and_usage(self, start):
        usage = 0
        price = 0
        std_chg = 0
        cost = []
        utc = pytz.timezone("UTC")
        expected_count = self.calculate_count(start=start)
        self.log(f"period_from: {start.isoformat()}T00:00:00Z", level="DEBUG")
        self.log(f"period_to: {self.yesterday.isoformat()}T23:59:59Z", level="DEBUG")

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

        if consump_resp.status_code != 200:
            self.log(
                f"Error {consump_resp.status_code} getting consumption data: {consump_resp.text}",
                level="ERROR",
            )
            return
        if cost_resp.status_code != 200:
            self.log(
                f"Error {cost_resp.status_code} getting cost data: {cost_resp.text}",
                level="ERROR",
            )
            return
        # If cost_url contains `-1R-FIX-`, assume it's a fixed rate and get the standing charge too.
        # Applies to fixed rate gas and fixed rate electricity
        if "-1R-FIX-" in self.cost_url:
            if "gas-tariffs" in self.cost_url:
                std_chg_url = self.tariff_url(
                    energy="gas", tariff=self.gas_tariff, units="standing-charges"
                )
            else:
                std_chg_url = self.tariff_url(
                    tariff=self.gas_tariff, units="standing-charges"
                )

            standing_chg_resp = requests.get(
                url=std_chg_url
                + "?period_from="
                + start.isoformat()
                + "T00:00:00Z&period_to="
                + self.yesterday.isoformat()
                + "T23:59:59Z"
            )
            if standing_chg_resp.status_code != 200:
                self.log(
                    "Error {} getting standing charge data: {}".format(
                        standing_chg_resp.status_code, standing_chg_resp.text
                    ),
                    level="ERROR",
                )
            else:
                standing_chg_json = json.loads(standing_chg_resp.text)
                std_chg = standing_chg_json["results"][0]["value_inc_vat"] * (
                    (self.yesterday - start).days + 1
                )

        consump_json = json.loads(consump_resp.text)
        cost_json = json.loads(cost_resp.text)

        results = consump_json["results"]

        while cost_json["next"]:
            cost.extend(cost_json["results"])
            cost_resp = requests.get(url=cost_json["next"])
            cost_json = json.loads(cost_resp.text)

        cost.extend(cost_json["results"])
        cost.reverse()

        for period in results:
            current_index = results.index(period)
            usage = usage + (results[current_index]["consumption"])
            if "-1R-FIX-" in self.cost_url:
                # Only dealing with gas price which doesn't vary at the moment
                if cost_json["count"] == 1:
                    cost = cost_json["results"][0]["value_inc_vat"]
                    kwh = results[current_index]["consumption"]
                    # Convert consumption from m3 to kWh for gas
                    if "gas-tariffs" in self.cost_url:
                        kwh = kwh * 11.1868

                    price = price + (cost * kwh)
                else:
                    self.log("Error: can only process fixed price gas", level="ERROR")
                    price = 0
            else:
                if (results[current_index]["interval_start"]) != (
                    cost[current_index]["valid_from"]
                ):
                    # Daylight Savings?
                    consumption_date = results[current_index]["interval_start"]
                    if consumption_date.endswith("+01:00"):
                        date_time = dateutil.parser.parse(consumption_date)
                        utc_datetime = date_time.astimezone(utc)
                        utc_iso = utc_datetime.isoformat().replace("+00:00", "Z")
                        if utc_iso == (cost[current_index]["valid_from"]):
                            (results[current_index]["interval_start"]) = utc_iso
                        else:
                            self.log(
                                "UTC Unmatched consumption {}".format(
                                    results[current_index]["interval_start"]
                                )
                                + " / cost {}".format(
                                    cost[current_index]["valid_from"]
                                ),
                                level="ERROR",
                            )
                    else:
                        self.log(
                            "Unmatched consumption {}".format(
                                results[current_index]["interval_start"]
                            )
                            + " / cost {}".format(cost[current_index]["valid_from"]),
                            level="ERROR",
                        )
                price = price + (
                    (cost[current_index]["value_inc_vat"])
                    * (results[current_index]["consumption"])
                )

        # We round because floating point arithmatic leads to some crazy looking figures
        return round(usage, 3), round((price + std_chg), 4)
