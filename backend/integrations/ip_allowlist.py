"""
IP Allowlisting Utilities

Validates that incoming requests originate from trusted IP addresses.
Used for webhook security to ensure only Meta's servers can send webhooks.
"""

import ipaddress
from typing import List
from common.logger import logger


def is_ip_allowed(client_ip: str, allowed_ranges: List[str]) -> bool:
    """
    Check if client IP is within allowed IP ranges.
    
    Args:
        client_ip: Client IP address (e.g., "173.252.88.100")
        allowed_ranges: List of CIDR ranges (e.g., ["173.252.88.0/21"])
    
    Returns:
        bool: True if IP is allowed
    
    Example:
        >>> is_ip_allowed("173.252.88.100", ["173.252.88.0/21"])
        True
        >>> is_ip_allowed("1.2.3.4", ["173.252.88.0/21"])
        False
    """
    try:
        client_addr = ipaddress.ip_address(client_ip)
        
        for cidr_range in allowed_ranges:
            network = ipaddress.ip_network(cidr_range, strict=False)
            if client_addr in network:
                logger.debug(
                    f"IP {client_ip} allowed (matches {cidr_range})",
                    extra={'client_ip': client_ip, 'matched_range': cidr_range}
                )
                return True
        
        logger.warning(
            f"IP {client_ip} not in allowed ranges",
            extra={'client_ip': client_ip, 'allowed_ranges': allowed_ranges}
        )
        return False
    
    except ValueError as e:
        logger.error(f"Invalid IP address: {client_ip} - {str(e)}")
        return False


def get_client_ip(request) -> str:
    """
    Extract client IP from request, handling proxies and load balancers.
    
    Checks headers in order:
    1. X-Forwarded-For (most common for proxies)
    2. X-Real-IP (nginx)
    3. request.client.host (direct connection)
    
    Args:
        request: FastAPI Request object
    
    Returns:
        str: Client IP address
    """
    # Check X-Forwarded-For header (proxy/load balancer)
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs: "client, proxy1, proxy2"
        # Take the first one (original client)
        client_ip = forwarded_for.split(',')[0].strip()
        logger.debug(f"Client IP from X-Forwarded-For: {client_ip}")
        return client_ip
    
    # Check X-Real-IP header (nginx)
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        logger.debug(f"Client IP from X-Real-IP: {real_ip}")
        return real_ip
    
    # Direct connection
    if request.client:
        client_ip = request.client.host
        logger.debug(f"Client IP from request.client: {client_ip}")
        return client_ip
    
    logger.warning("Could not determine client IP")
    return "unknown"
