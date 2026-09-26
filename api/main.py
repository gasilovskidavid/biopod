import logging
import os
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()

AWS_REGION = os.environ.get("AWS_REGION")
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

logger = logging.getLogger(__name__)

app = FastAPI()

MAX_ITEMS = 10_000

DYNAMODB_ERROR_STATUS: dict[str, int] = {
    "ProvisionedThroughputExceededException": 503,
    "ThrottlingException": 503,
    "RequestLimitExceeded": 503,
    "InternalServerError": 503,
    "ValidationException": 500,
    "ResourceNotFoundException": 500,
}

DYNAMODB_RETRY_AFTER_SECONDS = "2"

DYNAMODB_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

def parse_iso8601(field_name: str, value: str) -> str:
    try:
        dt = datetime.fromisoformat(value)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid {field_name!r}: {value!r} is not a valid ISO-8601 datetime."
            ),
        ) from e

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime(DYNAMODB_TIMESTAMP_FORMAT)


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

        try:
            response = table.query(**query_kwargs)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            request_id = e.response.get("ResponseMetadata", {}).get(
                "RequestId", "Unknown"
            )
            status_code = DYNAMODB_ERROR_STATUS.get(error_code, 500)

            logger.error(
                "DynamoDB query failed: code=%s request_id=%s status=%s",
                error_code,
                request_id,
                status_code,
            )

            if status_code == 503:
                raise HTTPException(
                    status_code=503,
                    detail=(
                        "The readings service is temporarily unavailable. "
                        "Please retry shortly."
                    ),
                    headers={"Retry-After": DYNAMODB_RETRY_AFTER_SECONDS},
                ) from e
            raise HTTPException(
                status_code=500,
                detail="An internal error occurred while retrieving readings.",
            ) from e

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
    if start_time is not None:
        start_time = parse_iso8601("start_time", start_time)
    if end_time is not None:
        end_time = parse_iso8601("end_time", end_time)

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
