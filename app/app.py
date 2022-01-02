import argparse
from datetime import datetime

import pandas as pd
from dateutil.parser import parse
from flask import *
from flask_recaptcha import ReCaptcha

from app.config import RECAPTCHA_SECRET_KEY, RECAPTCHA_SITE_KEY
from model.tax import Tax

app = Flask(__name__)
app.config["RECAPTCHA_SITE_KEY"] = RECAPTCHA_SITE_KEY
app.config["RECAPTCHA_SECRET_KEY"] = RECAPTCHA_SECRET_KEY
recaptcha = ReCaptcha(app)


def load_prices():
    df = pd.read_csv(args.metadata, index_col="epoch")
    time_price = {}
    for e, (block_height, timestamp, price) in df.iterrows():
        ts = parse(timestamp)
        timestamp = ts.strftime("%m/%d/%Y")
        time_price[timestamp] = price
    return time_price


@app.route("/", methods=["GET", "POST"])
def index():
    WalletAddress = ""
    sStartDate = ""
    sEndDate = ""
    taxs = ""
    total_amount = 0.0
    total_price = 0.0

    if request.method == "POST" and "WalletAddress" in request.form:
        if recaptcha.verify():
            WalletAddress = request.form["WalletAddress"].strip()
            StartDate = request.form["StartDate"].strip()
            sStartDate = StartDate
            EndDate = request.form["EndDate"].strip()
            sEndDate = EndDate

            if len(StartDate) > 0:
                StartDate = parse(StartDate)
            else:
                StartDate = parse("01/01/2021")

            if len(EndDate) > 0:
                EndDate = parse(EndDate)
            else:
                EndDate = datetime.utcnow()

            taxs = ""
            for tax in Tax.query(
                WalletAddress, Tax.timestamp.between(StartDate, EndDate)
            ):
                date = tax.timestamp.strftime("%m/%d/%Y")
                price = args.time_price[date]
                amount = sum(tax.osmo) / 1000000
                total_amount += amount
                total_price += amount * price
                taxs += f"<tr><td>{date}</td><td>{round(amount, 2)}</td><td>{round(price, 2)}</td><td>{round(amount * price, 2)}</td></tr>"

    return render_template(
        "index.html",
        WalletAddress=WalletAddress,
        StartDate=sStartDate,
        EndDate=sEndDate,
        taxs=taxs,
        total_amount=round(total_amount, 2),
        total_price=round(total_price, 2),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--metadata", type=str, default="epoch_height_price.csv")
    parser.add_argument("--port", type=int, default=8888)
    args = parser.parse_args()
    args.time_price = load_prices()

    app.run(host="0.0.0.0", debug=True, port=args.port)
