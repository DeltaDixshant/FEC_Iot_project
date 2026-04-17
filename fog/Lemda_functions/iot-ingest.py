import json
import boto3
import os

sqs = boto3.client('sqs')
QUEUE_URL = os.environ['QUEUE_URL']   # we will set this in environment variables

def lambda_handler(event, context):
    try:
        # The fog node sends JSON in the body
        body = json.loads(event['body'])
        
        # Send the processed payload to SQS
        response = sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(body)
        )
        
        print(f"✅ Ingest Lambda: Sent to SQS - {body['sensor_type']}")
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'status': 'success',
                'messageId': response['MessageId'],
                'sensor_type': body['sensor_type']
            })
        }
    except Exception as e:
        print(f"❌ Error in ingest: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }