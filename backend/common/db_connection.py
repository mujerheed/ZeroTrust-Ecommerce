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
