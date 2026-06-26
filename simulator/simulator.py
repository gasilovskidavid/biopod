import asyncio
import json
import logging
import math
import os
import random
import time
from dataclasses import asdict, dataclass

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

STREAM_NAME = os.environ.get("STREAM_NAME")
AWS_REGION = os.environ.get("AWS_REGION")

client = boto3.client("kinesis", region_name=AWS_REGION)

logger = logging.getLogger(__name__)


@dataclass
class SensorReading:
    pod_id: str
    co2_ppm: float
    temperature_c: float
    light_ppfd: float
    rh_pct: float
    water_ph: float
    timestamp: str


PODS = ["alpha", "beta", "gamma"]


def generate_reading(pod_id: str, t: float) -> SensorReading:
    return SensorReading(
        pod_id=pod_id,
        co2_ppm=800 + 200 * math.sin(t) + random.gauss(0, 10),
        temperature_c=24 + 3 * math.sin(t) + random.gauss(0, 0.2),
        light_ppfd=400 + 400 * math.sin(t) + random.gauss(0, 5),
        rh_pct=70 + 10 * math.sin(t) + random.gauss(0, 1),
        water_ph=6.5 + 0.5 * math.sin(t) + random.gauss(0, 0.05),
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )


t = 0


async def run_pod(pod_id: str, phase_offset: float = 0.0, start_delay: float = 0.0):
    await asyncio.sleep(start_delay)
    t = phase_offset
    while True:
        reading = generate_reading(pod_id, t)
        try:
            client.put_record(
                StreamName=STREAM_NAME,
                Data=json.dumps(asdict(reading)).encode("utf-8"),
                PartitionKey=pod_id,
            )
            logger.info(f"{pod_id} sent at {time.time():.2f}")
        except ClientError as e:
            logger.warning(f"{pod_id}: put_record failed - {e}")
        print(
            f"Sent: pod id = {reading.pod_id}, co2={reading.co2_ppm:.1f}, "
            f"temperature_c={reading.temperature_c:.1f}, "
            f"ppfd={reading.light_ppfd:.1f}, "
            f"relative_humidity={reading.rh_pct:.1f}, "
            f"water_ph={reading.water_ph:.1f}"
        )
        t += 1
        jitter = random.uniform(-0.5, 0.5)
        await asyncio.sleep(5 + jitter)


async def main():
    offsets = {
        "alpha": {"phase_offset": 0.0, "start_delay": 0.0},
        "beta": {"phase_offset": 2.0, "start_delay": 1.5},
        "gamma": {"phase_offset": 4.0, "start_delay": 3.3},
    }
    await asyncio.gather(*(run_pod(pod_id, **cfg) for pod_id, cfg in offsets.items()))


asyncio.run(main())
