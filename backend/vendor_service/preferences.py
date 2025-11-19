"""
Vendor preferences management for TrustGuard.

This module handles vendor business preferences including:
- Auto-approve thresholds for low-value receipts
- Textract OCR enablement
- Other vendor-specific settings
"""

import time
from common.db_connection import dynamodb
from common.config import settings
from common.logger import logger
from typing import Dict, Optional


VENDOR_PREFERENCES_TABLE = dynamodb.Table(settings.VENDOR_PREFERENCES_TABLE)


def save_vendor_preferences(
    vendor_id: str,
    auto_approve_threshold: int = None,
    textract_enabled: bool = None,
    **additional_settings
) -> Dict:
    """
    Save or update vendor preferences in VENDOR_PREFERENCES_TABLE.
    
    Args:
        vendor_id: Vendor identifier
        auto_approve_threshold: Amount in kobo (e.g., 500000 = ₦5,000) below which receipts auto-approve
        textract_enabled: Whether to use Textract OCR for receipt verification
        **additional_settings: Any other vendor preferences
    
    Returns:
        Updated preferences record
    
    Raises:
        ValueError: If validation fails
    """
    # Get current preferences to merge
    current_prefs = get_vendor_preferences(vendor_id)
    
    preferences_record = {
        "vendor_id": vendor_id,
        "updated_at": int(time.time()),
    }
    
    if auto_approve_threshold is not None:
        if auto_approve_threshold < 0:
            raise ValueError("Auto-approve threshold must be non-negative")
        if auto_approve_threshold > 100000000:  # Max ₦1M = 100,000,000 kobo
            raise ValueError("Auto-approve threshold too high (max ₦1,000,000)")
        preferences_record["auto_approve_threshold"] = auto_approve_threshold
    else:
        preferences_record["auto_approve_threshold"] = current_prefs.get("auto_approve_threshold", 0)
    
    if textract_enabled is not None:
        preferences_record["textract_enabled"] = textract_enabled
    else:
        preferences_record["textract_enabled"] = current_prefs.get("textract_enabled", True)
    
    # Add any additional settings
    preferences_record.update(additional_settings)
    
    VENDOR_PREFERENCES_TABLE.put_item(Item=preferences_record)
    
    logger.info("Vendor preferences saved", extra={
        "vendor_id": vendor_id,
        "auto_approve_threshold": preferences_record["auto_approve_threshold"],
        "textract_enabled": preferences_record["textract_enabled"]
    })
    
    return preferences_record


def get_vendor_preferences(vendor_id: str) -> Dict:
    """
    Retrieve vendor preferences from VENDOR_PREFERENCES_TABLE.
    Returns default preferences if not customized.
    
    Args:
        vendor_id: Vendor identifier
    
    Returns:
        Vendor preferences dictionary with:
        - auto_approve_threshold: Amount in kobo (0 = disabled)
        - textract_enabled: Boolean
        - updated_at: Unix timestamp or None
    """
    resp = VENDOR_PREFERENCES_TABLE.get_item(Key={"vendor_id": vendor_id})
    
    if resp.get("Item"):
        logger.info("Vendor preferences retrieved", extra={
            "vendor_id": vendor_id,
            "auto_approve_threshold": resp["Item"].get("auto_approve_threshold", 0)
        })
        return resp["Item"]
    
    # Return default preferences
    logger.info("Using default vendor preferences", extra={"vendor_id": vendor_id})
    return {
        "vendor_id": vendor_id,
        "auto_approve_threshold": 0,  # Disabled by default (manual review required)
        "textract_enabled": True,  # Enable OCR by default
        "updated_at": None,
    }
