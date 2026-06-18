import json
import os
import boto3
from dotenv import load_dotenv
from dataclasses import dataclass, asdict
import time
import math
import random

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

t = 0

while True :

    reading = SensorReading(
    pod_id = "alpha",
    co2_ppm = 800 + 200 * math.sin(t) + random.gauss(0,10),
    temperature_c = 24 + 3 * math.sin(t) + random.gauss(0,0.2),
    ppf_umols = 400 + 400 * math.sin(t) + random.gauss(0,5),
    rh_pct = 70 + 10 * math.sin(t) + random.gauss(0,1),
    water_ph = 6.5 + 0.5 *  math.sin(t) + random.gauss(0,0.05),
    timestamp = time.asctime()
    )

    response = client.put_record(
        StreamName=STREAM_NAME,
        Data=json.dumps(asdict(reading)).encode("utf-8"),
        PartitionKey=reading.pod_id,
    )

    t+=1

    time.sleep(5)

    print(f"Sent: t={t}, co2={reading.co2_ppm:.1f}, temperature_c={reading.temperature_c:.1f}, ppf={reading.ppf_umols:.1f}, relative_humidity={reading.rh_pct:.1f}, water_ph={reading.water_ph:.1f}")