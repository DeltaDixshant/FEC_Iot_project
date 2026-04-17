import json
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('SensorData')

SENSOR_TYPES = ["temperature", "humidity", "pm25", "light"]

def _to_jsonable(item):
    for k, v in list(item.items()):
        if isinstance(v, Decimal):
            item[k] = float(v)
    return item

def lambda_handler(event, context):
    try:
        print("📡 iot-query Lambda called")

        all_items = []
        # Query each sensor type to guarantee data for all types
        for stype in SENSOR_TYPES:
            resp = table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('sensor_type').eq(stype),
                ScanIndexForward=False,  # latest first
                Limit=25
            )
            items = resp.get('Items', [])
            all_items.extend(items)

        # Convert Decimal to float
        all_items = [_to_jsonable(i) for i in all_items]

        # Sort newest first
        all_items.sort(key=lambda x: x.get("timestamp", 0), reverse=True)

        print(f"✅ Returned {len(all_items)} records")

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
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