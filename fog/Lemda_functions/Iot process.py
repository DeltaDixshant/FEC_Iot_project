import json
import boto3
import os
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('SensorData')

def lambda_handler(event, context):
    for record in event['Records']:
        try:
            payload = json.loads(record['body'])
            
            # Convert float to Decimal (required by DynamoDB)
            item = {
                'sensor_type': payload['sensor_type'],
                'timestamp': int(payload['timestamp']),   # sort key
                'value': Decimal(str(payload['value'])),
                'unit': payload['unit'],
                'count': int(payload.get('count', 1)),
                'fog_processed': payload.get('fog_processed', True),
                'alert': payload.get('alert')
            }
            
            table.put_item(Item=item)
            print(f"✅ Stored in DynamoDB: {payload['sensor_type']} = {payload['value']}")
            
        except Exception as e:
            print(f"❌ Error storing message: {str(e)}")
    
    return {'status': 'success'}