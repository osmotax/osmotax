import argparse
import json
import os.path as osp
from datetime import datetime, timezone
from time import sleep

import pandas as pd
import requests
from dateutil.parser import parse
from tqdm import tqdm


def get_osmo_price():
    r = requests.get(
        "https://api-osmosis.imperator.co/tokens/v1/historical/osmo/chart?range=2000d"
    )
    assert r.status_code == 200
    timestamp_price = {}
    for row in json.loads(r.text):
        timestamp_price[row["time"]] = row["close"]
    return timestamp_price


def convert_timestamp_to_osmo_price(timestamp, timestamp_price):
    ts = parse(timestamp)
    ts = datetime(ts.year, ts.month, ts.day, ts.hour, tzinfo=timezone.utc)
    key = int(ts.timestamp())

    price = 0
    if key in timestamp_price:
        price = timestamp_price[key]
    return price


def create_metadata(args):
    timestamp_price = get_osmo_price()

    rows = {}
    start_epoch = 1
    if osp.exists(args.output):
        df = pd.read_csv(args.output, index_col="epoch")
        for e, (height, timestamp, price) in df.iterrows():
            rows[str(e)] = {"height": height, "time": timestamp, "price": price}
        if len(df) > 0:
            start_epoch = df.index[-1] + 1

    start_epoch = start_epoch if args.start_epoch == 0 else args.start_epoch
    end_epoch = args.end_epoch
    print(f"[Info] Fetching epoch from {start_epoch} to {end_epoch}")

    for e in tqdm(range(start_epoch, end_epoch + 1)):
        if e < start_epoch:
            continue
        if end_epoch < e:
            break

        r = requests.get(
            f"{args.server}/block_search?query=%22epoch_start.epoch_number={e}%22"
        )
        assert r.status_code == 200
        r = json.loads(r.text)
        blocks = r["result"]["blocks"]
        if len(blocks) == 0:
            if e == 88:
                price = convert_timestamp_to_osmo_price(
                    timestamp="2021-09-14T17:14:46.02737054Z",
                    timestamp_price=timestamp_price,
                )
                rows["88"] = {
                    "height": 1182570,
                    "time": "2021-09-14T17:14:46.02737054Z",
                    "price": price,
                }
                continue
            else:
                print(f"Ended in epoch {e}")
                break
        assert isinstance(blocks, list) and (len(blocks) == 2 or len(blocks) == 1)
        day_idx = -1
        if len(blocks) == 1:
            day_idx = 0
        elif len(blocks) == 2:
            T1 = parse(blocks[0]["block"]["header"]["time"])
            T2 = parse(blocks[1]["block"]["header"]["time"])
            assert T1 != T2
            if T1 < T2:
                day_idx = 0
            elif T1 > T2:
                day_idx = 1

        price = convert_timestamp_to_osmo_price(
            timestamp=blocks[day_idx]["block"]["header"]["time"],
            timestamp_price=timestamp_price,
        )

        rows[str(e)] = {
            "height": blocks[day_idx]["block"]["header"]["height"],
            "time": blocks[day_idx]["block"]["header"]["time"],
            "price": price,
        }
        sleep(0.33)

    df = pd.DataFrame.from_dict(rows, orient="index")
    df.index.name = "epoch"
    df.to_csv(args.output, index="epoch")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--server", type=str, default="http://localhost:26657")
    parser.add_argument("--output", type=str, default="epoch_height_price.csv")
    parser.add_argument("--start_epoch", type=int, default=0)
    parser.add_argument("--end_epoch", type=int, default=10000)
    args = parser.parse_args()
    print(args)

    create_metadata(args=args)
