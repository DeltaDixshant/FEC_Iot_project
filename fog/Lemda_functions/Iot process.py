# AWS Lambda function: iot-process
#
# This Lambda is triggered automatically by SQS whenever a new message arrives
# in the queue (set up as an Event Source Mapping in AWS Lambda console).
# Its job is to take the processed sensor summary from the fog node and
# persist it into DynamoDB so the dashboard can query it later.
#
# Using SQS as the trigger (rather than calling DynamoDB directly from the fog)
# decouples the ingestion and storage steps — if DynamoDB is throttling, messages
# just queue up in SQS rather than failing at the fog node.

import json
import boto3
import os
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('SensorData')

def lambda_handler(event, context):
    # event['Records'] contains all the SQS messages delivered in this batch.
    # Lambda can batch multiple SQS messages together for efficiency — we handle
    # each one individually so a single bad record doesn't block the rest.
    for record in event['Records']:
        try:
            # SQS delivers the message body as a string, so we parse it back to a dict
            payload = json.loads(record['body'])
            
            # DynamoDB requires Decimal for numeric types — it doesn't accept Python floats
            # directly because of floating-point precision concerns. We convert via str()
            # to avoid any floating-point rounding issues during the conversion.
            item = {
                'sensor_type': payload['sensor_type'],   # partition key
                'timestamp': int(payload['timestamp']),  # sort key — integer seconds since epoch
                'value': Decimal(str(payload['value'])),
                'unit': payload['unit'],
                'count': int(payload.get('count', 1)),         # how many raw readings were aggregated
                'fog_processed': payload.get('fog_processed', True),
                'alert': payload.get('alert')                  # None if no threshold was breached
            }
            
            # put_item will insert a new record or overwrite an existing one with the same keys
            table.put_item(Item=item)
            print(f"✅ Stored in DynamoDB: {payload['sensor_type']} = {payload['value']}")
            
        except Exception as e:
            # Log the error but continue processing remaining messages in the batch
            print(f"❌ Error storing message: {str(e)}")
    
    return {'status': 'success'}