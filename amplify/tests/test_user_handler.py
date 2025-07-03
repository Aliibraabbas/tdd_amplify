"""
Unit-tests Moto pour la Lambda userHandler
‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
• Vérifie add_user / get_user / get_user_by_email
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import boto3
from moto import mock_dynamodb


#chemin vers la Lambda + var d’env                            
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT / "function" / "userHandler" / "src"))

TABLE = "UserTable"
os.environ["STORAGE_USERTABLE_NAME"] = TABLE  

import index as handler  # type: ignore  # module importé dynamiquement


def _create_table() -> None:
    """Create Moto table (PK user_id + GSI email-index)."""
    ddb = boto3.resource("dynamodb", region_name="eu-west-1")
    ddb.create_table(
        TableName=TABLE,
        KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "email", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "email-index",
                "KeySchema": [{"AttributeName": "email", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
                "ProvisionedThroughput": {"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    # Rebind le handler sur la table Moto
    handler.table = ddb.Table(TABLE)

@mock_dynamodb
def test_add_and_get() -> None:
    _create_table()
    saved = handler.add_user({"name": "Ali", "email": "ali@example.com"})
    assert handler.get_user(saved["user_id"]) == saved


@mock_dynamodb
def test_get_by_email() -> None:
    _create_table()
    handler.add_user({"name": "Bob", "email": "bob@example.com"})
    res = handler.get_user_by_email("bob@example.com")
    assert res and res["name"] == "Bob"
