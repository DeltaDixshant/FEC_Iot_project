# AWS Lambda function: iot-query
#
# This Lambda is called by the frontend dashboard whenever it needs fresh data.
# It queries our DynamoDB table and returns the latest sensor readings so the
# dashboard can update its charts, KPI cards, and alerts.
#
# DynamoDB is a key-value / document store, and our table uses sensor_type as the
# partition key and timestamp as the sort key. This means we have to run a separate
# query for each sensor type — we can't do one scan across all types efficiently.
# That's why we loop through SENSOR_TYPES and merge the results manually.
#
# We also need to handle Decimal values here because DynamoDB returns numbers as
# Python Decimal objects (not float), and json.dumps() doesn't know how to
# serialise Decimals — so we convert them to float before returning.

import json
import boto3
from decimal import Decimal

# DynamoDB resource — the table name is hardcoded because there's only one table
# in this project; for a larger system we'd use an environment variable.
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('SensorData')

# All the sensor types we track — if a new sensor is added to the project, just add it here
SENSOR_TYPES = ["temperature", "humidity", "pm25", "light"]

def _to_jsonable(item):
    # DynamoDB stores floating-point numbers as Decimal to avoid precision issues.
    # We need to convert them back to float so json.dumps() can handle the response.
    for k, v in list(item.items()):
        if isinstance(v, Decimal):
            item[k] = float(v)
    return item

def lambda_handler(event, context):
    try:
        print("📡 iot-query Lambda called")

        all_items = []

        # Query each sensor type separately and combine the results.
        # ScanIndexForward=False means DynamoDB returns newest records first (descending sort key),
        # and Limit=25 caps how much data we pull back per sensor to keep response times fast.
        for stype in SENSOR_TYPES:
            resp = table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('sensor_type').eq(stype),
                ScanIndexForward=False,
                Limit=25
            )
            items = resp.get('Items', [])
            all_items.extend(items)

        # Convert all Decimal values before serialising to JSON
        all_items = [_to_jsonable(i) for i in all_items]

        # Final sort so the dashboard receives data newest-first regardless of sensor type
        all_items.sort(key=lambda x: x.get("timestamp", 0), reverse=True)

        print(f"✅ Returned {len(all_items)} records")

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                # CORS headers are required so the browser doesn't block the fetch() call
                # in the dashboard (since the API is on a different domain than the HTML file)
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            "body": json.dumps(all_items)
        }

    except Exception as e:
        print(f"❌ Error in iot-query: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"error": str(e)})
        }