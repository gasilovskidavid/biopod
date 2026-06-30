from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from boto3.dynamodb.types import TypeDeserializer

import boto3
import os

AWS_REGION = os.environ.get("AWS_REGION")
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME")

dynamodb_client = boto3.client('dynamodb', region_name=AWS_REGION)

app = FastAPI()

class Item(BaseModel):
    pod_id: str
    timestamp: str
    co2_ppm: float
    temperature_c: float
    rh_pct: float
    water_ph: float
    light_ppfd: float

@app.get("/items/{pod_id}/{start_time}/{end_time}", response_model=list[Item])
def querydb(pod_id: str, start_time: int, end_time: int) -> list[Item]:
    response = dynamodb_client.query(
        TableName=DYNAMODB_TABLE_NAME,
        KeyConditionExpression="pod_id = :pid AND #ts BETWEEN :start AND :end",
        ExpressionAttributeNames={"#ts": "timestamp"},
        ExpressionAttributeValues={
            ":pid": {"S": pod_id},
            ":start": {"N": str(start_time)},
            ":end": {"N": str(end_time)},
        },
    )
    if not response["Items"]:
        raise HTTPException(status_code=404, detail=f"No items found for pod {pod_id}"
                            f"for selected timerange")
    deserializer = TypeDeserializer()
    return [
        {k: str(deserializer.deserialize(v)) if k == "timestamp" else deserializer.deserialize(v)
         for k, v in item.items()}
        for item in response["Items"]
    ]
