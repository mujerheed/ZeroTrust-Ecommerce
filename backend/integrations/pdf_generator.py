"""
Transaction PDF Summary Generator

Generates professional PDF invoices/summaries for completed orders.
Includes order details, buyer/vendor information, payment proof, and delivery address.

Features:
- Professional invoice layout with TrustGuard branding
- Order details table (items, quantities, amounts)
- Buyer and vendor information
- Payment receipt reference
- Delivery address
- Transaction ID and timestamp
- Generated as BytesIO for direct S3 upload

Dependencies:
- reportlab: PDF generation library
"""

from io import BytesIO
from datetime import datetime
from typing import Dict, Any, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, Image, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from common.logger import logger


class OrderPDFGenerator:
    """
    Generates PDF summaries for TrustGuard orders.
    """
    
    def __init__(self):
        self.page_size = A4
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for PDF."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='SubTitle',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER,
            spaceAfter=20
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=10,
            spaceBefore=15
        ))
        
        # Info text style
        self.styles.add(ParagraphStyle(
            name='InfoText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#333333')
        ))
    
    def generate_order_pdf(
        self,
        order: Dict[str, Any],
        buyer: Dict[str, Any],
        vendor: Optional[Dict[str, Any]] = None,
        receipt_url: Optional[str] = None
    ) -> bytes:
        """
        Generate PDF summary for an order.
        
        Args:
            order: Order dictionary with order_id, items, total, status, etc.
            buyer: Buyer dictionary with name, phone, address
            vendor: Optional vendor dictionary with name, business_name
            receipt_url: Optional S3 presigned URL for payment receipt
        
        Returns:
            PDF bytes
        
        Example:
            >>> pdf_bytes = pdf_gen.generate_order_pdf(order, buyer, vendor, receipt_url)
            >>> # Upload to S3 or send to user
        """
        try:
            # Create BytesIO buffer
            buffer = BytesIO()
            
            # Create PDF document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=self.page_size,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build PDF content
            story = []
            
            # Header / Title
            story.append(Paragraph("TrustGuard", self.styles['CustomTitle']))
            story.append(Paragraph(
                "Secure E-Commerce Transaction Summary",
                self.styles['SubTitle']
            ))
            story.append(Spacer(1, 0.3 * inch))
            
            # Order Information Section
            story.append(Paragraph("Order Information", self.styles['SectionHeader']))
            
            order_id = order.get('order_id', 'N/A')
            created_at = order.get('created_at', datetime.now().isoformat())
            status = order.get('status', 'unknown').upper()
            currency = order.get('currency', 'NGN')
            total = order.get('total_amount', 0)
            
            # Format timestamp
            try:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                formatted_date = dt.strftime('%B %d, %Y at %I:%M %p')
            except:
                formatted_date = created_at
            
            order_info_data = [
                ['Order ID:', order_id],
                ['Date:', formatted_date],
                ['Status:', status],
                ['Total Amount:', f"{currency} {total:,.2f}"]
            ]
            
            order_info_table = Table(order_info_data, colWidths=[2 * inch, 4 * inch])
            order_info_table.setStyle(TableStyle([
                ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
                ('FONT', (1, 0), (1, -1), 'Helvetica', 10),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#555555')),
                ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#000000')),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
            ]))
            
            story.append(order_info_table)
            story.append(Spacer(1, 0.3 * inch))
            
            # Buyer Information Section
            story.append(Paragraph("Buyer Information", self.styles['SectionHeader']))
            
            buyer_name = buyer.get('name', 'N/A')
            buyer_phone = buyer.get('phone', 'N/A')
            buyer_address = buyer.get('delivery_address', 'Not provided')
            buyer_email = buyer.get('email', 'Not provided')
            
            buyer_info_data = [
                ['Name:', buyer_name],
                ['Phone:', buyer_phone],
                ['Email:', buyer_email],
                ['Delivery Address:', buyer_address]
            ]
            
            buyer_info_table = Table(buyer_info_data, colWidths=[2 * inch, 4 * inch])
            buyer_info_table.setStyle(TableStyle([
                ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
                ('FONT', (1, 0), (1, -1), 'Helvetica', 10),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#555555')),
                ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#000000')),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
            ]))
            
            story.append(buyer_info_table)
            story.append(Spacer(1, 0.3 * inch))
            
            # Vendor Information Section (if provided)
            if vendor:
                story.append(Paragraph("Vendor Information", self.styles['SectionHeader']))
                
                vendor_name = vendor.get('name', 'N/A')
                business_name = vendor.get('business_name', 'N/A')
                vendor_phone = vendor.get('phone', 'N/A')
                vendor_email = vendor.get('email', 'Not provided')
                
                vendor_info_data = [
                    ['Vendor Name:', vendor_name],
                    ['Business:', business_name],
                    ['Phone:', vendor_phone],
                    ['Email:', vendor_email]
                ]
                
                vendor_info_table = Table(vendor_info_data, colWidths=[2 * inch, 4 * inch])
                vendor_info_table.setStyle(TableStyle([
                    ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
                    ('FONT', (1, 0), (1, -1), 'Helvetica', 10),
                    ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#555555')),
                    ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#000000')),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
                ]))
                
                story.append(vendor_info_table)
                story.append(Spacer(1, 0.3 * inch))
            
            # Order Items Section
            items = order.get('items', [])
            if items:
                story.append(Paragraph("Order Items", self.styles['SectionHeader']))
                
                # Items table header
                items_data = [['Item', 'Quantity', 'Unit Price', 'Subtotal']]
                
                for item in items:
                    item_name = item.get('name', 'Unknown Item')
                    quantity = item.get('quantity', 1)
                    unit_price = item.get('unit_price', 0)
                    subtotal = quantity * unit_price
                    
                    items_data.append([
                        item_name,
                        str(quantity),
                        f"{currency} {unit_price:,.2f}",
                        f"{currency} {subtotal:,.2f}"
                    ])
                
                # Add total row
                items_data.append(['', '', 'TOTAL:', f"{currency} {total:,.2f}"])
                
                items_table = Table(items_data, colWidths=[2.5 * inch, 1 * inch, 1.5 * inch, 1.5 * inch])
                items_table.setStyle(TableStyle([
                    # Header style
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    
                    # Body style
                    ('FONT', (0, 1), (-1, -2), 'Helvetica', 9),
                    ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                    ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                    
                    # Total row style
                    ('FONT', (-2, -1), (-1, -1), 'Helvetica-Bold', 11),
                    ('BACKGROUND', (-2, -1), (-1, -1), colors.HexColor('#ecf0f1')),
                    
                    # Grid
                    ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
                    ('BOX', (0, 0), (-1, -1), 1, colors.black),
                    ('LINEABOVE', (-2, -1), (-1, -1), 2, colors.black),
                    
                    # Padding
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
                ]))
                
                story.append(items_table)
                story.append(Spacer(1, 0.3 * inch))
            
            # Payment Receipt Section
            if receipt_url:
                story.append(Paragraph("Payment Verification", self.styles['SectionHeader']))
                story.append(Paragraph(
                    f"Payment receipt uploaded and verified by vendor.",
                    self.styles['InfoText']
                ))
                story.append(Paragraph(
                    f"Receipt URL: {receipt_url[:80]}...",
                    self.styles['InfoText']
                ))
                story.append(Spacer(1, 0.2 * inch))
            
            # Footer
            story.append(Spacer(1, 0.5 * inch))
            story.append(Paragraph(
                "This is an automated transaction summary generated by TrustGuard.",
                self.styles['InfoText']
            ))
            story.append(Paragraph(
                f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p UTC')}",
                self.styles['InfoText']
            ))
            
            # Build PDF
            doc.build(story)
            
            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            logger.info("Order PDF generated successfully", extra={
                'order_id': order_id,
                'pdf_size_kb': len(pdf_bytes) / 1024
            })
            
            return pdf_bytes
        
        except Exception as e:
            logger.error(f"PDF generation failed: {str(e)}")
            raise


# Singleton instance
pdf_generator = OrderPDFGenerator()
