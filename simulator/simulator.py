import json
import os

import boto3
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()

STREAM_NAME = os.environ.get("STREAM_NAME")
AWS_REGION = os.environ.get("AWS_REGION")

client = boto3.client("kinesis", region_name=AWS_REGION)

@dataclass
class SensorReading:
    pod_id: str
    co2_ppm: float
    temperature_c: float
    ppf_umols: float
    rh_pct: float
    water_ph: float
    timestamp: str

response = client.put_record(
    StreamName=STREAM_NAME,
    Data=json.dumps(record).encode("utf-8"),
    PartitionKey="alpha",
)

print(response)
