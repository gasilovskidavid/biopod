import json
import base64
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    for record in event["Records"]:
        try:
            raw_data = base64.b64decode(record["kinesis"]["data"])
            reading = json.loads(raw_data)
            logger.info(f"pod = {reading['pod_id']}, co2 = {reading['co2_ppm']:.1f}, temp = {reading['temperature_c']:.1f}")
        except(ValueError, TypeError) as e:
            logger.warning(f"Skipped faulty record (seq={record['kinesis']['sequenceNumber']}): {e}")
    return {"statusCode": 200}