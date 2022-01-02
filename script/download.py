import argparse
import json
import os
import os.path as osp
import subprocess
from glob import glob

import pandas as pd
from tqdm import tqdm

pd.options.mode.chained_assignment = None


def download_height(start_epoch, end_epoch):
    print("[Download] Block Height")
    assert osp.exists(args.metadata)
    df = pd.read_csv(args.metadata, index_col="epoch")
    if end_epoch == -1:
        end_epoch = len(df)
    for e, (block_height, time, price) in tqdm(df.iterrows(), total=len(df)):
        if e < start_epoch:
            continue
        if end_epoch < e:
            break
        fn = osp.join("data", "{0:04}".format(e) + ".json")

        if e < 98:
            url = f"{args.server}/block_results?height={block_height - 1}"
        else:
            url = f"{args.server}/block_results?height={block_height}"
        subprocess.call(
            [
                "curl",
                url,
                "--output",
                fn,
                "--keepalive-time",
                "60",
                "--connect-timeout",
                "0",
                "--max-time",
                "600",
                "--keepalive",
                "-vv",
            ]
        )


def check_distribution():
    files = glob("data/*.json")
    files = sorted(files)
    for file in tqdm(files, total=len(files)):
        find = False
        with open(file, "r") as f:
            data = json.load(f)

        for event in data["result"]["begin_block_events"]:
            if event["type"] == "distribution":
                find = True
                print(f"[begin_block_events] in {file}")
                break

        for event in data["result"]["end_block_events"]:
            if event["type"] == "distribution":
                find = True
                print(f"[end_block_events] in {file}")
                break

        if not find:
            print(f"[Warning] Distribution is not found in {file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--server", type=str, default="http://localhost:26657")
    parser.add_argument("--metadata", type=str, default="epoch_height_price.csv")
    parser.add_argument("--start_epoch", type=int, default=1)
    parser.add_argument("--end_epoch", type=int, default=-1)
    parser.add_argument("--only_check", action="store_true")
    args = parser.parse_args()
    print(args)

    if not osp.exists("data"):
        os.makedirs("data")

    if not args.only_check:
        download_height(start_epoch=args.start_epoch, end_epoch=args.end_epoch)
    check_distribution()
