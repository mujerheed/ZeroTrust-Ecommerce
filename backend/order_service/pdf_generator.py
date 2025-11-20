"""
PDF generation utilities for order summaries.

Uses reportlab to generate professional PDF invoices/receipts
with order details, bank account info, and QR codes.
"""

from typing import Dict, Any
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
import qrcode
from datetime import datetime
from decimal import Decimal
from common.logger import logger


def generate_qr_code(data: str) -> BytesIO:
    """Generate QR code image from data string"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer


def convert_decimal_to_float(obj):
    """Recursively convert Decimal to float"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_to_float(item) for item in obj]
    return obj


def generate_order_pdf(order_summary: Dict[str, Any]) -> BytesIO:
    """
    Generate PDF document for order summary.
    
    Args:
        order_summary: Order summary dict from get_order_summary()
    
    Returns:
        BytesIO: PDF document as bytes
    """
    # Convert any Decimal objects to float
    order_summary = convert_decimal_to_float(order_summary)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                          rightMargin=72, leftMargin=72,
                          topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    normal_style = styles['BodyText']
    
    # ========== TITLE ==========
    elements.append(Paragraph("ORDER SUMMARY", title_style))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2563eb')))
    elements.append(Spacer(1, 12))
    
    # ========== ORDER INFO ==========
    order_id = order_summary.get("order_id", "N/A")
    status = order_summary.get("status", "N/A").upper()
    created_at = order_summary.get("created_at", 0)
    created_date = datetime.fromtimestamp(created_at).strftime("%B %d, %Y %I:%M %p") if created_at else "N/A"
    
    info_data = [
        ["Order ID:", order_id],
        ["Status:", status],
        ["Date:", created_date],
        ["Currency:", order_summary.get("currency", "NGN")]
    ]
    
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 20))
    
    # ========== ITEMS TABLE ==========
    elements.append(Paragraph("ORDER ITEMS", heading_style))
    
    items = order_summary.get("items", [])
    items_data = [["Item", "Qty", "Price", "Subtotal"]]
    
    for item in items:
        name = item.get("name", "N/A")
        qty = str(item.get("quantity", 0))
        price = float(item.get("price", 0))
        subtotal = float(item.get("subtotal", 0))
        
        items_data.append([
            name,
            qty,
            f"₦{price:,.2f}",
            f"₦{subtotal:,.2f}"
        ])
    
    # Add total row
    total_amount = float(order_summary.get("total_amount", 0))
    items_data.append(["", "", "TOTAL:", f"₦{total_amount:,.2f}"])
    
    items_table = Table(items_data, colWidths=[2.5*inch, 0.8*inch, 1.2*inch, 1.2*inch])
    items_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Data rows
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -2), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f9fafb')]),
        ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
        
        # Total row
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f3f4f6')),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
        ('TOPPADDING', (0, -1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 8),
        
        # Alignment
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(items_table)
    elements.append(Spacer(1, 20))
    
    # ========== PAYMENT DETAILS ==========
    payment_details = order_summary.get("payment_details")
    if payment_details:
        elements.append(Paragraph("PAYMENT INFORMATION", heading_style))
        
        payment_data = [
            ["Bank Name:", payment_details.get("bank_name", "N/A")],
            ["Account Number:", payment_details.get("account_number", "N/A")],
            ["Account Name:", payment_details.get("account_name", "N/A")],
        ]
        
        payment_table = Table(payment_data, colWidths=[2*inch, 4*inch])
        payment_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#eff6ff')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#2563eb')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(payment_table)
        
        # Add payment instructions
        if payment_details.get("instructions"):
            elements.append(Spacer(1, 8))
            instructions_style = ParagraphStyle(
                'Instructions',
                parent=styles['Italic'],
                fontSize=9,
                textColor=colors.grey
            )
            elements.append(Paragraph(payment_details["instructions"], instructions_style))
        
        elements.append(Spacer(1, 20))
    
    # ========== DELIVERY ADDRESS ==========
    if order_summary.get("requires_delivery") and order_summary.get("delivery_address"):
        elements.append(Paragraph("DELIVERY ADDRESS", heading_style))
        
        addr = order_summary["delivery_address"]
        address_lines = [
            addr.get("street", ""),
            f"{addr.get('city', '')}, {addr.get('state', '')}",
            addr.get("country", "Nigeria"),
        ]
        
        if addr.get("postal_code"):
            address_lines.insert(2, f"Postal Code: {addr['postal_code']}")
        
        if addr.get("landmark"):
            address_lines.append(f"Landmark: {addr['landmark']}")
        
        if addr.get("phone"):
            address_lines.append(f"Contact: {addr['phone']}")
        
        address_text = "<br/>".join(address_lines)
        elements.append(Paragraph(address_text, normal_style))
        elements.append(Spacer(1, 20))
    
    # ========== RECEIPT STATUS ==========
    receipt = order_summary.get("receipt")
    if receipt:
        elements.append(Paragraph("RECEIPT STATUS", heading_style))
        
        receipt_status = receipt.get("status", "N/A").upper()
        uploaded_at = receipt.get("uploaded_at", 0)
        uploaded_date = datetime.fromtimestamp(uploaded_at).strftime("%B %d, %Y %I:%M %p") if uploaded_at else "N/A"
        
        receipt_data = [
            ["Receipt ID:", receipt.get("receipt_id", "N/A")],
            ["Uploaded:", uploaded_date],
            ["Status:", receipt_status]
        ]
        
        receipt_table = Table(receipt_data, colWidths=[2*inch, 4*inch])
        receipt_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        elements.append(receipt_table)
        elements.append(Spacer(1, 20))
    
    # ========== QR CODE ==========
    # Generate QR code with order ID for quick lookup
    qr_data = f"ORDER:{order_id}"
    qr_buffer = generate_qr_code(qr_data)
    qr_image = Image(qr_buffer, width=1.5*inch, height=1.5*inch)
    
    elements.append(Paragraph("QR CODE FOR ORDER TRACKING", heading_style))
    elements.append(Spacer(1, 8))
    elements.append(qr_image)
    elements.append(Spacer(1, 8))
    qr_label = Paragraph(f"Scan to view order: {order_id}", styles['Italic'])
    elements.append(qr_label)
    
    # ========== FOOTER ==========
    elements.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("TrustGuard E-Commerce Platform", footer_style))
    elements.append(Paragraph("Secure Zero-Trust Transaction System", footer_style))
    elements.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", footer_style))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    logger.info(f"PDF generated for order {order_id}")
    
    return buffer
