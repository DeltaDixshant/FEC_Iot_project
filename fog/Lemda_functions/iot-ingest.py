# AWS Lambda function: iot-ingest
#
# This is the entry point on the cloud side of our FEC architecture.
# When the fog node finishes processing a sensor batch, it sends the result
# to this Lambda via API Gateway (HTTP POST). Our job here is simple:
# validate that the request has a body, and push the payload onto an SQS queue.
#
# Why SQS? We use a queue so the system can handle spikes in sensor data gracefully.
# If multiple fog nodes are sending at the same time, SQS absorbs the load and the
# downstream "process" Lambda reads from the queue at its own pace — no dropped data.

import json
import boto3
import os

# Create the SQS client once at module level so it's reused across Lambda invocations.
# Lambda keeps the execution environment warm between calls, so this saves the overhead
# of creating a new client on every request.
sqs = boto3.client('sqs')

# The queue URL comes from an environment variable set in the Lambda console.
# Keeping it out of the code means we can point to a different queue (e.g. staging vs production)
# without touching the source code.
QUEUE_URL = os.environ['QUEUE_URL']

def lambda_handler(event, context):
    try:
        # API Gateway delivers the HTTP request body as a JSON string in event['body'],
        # so we need to parse it back into a Python dict first.
        body = json.loads(event['body'])
        
        # Push the processed sensor payload onto the SQS queue.
        # The downstream Lambda (iot-process) will pick this up and write it to DynamoDB.
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
                'messageId': response['MessageId'],   # useful for tracing the message later
                'sensor_type': body['sensor_type']
            })
        }
    except Exception as e:
        # Return 500 so the fog node knows the dispatch failed and can log/retry
        print(f"❌ Error in ingest: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }