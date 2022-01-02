import argparse
import base64
import json
import os.path as osp
from collections import defaultdict
from datetime import datetime, timezone
from glob import glob

import pandas as pd
from dateutil.parser import parse
from tqdm import tqdm

from model.tax import Tax
from script.utils.bech32 import bech32encode


def create_chunks(l, n):
    n = max(1, n)
    return (l[i : i + n] for i in range(0, len(l), n))


def save_distribition(epoch_timestamp: dict):
    files = glob(f"data/*.json")
    files = sorted(files, reverse=True)
    for file in tqdm(files, total=len(files)):
        with open(file, "r") as f:
            data = json.load(f)

        epoch = int(osp.splitext(osp.basename(file))[0])
        print(f"[log] epoch {epoch}")
        timestamp = epoch_timestamp[epoch]

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
                                            [
                                                v
                                                for v in base64.b64decode(attr["value"])
                                            ],
                                        )
                                elif attr["key"] == "YW1vdW50":  # amount
                                    amount = str(
                                        base64.b64decode(attr["value"]), "utf-8"
                                    )
                                    for reward in [o for o in amount.split(",")]:
                                        if "uosmo" in reward:
                                            osmo = int(reward.replace("uosmo", ""))

                            if address and timestamp and amount:
                                rows[address]["amount"].append(amount)
                                rows[address]["osmo"].append(osmo)

        chunks = list(create_chunks(list(rows.items()), n=25))
        for chunk in tqdm(chunks, total=len(chunks)):
            with Tax.batch_write() as batch:
                for c in chunk:
                    batch.save(
                        Tax(
                            c[0],
                            timestamp,
                            amount=c[1]["amount"],
                            osmo=c[1]["osmo"],
                        )
                    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--metadata", type=str, default="epoch_height_price.csv")
    args = parser.parse_args()

    df = pd.read_csv(args.metadata, index_col="epoch")
    epoch_timestamp = {}
    for e, (height, timestamp, price) in df.iterrows():
        ts = parse(timestamp)
        timestamp = datetime(ts.year, ts.month, ts.day, tzinfo=timezone.utc)
        epoch_timestamp[e] = timestamp

    save_distribition(epoch_timestamp)
