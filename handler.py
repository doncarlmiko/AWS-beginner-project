import json
import boto3
import os

dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
products_table = dynamodb.Table(os.environ["DYNAMO_TABLE"])
inventory_table = dynamodb.Table(os.environ["INVENTORY_TABLE"])

from datetime import datetime   

from decimal import Decimal

from boto3.dynamodb.conditions import Key

class DecimalEncoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, Decimal):
      return str(obj)
    return json.JSONEncoder.default(self, obj)

def hello(event, context):
    body = {
        "message": "This is my store!",
    }
    
    print(event)
    

    response = {"statusCode": 200, "body": json.dumps(body)}

    return response
    
def get_all_products(event, context):
    body = {
        "message": "I'm getting all the products",
        "input": event,
    }
    
    return_body = {}
    return_body["items"] = products_table.get_item(Key={'product_id': 'P9999'})
    
    return_body["status"] = "success"
    response = {"statusCode": 200, "body": json.dumps(return_body, cls=DecimalEncoder)}
    
    return response
    
def create_one_product(event, context):
    body = json.loads(event["body"], parse_float=Decimal)
        
    products_table.put_item(Item=body)
    
    response = {
        "statusCode": 200,
        "body": json.dumps(body, cls=DecimalEncoder)
    }

    return response

def delete_product(event, context):
    body = json.loads(event["body"], parse_float=Decimal)
        
    # Built-in method to delete an item
    products_table.delete_item(
        Key={
            'product_id': body['product_id']
        }
    )
    
    response = {
        "statusCode": 200,
        "body": json.dumps({"message": "Product deleted successfully!"})
    }

    return response
    
def update_product(event, context):
    body = json.loads(event["body"], parse_float=Decimal)

    response = products_table.update_item(
        Key={'product_id': body['product_id']},  # The primary key of the item to update
       
        UpdateExpression="SET price = :p, product_name = :n",
        ExpressionAttributeValues={
            ':p': Decimal(body['price']),
            ':n': body['product_name']
        }
    )
    return response

import boto3
import json
from decimal import Decimal
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='us-east-2')

def add_stocks_to_product(event, context):
    # Parse request body
    body = json.loads(event["body"], parse_float=Decimal)
    product_id = body["product_id"]
    quantity = body["quantity"]
    remarks = body.get("remarks", "")

     # Use current datetime as sort key
    timestamp = datetime.now().isoformat()

    # Add a new entry (log) to the ProductInventory table
    inventory_table.put_item(
        Item={
            "product_id": product_id,
            "datetime": timestamp,
            "quantity": quantity,
            "remarks": remarks
        }
    )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Stock entry added successfully!",
            "data": {
                "product_id": product_id,
                "datetime": timestamp,
                "quantity": quantity,
                "remarks": remarks
            }
        })
    }

def get_one_product(event, context):
    product_id = 'Don product 89'
    product = products_table.get_item(Key={"product_id": product_id})
    product_data = product.get("Item",{})
    
    # Get all inventory entries for that product
    inventory_items = inventory_table.query(KeyConditionExpression=Key("product_id").eq(product_id))
    inventory_items_result = inventory_items.get("Items", [])
    
    total_stocks = sum(item['quantity'] for item in inventory_items_result)
    
    # Sort inventory entries by datetime (to get the latest)
    latest_entry = max(inventory_items_result, key=lambda x: x["datetime"]) if inventory_items_result else None
    
    response = {
        "statusCode": 200,
        "body": json.dumps({
            "message": f"product id:{product_data['product_id']}, total stocks ={total_stocks}",
            "data": {
                    "product_id": product_data["product_id"],
                    "datetime": latest_entry["datetime"] if latest_entry else None,
                    "quantity": total_stocks,
                }
        }, cls=DecimalEncoder)
    }

    return response