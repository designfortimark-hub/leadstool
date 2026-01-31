"""
Vercel serverless function for website vetting
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import VettingEngine

def handler(request):
    """Vercel serverless function handler"""
    try:
        # Parse request body - Vercel Python runtime provides request as dict
        if isinstance(request, dict):
            body = request.get('body', '{}')
            if isinstance(body, str):
                data = json.loads(body)
            else:
                data = body
        else:
            # Fallback for other formats
            body = getattr(request, 'body', b'{}')
            if isinstance(body, bytes):
                data = json.loads(body.decode('utf-8'))
            else:
                data = json.loads(body) if isinstance(body, str) else body
        
        url = data.get('url', '')
        if not url:
            raise ValueError("URL is required")
        
        vetter = VettingEngine()
        score, details, budget = vetter.analyze_site(url)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'score': score,
                'details': details,
                'budget': budget
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'success': False, 'error': str(e)})
        }
