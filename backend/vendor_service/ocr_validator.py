"""
OCR Validation Logic for Receipt Verification.

This module provides automated receipt validation using Textract OCR results.
It implements Zero Trust principles by verifying:
1. Amount extracted matches order amount
2. Vendor name/business matches expected vendor
3. OCR confidence scores meet minimum thresholds

Auto-approval logic:
- If Textract passes all checks → Auto-approve
- If Textract fails any check → Flag for manual vendor review
- If amount ≥ ₦1,000,000 → Always escalate to CEO (regardless of Textract)
"""

import re
from typing import Dict, Tuple, Optional
from decimal import Decimal
from common.logger import logger


class OCRValidationResult:
    """Result of OCR validation with detailed feedback."""
    
    def __init__(
        self,
        is_valid: bool,
        auto_approve: bool,
        requires_manual_review: bool,
        reason: str,
        details: Dict
    ):
        self.is_valid = is_valid
        self.auto_approve = auto_approve
        self.requires_manual_review = requires_manual_review
        self.reason = reason
        self.details = details
    
    def to_dict(self) -> Dict:
        return {
            "is_valid": self.is_valid,
            "auto_approve": self.auto_approve,
            "requires_manual_review": self.requires_manual_review,
            "reason": self.reason,
            "details": self.details
        }


def validate_receipt_ocr(
    order: Dict,
    receipt: Dict,
    vendor: Dict,
    confidence_threshold: float = 75.0,
    amount_tolerance_percent: float = 2.0
) -> OCRValidationResult:
    """
    Validate receipt using Textract OCR data.
    
    Args:
        order: Order record with expected amount
        receipt: Receipt record with textract_data
        vendor: Vendor record with business name
        confidence_threshold: Minimum OCR confidence (default 75%)
        amount_tolerance_percent: Allowed variance in amount (default 2%)
    
    Returns:
        OCRValidationResult with validation outcome and details
    """
    
    # Check if Textract OCR data exists
    textract_data = receipt.get("textract_data")
    if not textract_data:
        logger.warning("No Textract OCR data found", extra={
            "receipt_id": receipt.get("receipt_id"),
            "order_id": order.get("order_id")
        })
        return OCRValidationResult(
            is_valid=False,
            auto_approve=False,
            requires_manual_review=True,
            reason="NO_OCR_DATA",
            details={
                "message": "Receipt has not been processed by Textract OCR",
                "action_required": "Wait for OCR processing or manually review"
            }
        )
    
    # Extract OCR fields
    extracted_fields = textract_data.get("extracted_fields", {})
    metadata = textract_data.get("metadata", {})
    
    # Check overall OCR confidence
    ocr_confidence = metadata.get("extraction_confidence", 0)
    if ocr_confidence < confidence_threshold:
        logger.warning("OCR confidence too low", extra={
            "receipt_id": receipt.get("receipt_id"),
            "confidence": ocr_confidence,
            "threshold": confidence_threshold
        })
        return OCRValidationResult(
            is_valid=False,
            auto_approve=False,
            requires_manual_review=True,
            reason="LOW_CONFIDENCE",
            details={
                "ocr_confidence": ocr_confidence,
                "threshold": confidence_threshold,
                "message": f"OCR confidence ({ocr_confidence:.1f}%) below threshold ({confidence_threshold}%)"
            }
        )
    
    # Validate amount
    amount_validation = validate_amount(order, extracted_fields, amount_tolerance_percent)
    if not amount_validation["valid"]:
        logger.warning("Amount mismatch detected", extra={
            "receipt_id": receipt.get("receipt_id"),
            "expected": order.get("amount"),
            "extracted": amount_validation.get("extracted_amount")
        })
        return OCRValidationResult(
            is_valid=False,
            auto_approve=False,
            requires_manual_review=True,
            reason="AMOUNT_MISMATCH",
            details=amount_validation
        )
    
    # Validate vendor/business name (if available in OCR)
    vendor_validation = validate_vendor_name(vendor, textract_data.get("raw_text", ""))
    if not vendor_validation["valid"]:
        logger.warning("Vendor name mismatch", extra={
            "receipt_id": receipt.get("receipt_id"),
            "expected_vendor": vendor.get("name"),
            "ocr_text_sample": textract_data.get("raw_text", "")[:100]
        })
        # Note: Vendor name mismatch is flagged but not a hard failure
        # (many receipts don't show vendor name clearly)
        pass
    
    # All checks passed - AUTO-APPROVE
    logger.info("OCR validation PASSED - Auto-approving receipt", extra={
        "receipt_id": receipt.get("receipt_id"),
        "order_id": order.get("order_id"),
        "ocr_confidence": ocr_confidence,
        "amount_match": amount_validation["valid"],
        "vendor_match": vendor_validation["valid"]
    })
    
    return OCRValidationResult(
        is_valid=True,
        auto_approve=True,
        requires_manual_review=False,
        reason="OCR_VALIDATION_PASSED",
        details={
            "ocr_confidence": ocr_confidence,
            "amount_validation": amount_validation,
            "vendor_validation": vendor_validation,
            "message": "All OCR checks passed - Receipt auto-approved"
        }
    )


