"""
Initialize shared AWS clients.
"""

import boto3
from .config import settings

dynamodb = boto3.resource(
    "dynamodb",
    region_name=settings.AWS_REGION
)

s3 = boto3.client(
    "s3",
    region_name=settings.AWS_REGION
)

sns_client = boto3.client(
    "sns",
    region_name=settings.AWS_REGION
)

ses_client = boto3.client(
    "ses",
    region_name=settings.AWS_REGION
)


def get_dynamodb_table(table_name: str):
    """
    Get a DynamoDB table resource by name.
    
    Args:
        table_name: Name of the DynamoDB table
    
    Returns:
        boto3 DynamoDB Table resource
    """
    return dynamodb.Table(table_name)
