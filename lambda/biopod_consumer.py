import base64
import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

AWS_REGION = os.environ.get("AWS_REGION")
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME")

dynamodb_client = boto3.client('dynamodb', region_name=AWS_REGION)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, _context):
    for record in event["Records"]:
        try:
            raw_data = base64.b64decode(record["kinesis"]["data"])
            reading = json.loads(raw_data)
            item = {
                'pod_id': {'S': reading['pod_id']},
                'timestamp': {'S': reading['timestamp']},
                'co2_ppm': {'N': str(reading['co2_ppm'])},
                'temperature_c': {'N': str(reading['temperature_c'])},
                'rh_pct': {'N': str(reading['rh_pct'])},
                'water_ph': {'N': str(reading['water_ph'])},
                'light_ppfd': {'N': str(reading['light_ppfd'])},
            }
            dynamodb_client.put_item(
                TableName=DYNAMODB_TABLE_NAME,
                Item=item,
            )
            logger.info(
                f"pod = {reading['pod_id']}, co2 = {reading['co2_ppm']:.1f},"
                f"temp = {reading['temperature_c']:.1f}"
            )
        except (ValueError, TypeError) as e:
            logger.warning(
                f"Skipped faulty record(seq={record['kinesis']['sequenceNumber']}): {e}"
            )
        except ClientError as e:
            logger.error(f"Write failed to DynamoDB table: {e}")
    return {"statusCode": 200}
