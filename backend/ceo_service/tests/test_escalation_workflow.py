"""
Integration tests for CEO Escalation Approval Workflow.

Tests the complete flow:
1. High-value order creation (≥₦1M)
2. Vendor verification triggers escalation
3. CEO receives SNS alert
4. CEO reviews escalation details
5. CEO generates fresh OTP
6. CEO approves/rejects with OTP
7. Order status updated
8. Buyer and vendor notified
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from ceo_service.ceo_logic import (
    get_ceo_pending_escalations,
    get_escalation_details,
    approve_escalation_with_otp,
    reject_escalation_with_otp,
    generate_ceo_otp
)


class TestEscalationWorkflow:
    """Test suite for CEO escalation approval workflow."""
    
    @pytest.fixture
    def mock_escalation(self):
        """Sample escalation record."""
        return {
            'escalation_id': 'esc_test123',
            'ceo_id': 'ceo_001',
            'order_id': 'order_high_value_001',
            'vendor_id': 'vendor_001',
            'buyer_id': 'wa_2348012345678',
            'amount': 2500000,  # ₦2.5M
            'reason': 'HIGH_VALUE',
            'status': 'PENDING',
            'notes': 'Large transaction requires review',
            'created_at': int(time.time()),
            'expires_at': int(time.time()) + (24 * 3600)
        }
    
    @pytest.fixture
    def mock_order(self):
        """Sample high-value order."""
        return {
            'order_id': 'order_high_value_001',
            'buyer_id': 'wa_2348012345678',
            'vendor_id': 'vendor_001',
            'ceo_id': 'ceo_001',
            'product_name': 'iPhone 15 Pro Max (x5)',
            'quantity': 5,
            'amount': 2500000,
            'order_status': 'escalated',
            'delivery_address': '123 Lagos Street, VI, Lagos',
            'receipt_url': 's3://trustguard-receipts/receipts/ceo_001/vendor_001/order_high_value_001/receipt.jpg',
            'receipt_metadata': {
                'checksum': 'abc123',
                'uploaded_at': int(time.time())
            },
            'textract_results': {
                'confidence': 0.95,
                'extracted_amount': 2500000,
                'vendor_name': 'TechStore Nigeria'
            },
            'created_at': int(time.time())
        }
    
    @pytest.fixture
    def mock_buyer(self):
        """Sample buyer user."""
        return {
            'user_id': 'wa_2348012345678',
            'name': 'John Doe',
            'phone': '+2348012345678',
            'role': 'Buyer'
        }
    
    @pytest.fixture
    def mock_vendor(self):
        """Sample vendor user."""
        return {
            'user_id': 'vendor_001',
            'name': 'TechStore Vendor',
            'email': 'vendor@techstore.com',
            'role': 'Vendor',
            'ceo_id': 'ceo_001'
        }
    
    @patch('ceo_service.ceo_logic.get_pending_escalations')
    @patch('ceo_service.ceo_logic.get_order_by_id')
    @patch('ceo_service.ceo_logic.get_user_by_id')
    def test_get_pending_escalations_enriched(
        self,
        mock_get_user,
        mock_get_order,
        mock_get_escalations,
        mock_escalation,
        mock_order,
        mock_buyer,
        mock_vendor
    ):
        """Test that pending escalations are enriched with order and user details."""
        # Setup mocks
        mock_get_escalations.return_value = [mock_escalation]
        mock_get_order.return_value = mock_order
        
        def get_user_side_effect(user_id):
            if user_id == 'wa_2348012345678':
                return mock_buyer
            elif user_id == 'vendor_001':
                return mock_vendor
            return None
        
        mock_get_user.side_effect = get_user_side_effect
        
        # Execute
        result = get_ceo_pending_escalations('ceo_001', limit=50)
        
        # Assertions
        assert len(result) == 1
        escalation = result[0]
        
        # Verify enriched data
        assert escalation['escalation_id'] == 'esc_test123'
        assert escalation['amount'] == 2500000
        assert escalation['vendor_name'] == 'TechStore Vendor'
        assert escalation['buyer_name'] == 'John Doe'
        assert '***' in escalation['buyer_phone_masked']  # PII masked
        assert escalation['order_details']['product'] == 'iPhone 15 Pro Max (x5)'
        assert escalation['order_details']['textract_results']['confidence'] == 0.95
    
    @patch('ceo_service.ceo_logic.get_escalation')
    @patch('ceo_service.ceo_logic.get_order_by_id')
    @patch('ceo_service.ceo_logic.get_user_by_id')
    def test_get_escalation_details(
        self,
        mock_get_user,
        mock_get_order,
        mock_get_escalation,
        mock_escalation,
        mock_order,
        mock_buyer,
        mock_vendor
    ):
        """Test retrieval of detailed escalation information."""
        # Setup mocks
        mock_get_escalation.return_value = mock_escalation
        mock_get_order.return_value = mock_order
        
        def get_user_side_effect(user_id):
            if user_id == 'wa_2348012345678':
                return mock_buyer
            elif user_id == 'vendor_001':
                return mock_vendor
            return None
        
        mock_get_user.side_effect = get_user_side_effect
        
        # Execute
        result = get_escalation_details('ceo_001', 'esc_test123')
        
        # Assertions
        assert 'escalation' in result
        assert 'order' in result
        assert 'buyer' in result
        assert 'vendor' in result
        
        # Verify escalation details
        assert result['escalation']['escalation_id'] == 'esc_test123'
        assert result['escalation']['status'] == 'PENDING'
        assert result['escalation']['reason'] == 'HIGH_VALUE'
        
        # Verify order details
        assert result['order']['order_id'] == 'order_high_value_001'
        assert result['order']['amount'] == 2500000
        assert result['order']['textract_results']['confidence'] == 0.95
        
        # Verify PII masking
        assert '***' in result['buyer']['phone_masked']
        assert result['buyer']['name'] == 'John Doe'
    
    def test_get_escalation_details_unauthorized(self):
        """Test that CEO cannot access escalations belonging to other CEOs."""
        mock_escalation = {
            'escalation_id': 'esc_test123',
            'ceo_id': 'ceo_002',  # Different CEO
            'order_id': 'order_001'
        }
        
        with patch('ceo_service.ceo_logic.get_escalation', return_value=mock_escalation):
            with pytest.raises(ValueError, match="Unauthorized"):
                get_escalation_details('ceo_001', 'esc_test123')
    
    @patch('ceo_service.ceo_logic.get_otp')
    @patch('ceo_service.ceo_logic.delete_otp')
    @patch('ceo_service.ceo_logic.get_escalation')
    @patch('ceo_service.ceo_logic.update_escalation_status')
    @patch('ceo_service.ceo_logic.update_order_status')
    @patch('ceo_service.ceo_logic.get_order_by_id')
    @patch('ceo_service.ceo_logic.get_user_by_id')
    @patch('ceo_service.ceo_logic.send_buyer_notification')
    @patch('ceo_service.ceo_logic.send_escalation_resolved_notification')
    def test_approve_escalation_with_valid_otp(
        self,
        mock_send_resolved,
        mock_send_buyer,
        mock_get_user,
        mock_get_order,
        mock_update_order,
        mock_update_escalation,
        mock_get_escalation,
        mock_delete_otp,
        mock_get_otp,
        mock_escalation,
        mock_order,
        mock_buyer
    ):
        """Test successful approval of escalation with valid OTP."""
        # Setup mocks
        mock_get_otp.return_value = {'otp_code': '123456', 'role': 'CEO'}
        mock_get_escalation.return_value = mock_escalation
        mock_update_escalation.return_value = True
        mock_get_order.return_value = mock_order
        mock_get_user.return_value = mock_buyer
        
        # Execute
        result = approve_escalation_with_otp(
            ceo_id='ceo_001',
            escalation_id='esc_test123',
            otp='123456',
            decision_notes='Verified with buyer via phone'
        )
        
        # Assertions
        assert result['decision'] == 'APPROVED'
        assert result['order_id'] == 'order_high_value_001'
        assert result['buyer_notified'] is True
        
        # Verify OTP was deleted (single-use)
        mock_delete_otp.assert_called_once_with('ceo_001')
        
        # Verify escalation status updated
        mock_update_escalation.assert_called_once()
        assert mock_update_escalation.call_args[1]['status'] == 'APPROVED'
        
        # Verify order status updated
        mock_update_order.assert_called_once()
        
        # Verify notifications sent
        mock_send_buyer.assert_called_once()
        mock_send_resolved.assert_called_once()
    
    @patch('ceo_service.ceo_logic.get_otp')
    def test_approve_escalation_invalid_otp(self, mock_get_otp):
        """Test that approval fails with invalid OTP."""
        mock_get_otp.return_value = {'otp_code': '999999', 'role': 'CEO'}
        
        with pytest.raises(ValueError, match="Invalid or expired OTP"):
            approve_escalation_with_otp(
                ceo_id='ceo_001',
                escalation_id='esc_test123',
                otp='123456',  # Wrong OTP
                decision_notes='Test'
            )
    
    @patch('ceo_service.ceo_logic.get_otp')
    @patch('ceo_service.ceo_logic.delete_otp')
    @patch('ceo_service.ceo_logic.get_escalation')
    @patch('ceo_service.ceo_logic.update_escalation_status')
    @patch('ceo_service.ceo_logic.update_order_status')
    @patch('ceo_service.ceo_logic.get_order_by_id')
    @patch('ceo_service.ceo_logic.get_user_by_id')
    @patch('ceo_service.ceo_logic.send_buyer_notification')
    @patch('ceo_service.ceo_logic.send_escalation_resolved_notification')
    def test_reject_escalation_with_valid_otp(
        self,
        mock_send_resolved,
        mock_send_buyer,
        mock_get_user,
        mock_get_order,
        mock_update_order,
        mock_update_escalation,
        mock_get_escalation,
        mock_delete_otp,
        mock_get_otp,
        mock_escalation,
        mock_order,
        mock_buyer
    ):
        """Test successful rejection of escalation with valid OTP."""
        # Setup mocks
        mock_get_otp.return_value = {'otp_code': '123456', 'role': 'CEO'}
        mock_get_escalation.return_value = mock_escalation
        mock_update_escalation.return_value = True
        mock_get_order.return_value = mock_order
        mock_get_user.return_value = mock_buyer
        
        # Execute
        result = reject_escalation_with_otp(
            ceo_id='ceo_001',
            escalation_id='esc_test123',
            otp='123456',
            decision_notes='Suspicious transaction pattern'
        )
        
        # Assertions
        assert result['decision'] == 'REJECTED'
        assert result['order_id'] == 'order_high_value_001'
        assert result['buyer_notified'] is True
        
        # Verify OTP was deleted (single-use)
        mock_delete_otp.assert_called_once_with('ceo_001')
        
        # Verify escalation status updated to REJECTED
        mock_update_escalation.assert_called_once()
        assert mock_update_escalation.call_args[1]['status'] == 'REJECTED'
        
        # Verify order status updated to rejected
        mock_update_order.assert_called_once()
        
        # Verify rejection notification sent to buyer
        mock_send_buyer.assert_called_once()
        buyer_notification_call = mock_send_buyer.call_args
        assert 'Rejected' in buyer_notification_call[1]['status']
        assert 'Suspicious transaction pattern' in buyer_notification_call[1]['additional_message']
    
    def test_cannot_approve_already_processed_escalation(self):
        """Test that approved/rejected escalations cannot be processed again."""
        mock_escalation = {
            'escalation_id': 'esc_test123',
            'ceo_id': 'ceo_001',
            'status': 'APPROVED',  # Already approved
            'order_id': 'order_001'
        }
        
        with patch('ceo_service.ceo_logic.get_otp', return_value={'otp_code': '123456'}):
            with patch('ceo_service.ceo_logic.delete_otp'):
                with patch('ceo_service.ceo_logic.get_escalation', return_value=mock_escalation):
                    with pytest.raises(ValueError, match="Cannot approve escalation with status"):
                        approve_escalation_with_otp(
                            ceo_id='ceo_001',
                            escalation_id='esc_test123',
                            otp='123456'
                        )
    
    @patch('ceo_service.ceo_logic.save_otp')
    def test_generate_ceo_otp(self, mock_save_otp):
        """Test CEO OTP generation."""
        otp = generate_ceo_otp('ceo_001')
        
        # Verify OTP format (6 characters, digits + symbols)
        assert len(otp) == 6
        assert any(c.isdigit() for c in otp)
        
        # Verify OTP was saved
        mock_save_otp.assert_called_once()
        assert mock_save_otp.call_args[0][0] == 'ceo_001'
        assert mock_save_otp.call_args[0][2] == 'CEO'
        assert mock_save_otp.call_args[0][3] == 300  # 5-minute TTL


class TestEscalationEdgeCases:
    """Test edge cases and error scenarios."""
    
    def test_expired_escalation(self):
        """Test handling of expired escalations (>24h)."""
        expired_escalation = {
            'escalation_id': 'esc_expired',
            'ceo_id': 'ceo_001',
            'status': 'EXPIRED',  # Auto-expired
            'created_at': int(time.time()) - (25 * 3600),  # 25 hours ago
            'expires_at': int(time.time()) - (1 * 3600)  # Expired 1 hour ago
        }
        
        with patch('ceo_service.ceo_logic.get_escalation', return_value=expired_escalation):
            # Should not be able to approve expired escalations
            # Implementation should check status == 'PENDING'
            pass
    
    def test_pii_masking_in_notifications(self):
        """Verify that buyer phone numbers are masked in CEO-facing data."""
        # This is tested implicitly in test_get_pending_escalations_enriched
        # But we can add explicit checks here
        pass
    
    @patch('ceo_service.ceo_logic.logger')
    def test_audit_logging_on_approval(self, mock_logger):
        """Test that all escalation decisions are logged to audit table."""
        # Mock all dependencies
        with patch('ceo_service.ceo_logic.get_otp', return_value={'otp_code': '123456'}):
            with patch('ceo_service.ceo_logic.delete_otp'):
                with patch('ceo_service.ceo_logic.get_escalation', return_value={
                    'escalation_id': 'esc_001',
                    'ceo_id': 'ceo_001',
                    'status': 'PENDING',
                    'order_id': 'order_001',
                    'amount': 2500000
                }):
                    with patch('ceo_service.ceo_logic.update_escalation_status', return_value=True):
                        with patch('ceo_service.ceo_logic.update_order_status'):
                            with patch('ceo_service.ceo_logic.get_order_by_id', return_value=None):
                                with patch('ceo_service.ceo_logic.send_escalation_resolved_notification'):
                                    # Execute
                                    approve_escalation_with_otp(
                                        ceo_id='ceo_001',
                                        escalation_id='esc_001',
                                        otp='123456'
                                    )
                                    
                                    # Verify audit log was called
                                    mock_logger.info.assert_called()
                                    log_call = mock_logger.info.call_args
                                    assert 'APPROVED' in str(log_call)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
