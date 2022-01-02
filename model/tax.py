import json
import os

from pynamodb.attributes import ListAttribute, UnicodeAttribute
from pynamodb.models import Model
from pynamodb_attributes import TimestampAttribute

from model.utils import ModelEncoder


class Tax(Model):
    class Meta:
        table_name = "osmosis-tax-test"

        if "ENV" in os.environ:
            host = "http://localhost:8000"
        else:
            region = "ap-northeast-2"
            host = "https://dynamodb.ap-northeast-2.amazonaws.com"

    address = UnicodeAttribute(hash_key=True)
    timestamp = TimestampAttribute(range_key=True)
    amount = ListAttribute(default=list)
    osmo = ListAttribute(default=list)

    def __str__(self):
        return json.dumps(self, cls=ModelEncoder)
