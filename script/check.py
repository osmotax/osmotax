import argparse
import base64
import json
import os.path as osp
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests
from dateutil.parser import parse

from script.utils.bech32 import bech32encode


def get_pool_incentives(args):
    r = requests.get(
        f"{args.server}/osmosis/mint/v1beta1/params",
        headers={
            "accept": "application/json",
        },
    )
    assert r.status_code == 200
    r = json.loads(r.text)
    pool_incentives = float(r["params"]["distribution_proportions"]["pool_incentives"])
    return pool_incentives


def get_epoch_provisions(args):
    r = requests.get(
        f"{args.server}/osmosis/mint/v1beta1/epoch_provisions",
        headers={
            "accept": "application/json",
        },
    )
    assert r.status_code == 200
    epoch_provisions = float(json.loads(r.text)["epoch_provisions"])
    return epoch_provisions


def get_daily_distribution(epoch, timestamp):
    fn = osp.join("data", "{0:04}".format(epoch) + ".json")
    with open(fn, "r") as f:
        data = json.load(f)

    print(f"[log] epoch {epoch}")

    rows = defaultdict(lambda: {"amount": [], "osmo": []})

    for key in ["end_block_events", "begin_block_events"]:
        if key in data["result"] and data["result"][key] is not None:
            for event in data["result"][key]:
                if event["type"] == "distribution":
                    if any(
                        [
                            attr
                            for attr in event["attributes"]
                            if attr["key"] == "Z2F1Z2VfaWQ="
                        ]
                    ):
                        address = None
                        amount = None
                        osmo = 0

                        attributes = event["attributes"]
                        for attr in attributes:
                            if attr["key"] == "cmVjZWl2ZXI=":  # receiver
                                try:
                                    address = str(
                                        base64.b64decode(attr["value"]), "utf-8"
                                    )
                                except UnicodeDecodeError:
                                    address = bech32encode(
                                        "osmo",
                                        [v for v in base64.b64decode(attr["value"])],
                                    )
                            elif attr["key"] == "YW1vdW50":  # amount
                                amount = str(base64.b64decode(attr["value"]), "utf-8")
                                for reward in [o for o in amount.split(",")]:
                                    if "uosmo" in reward:
                                        osmo = int(reward.replace("uosmo", ""))

                        if address and timestamp and amount:
                            rows[address]["amount"].append(amount)
                            rows[address]["osmo"].append(osmo)
                        else:
                            assert False

    total_amount = 0
    for address, value in rows.items():
        total_amount += sum(value["osmo"])
    return total_amount


def check_distribution(args, epoch, height, timestamp):
    epoch_provisions = get_epoch_provisions(args)

    rheight = int(round(height / 500.0) * 500.0)
    r = requests.get(
        f"{args.server}/osmosis/pool-incentives/v1beta1/distr_info",
        headers={"accept": "application/json", "x-cosmos-block-height": str(rheight)},
    )
    assert r.status_code == 200
    r = json.loads(r.text)
    distr_info = r["distr_info"]
    total_weight = int(distr_info["total_weight"])
    exclude_weight = 0
    for r in distr_info["records"]:
        if r["gauge_id"] == "0":
            exclude_weight = int(r["weight"])

    pool_incentives = get_pool_incentives(args)
    real_error = pool_incentives * ((total_weight - exclude_weight) / total_weight)

    total_osmo = get_daily_distribution(epoch, timestamp)
    expected_error = total_osmo / epoch_provisions

    print(
        f"[Error] {timestamp} in ",
        "{:.20f}".format(abs((real_error - expected_error) * 100)),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--server", type=str, default="http://localhost:1317")
    parser.add_argument("--metadata", type=str, default="epoch_height_price.csv")
    parser.add_argument("--num", type=int, default=3)
    parser.add_argument(
        "--last_date", type=lambda d: datetime.strptime(d, "%Y-%m-%d"), required=True
    )
    args = parser.parse_args()

    df = pd.read_csv(args.metadata, index_col="epoch")
    time_epoch_height = {}
    for e, (height, timestamp, _) in df.iterrows():
        key = parse(timestamp).strftime("%Y-%m-%d")
        time_epoch_height[key] = (e, height)

    for delta in range(-args.num, 0):
        day = args.last_date + timedelta(days=delta)
        key = day.strftime("%Y-%m-%d")
        timestamp = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
        epoch, height = time_epoch_height[key]

        check_distribution(args=args, epoch=epoch, height=height, timestamp=timestamp)
