import json
from auth_service import lambda_handler as auth_handler

def lambda_handler(event, context):
    """
    Central router for all API Gateway requests.
    Routes requests based on the path prefix to the appropriate service handler.
    """
    
    # Enable CORS for development/testing
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
    }

    # Handle OPTIONS pre-flight request for CORS
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    path = event.get('path', '')

    # Route to AuthServiceLambda
    if path.startswith('/auth'):
        # Pass the full event/context to the specific service handler
        response = auth_handler(event, context)
        # Add CORS headers to the service response
        response['headers'] = {**response.get('headers', {}), **headers}
        return response
    
    # TODO: Add routing for /receipt and /vendor paths later

    return {
        'statusCode': 404,
        'headers': headers,
        'body': json.dumps({'message': 'Service not found.'})
    }
