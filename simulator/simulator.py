import json 
import boto3

client = boto3.client('Kinesis', region = 'eu-west-3')

record = {
    "pod_id" : "alpha",
    "co2_ppm" : 800, 
    "temperature_c" : 22.5
}


response = client.put_record(
    StreamName = "biopod-telemetry",
    Data = json.dumps(record).encode('utf-8'),
    PartitionKey = "alpha"
)

print(response)