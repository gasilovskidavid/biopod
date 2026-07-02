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


class Reading(BaseModel):
    pod_id: str
    timestamp: str
    co2_ppm: float
    temperature_c: float
    rh_pct: float
    water_ph: float
    light_ppfd: float


@app.get("/readings")
def query_readings(
    pod_id: str, start_time: str | None = None, end_time: str | None = None
) -> list[Reading]:
    pod_query_key = Key("pod_id").eq(pod_id)
    if start_time and end_time:
        pod_query_key &= Key("timestamp").between(start_time, end_time)
    elif start_time:
        pod_query_key &= Key("timestamp").gte(start_time)
    elif end_time:
        pod_query_key &= Key("timestamp").lte(end_time)

    response = table.query(KeyConditionExpression=pod_query_key)
    readings = response.get("Items", [])
    if not readings:
        raise HTTPException(
            status_code=404,
            detail=f"No readings found for pod {pod_id} for selected timerange",
        )
    return [Reading(**item) for item in readings]