def validate_amount(
    order: Dict,
    extracted_fields: Dict,
    tolerance_percent: float = 2.0
) -> Dict:
    """
    Validate that extracted amount matches order amount within tolerance.
    
    Args:
        order: Order record
        extracted_fields: Textract extracted fields
        tolerance_percent: Allowed variance (default 2%)
    
    Returns:
        Dict with validation result and details
    """
    expected_amount = Decimal(str(order.get("amount", 0)))
    
    # Get extracted amount
    amount_field = extracted_fields.get("amount")
    if not amount_field or not amount_field.get("value"):
        return {
            "valid": False,
            "reason": "Amount not found in OCR",
            "expected_amount": float(expected_amount),
            "extracted_amount": None,
            "confidence": 0
        }
    
    # Parse extracted amount (remove commas, currency symbols)
    extracted_raw = amount_field["value"]
    extracted_clean = re.sub(r'[^\d.]', '', extracted_raw)
    
    try:
        extracted_amount = Decimal(extracted_clean)
    except:
        return {
            "valid": False,
            "reason": "Invalid amount format in OCR",
            "expected_amount": float(expected_amount),
            "extracted_amount": extracted_raw,
            "confidence": amount_field.get("confidence", 0)
        }
    
    # Calculate variance
    variance = abs(extracted_amount - expected_amount)
    variance_percent = (variance / expected_amount * 100) if expected_amount > 0 else 100
    
    is_valid = variance_percent <= tolerance_percent
    
    return {
        "valid": is_valid,
        "expected_amount": float(expected_amount),
        "extracted_amount": float(extracted_amount),
        "variance": float(variance),
        "variance_percent": float(variance_percent),
        "tolerance_percent": tolerance_percent,
        "confidence": amount_field.get("confidence", 0),
        "reason": "Amount matches within tolerance" if is_valid else f"Amount variance {variance_percent:.1f}% exceeds {tolerance_percent}%"
    }


def validate_vendor_name(vendor: Dict, ocr_raw_text: str) -> Dict:
    """
    Check if vendor/business name appears in OCR text.
    This is a soft validation (won't fail auto-approval alone).
    
    Args:
        vendor: Vendor record
        ocr_raw_text: Raw text from Textract
    
    Returns:
        Dict with validation result
    """
    vendor_name = vendor.get("name", "").lower()
    business_name = vendor.get("company_name", "").lower()
    
    if not vendor_name and not business_name:
        return {
            "valid": False,
            "reason": "No vendor name to validate",
            "searched_for": None,
            "found": False
        }
    
    ocr_text_lower = ocr_raw_text.lower()
    
    # Check if vendor name or business name appears in OCR text
    vendor_found = vendor_name in ocr_text_lower if vendor_name else False
    business_found = business_name in ocr_text_lower if business_name else False
    
    found = vendor_found or business_found
    
    return {
        "valid": found,
        "searched_for": vendor_name or business_name,
        "found": found,
        "vendor_name_match": vendor_found,
        "business_name_match": business_found,
        "reason": "Vendor name found in receipt" if found else "Vendor name not found (may be normal for bank receipts)"
    }


def should_escalate_to_ceo(order: Dict, high_value_threshold: int = 1000000) -> Tuple[bool, Optional[str]]:
    """
    Check if order should be escalated to CEO regardless of OCR validation.
    
    Args:
        order: Order record
        high_value_threshold: Amount threshold in kobo (default ₦1,000,000)
    
    Returns:
        Tuple of (should_escalate, reason)
    """
    amount = order.get("amount", 0)
    
    # High-value transaction check
    if amount >= high_value_threshold:
        return (True, f"HIGH_VALUE_TRANSACTION (₦{amount / 100:,.2f})")
    
    return (False, None)
