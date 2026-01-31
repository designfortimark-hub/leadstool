"""
Vercel serverless function for Google Maps scraping
This is the API endpoint that can be called from a frontend
"""
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import run_google_maps_scraper, VettingEngine

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
        
        # Extract parameters
        keyword = data.get('keyword', '')
        location_input = data.get('location', '')
        latitude = float(data.get('latitude', 0))
        longitude = float(data.get('longitude', 0))
        zoom_level = int(data.get('zoom_level', 13))
        max_results = int(data.get('max_results', 5))
        reviews_threshold = int(data.get('reviews_threshold', 15))
        vetting_threshold = int(data.get('vetting_threshold', 50))
        use_scraper_api = data.get('use_scraper_api', False)
        
        # Create mock progress objects
        class MockProgress:
            def progress(self, value):
                pass
        
        class MockStatus:
            def text(self, value):
                pass
        
        progress_bar = MockProgress()
        status_text = MockStatus()
        
        api_key = os.getenv('SCRAPER_API_KEY', '') if use_scraper_api else None
        
        # Run scraper
        results = run_google_maps_scraper(
            keyword,
            location_input,
            latitude,
            longitude,
            zoom_level,
            max_results,
            progress_bar,
            status_text,
            reviews_threshold,
            vetting_threshold,
            use_scraper_api=use_scraper_api,
            api_key=api_key
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'success': True, 'data': results})
        }
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'success': False, 'error': error_msg})
        }
