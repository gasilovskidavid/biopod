import json 
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

STREAM_NAME = os.environ.get('STREAM_NAME')
AWS_REGION = os.environ.get('AWS_REGION')

client = boto3.client('kinesis', region_name=AWS_REGION)

record = {
    "pod_id" : "alpha",
    "co2_ppm" : 800, 
    "temperature_c" : 22.5
}


response = client.put_record(
    StreamName = STREAM_NAME,
    Data = json.dumps(record).encode('utf-8'),
    PartitionKey = "alpha"
)

print(response)