import base64
import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

AWS_REGION = os.environ.get("AWS_REGION")
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME")
CO2_ALERT_THRESHOLD = os.environ.get("CO2_ALERT_THRESHOLD")
SNS_TOPIC = os.environ.get("SNS_TOPIC")

dynamodb_client = boto3.client("dynamodb", region_name=AWS_REGION)
sns_client = boto3.client("sns", region_name=AWS_REGION)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def threshold_passed_before_check(pod_id) -> bool:
    try:
        response = dynamodb_client.query(
            TableName=DYNAMODB_TABLE_NAME,
            KeyConditionExpression="pod_id = :pid",
            ExpressionAttributeValues={":pid": {"S": pod_id}},
            ScanIndexForward=False,
            Limit=1,
        )
        items = response.get("Items", [])
        if not items:
            return False
        previous_co2_level = float(items[0]["co2_ppm"]["N"])
        return previous_co2_level > CO2_ALERT_THRESHOLD
    except (ClientError, KeyError, ValueError) as e:
        logger.warning(
            f"Couldn't get previous alert state for {pod_id}, alerting anyway: {e}"
        )
        return False


def lambda_handler(event, _context):
    for record in event["Records"]:
        try:
            raw_data = base64.b64decode(record["kinesis"]["data"])
            reading = json.loads(raw_data)
            pod_id = reading["pod_id"]
            co2_ppm = reading["co2_ppm"]
            item = {
                "pod_id": {"S": reading["pod_id"]},
                "timestamp": {"S": reading["timestamp"]},
                "co2_ppm": {"N": str(reading["co2_ppm"])},
                "temperature_c": {"N": str(reading["temperature_c"])},
                "rh_pct": {"N": str(reading["rh_pct"])},
                "water_ph": {"N": str(reading["water_ph"])},
                "light_ppfd": {"N": str(reading["light_ppfd"])},
            }
            is_threshold_just_passed = (
                co2_ppm > CO2_ALERT_THRESHOLD
                and not threshold_passed_before_check(pod_id)
            )
            dynamodb_client.put_item(
                TableName=DYNAMODB_TABLE_NAME,
                Item=item,
            )
            logger.info(
                f"pod = {reading['pod_id']}, co2 = {reading['co2_ppm']:.1f},"
                f"temp = {reading['temperature_c']:.1f}"
            )
            if is_threshold_just_passed:
                sns_client.publish(
                    TopicArn=SNS_TOPIC,
                    Subject=f"High CO2 levels in Biopod {pod_id} alert",
                    Message=(
                        f"Biopod {pod_id} CO2 level at {co2_ppm:.1f} ppm "
                        f"(threshold: {CO2_ALERT_THRESHOLD} ppm passed) "
                        f"at {reading['timestamp']}."
                    ),
                )
                logger.info(f"Alert published for {pod_id}: {co2_ppm:.1f} ppm")
        except (ValueError, TypeError) as e:
            logger.warning(
                f"Skipped faulty record(seq={record['kinesis']['sequenceNumber']}): {e}"
            )
        except ClientError as e:
            logger.error(f"Write failed to DynamoDB table: {e}")
    return {"statusCode": 200}
