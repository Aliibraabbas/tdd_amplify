"""
Lambda userHandler
• add_user(payload)        
• get_user(id)          
• get_user_by_email(email)  
• lambda_handler(event, …)  
"""

from __future__ import annotations

import json
import os
import uuid
from typing import Any, Dict, Optional

import boto3
from boto3.dynamodb.conditions import Key


# DynamoDB : nom de table + ressource   

TABLE_NAME: str = os.environ.get("STORAGE_USERTABLE_NAME", "UserTable")

dynamodb = boto3.resource("dynamodb", region_name="eu-west-1")
table = dynamodb.Table(TABLE_NAME)  

def debug_scan():
    """Affiche dans CloudWatch les 5 premiers items de la table."""
    # print("SCAN result:", table.scan(Limit=5))


def add_user(user: Dict[str, Any]) -> Dict[str, Any]:
    """Insert new user and return the full item."""
    item = {"user_id": str(uuid.uuid4()), **user}
    table.put_item(Item=item)
    debug_scan()  
    return item


def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    """Fetch by primary key."""
    resp = table.get_item(Key={"user_id": user_id})
    return resp.get("Item")


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Fetch by scanning on 'email' attribute (no GSI)."""
    resp = table.scan(
        FilterExpression=Key("email").eq(email),
        Limit=1
    )
    items = resp.get("Items", [])
    return items[0] if items else None


# Lambda handler                                                              #
def handler(event, _context): 
   
    # Event attendu :
    #   { "action": "add", "payload": { "name": "...", "email": "..." } }
    #   { "action": "get", "payload": { "user_id": "..." } }
   
    action = event.get("action")
    payload = event.get("payload", {})

    try:
        if action == "add":
            result, status = add_user(payload), 201
        elif action == "get":
            result = get_user(payload["user_id"])
            status = 200 if result else 404
        elif action == "get_email":            
            result = get_user_by_email(payload["email"])
            status = 200 if result else 404
        else:
            raise ValueError("Unknown action")

        return {
            "statusCode": status,
            "body": json.dumps(result, ensure_ascii=False),
            "headers": {"Content-Type": "application/json"},
        }

    except Exception as exc: 
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(exc)}),
        }
