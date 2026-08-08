import os

import boto3
from boto3.dynamodb.conditions import Key
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()

AWS_REGION = os.environ.get("AWS_REGION")
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

app = FastAPI()

# Items are small (2 strings + 5 floats, ~150-250 bytes each), so 10k items is a
# bounded payload that covers realistic query windows while protecting against an
# unbounded/mistaken time range driving many DynamoDB pages into one huge response.
MAX_ITEMS = 10_000


class Reading(BaseModel):
    pod_id: str
    timestamp: str
    co2_ppm: float
    temperature_c: float
    rh_pct: float
    water_ph: float
    light_ppfd: float


class ReadingsResponse(BaseModel):
    items: list[Reading]
    count: int
    truncated: bool


def fetch_all_readings(pod_query_key) -> tuple[list[dict], bool]:
    items: list[dict] = []
    exclusive_start_key = None

    while True:
        query_kwargs = {"KeyConditionExpression": pod_query_key}
        if exclusive_start_key:
            query_kwargs["ExclusiveStartKey"] = exclusive_start_key

        response = table.query(**query_kwargs)
        items.extend(response.get("Items", []))

        if len(items) >= MAX_ITEMS:
            return items[:MAX_ITEMS], True

        exclusive_start_key = response.get("LastEvaluatedKey")
        if not exclusive_start_key:
            return items, False


@app.get("/readings")
def query_readings(
    pod_id: str, start_time: str | None = None, end_time: str | None = None
) -> ReadingsResponse:
    pod_query_key = Key("pod_id").eq(pod_id)
    if start_time and end_time:
        pod_query_key &= Key("timestamp").between(start_time, end_time)
    elif start_time:
        pod_query_key &= Key("timestamp").gte(start_time)
    elif end_time:
        pod_query_key &= Key("timestamp").lte(end_time)

    readings, truncated = fetch_all_readings(pod_query_key)
    if not readings:
        raise HTTPException(
            status_code=404,
            detail=f"No readings found for pod {pod_id} for selected timerange",
        )
    return ReadingsResponse(
        items=[Reading(**item) for item in readings],
        count=len(readings),
        truncated=truncated,
    )
