import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random
import re
import os
import json
import urllib.parse
from geopy.geocoders import Nominatim

# --- CONFIGURATION & HELPERS ---

def random_sleep(min_seconds=1, max_seconds=3):
    time.sleep(random.uniform(min_seconds, max_seconds))

def get_scraper_api_url(url, api_key=None):
    """Get ScraperAPI URL for headless browser scraping"""
    if not api_key:
        api_key = os.getenv('SCRAPER_API_KEY', '')
    
    if api_key:
        return f"http://api.scraperapi.com?api_key={api_key}&url={urllib.parse.quote(url)}&render=true"
    return url

def fetch_with_retry(url, max_retries=3, use_scraper_api=False, api_key=None):
    """Fetch URL with retry logic and optional ScraperAPI"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    if use_scraper_api:
        url = get_scraper_api_url(url, api_key)
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            if attempt < max_retries - 1:
                random_sleep(2, 5)
                continue
            raise e
    return None

# --- VETTING ENGINE ---

class VettingEngine:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def analyze_site(self, url):
        """
        Scrapes the website HTML to find 'Wealth Markers'.
        Returns a score and details.
        """
        score = 0
        details = []
        budget_potential = "Unknown"
        
        # Tags to look for
        wealth_markers = {
            'ads': [r'facebook\.com/tr', r'linkedin\.com/insight', r'adsbygoogle', r'google-analytics', r'googletagmanager'],
            'tech': [r'shopify', r'hubspot', r'salesforce', r'magento', r'woocommerce'],
            'keywords': [r'industrial', r'corporate', r'wholesale', r'enterprise', r'luxury', r'manufacturer', r'distributor']
        }
        
        low_budget_markers = [r'wix\.com', r'blogspot\.com', r'wordpress\.com', r'weebly\.com']

        try:
            response = requests.get(url, headers=self.headers, timeout=10, allow_redirects=True)
            html_content = response.text.lower()
        except Exception as e:
            return 0, ["Failed to access site"], "Unreachable"

        # Check Ads
        found_ads = [marker for marker in wealth_markers['ads'] if re.search(marker, html_content)]
        if found_ads:
            score += 40
            details.append(f"Ads Detected ({len(found_ads)})")

        # Check Tech
        found_tech = [marker for marker in wealth_markers['tech'] if re.search(marker, html_content)]
        if found_tech:
            score += 30
            details.append(f"Premium Tech ({len(found_tech)})")
        
        # Check Keywords
        found_kws = [kw for kw in wealth_markers['keywords'] if kw in html_content]
        if found_kws:
            score += 20
            details.append(f"High-Ticket Keywords ({len(found_kws)})")

        # Check Low Budget
        if any(re.search(lb, html_content) for lb in low_budget_markers):
            score -= 10
            details.append("Free/Page-Builder Detected")

        # Determine Budget Potential
        if score >= 50:
            budget_potential = "High (Target Met)"
        elif score >= 20:
            budget_potential = "Medium"
        else:
            budget_potential = "Low"

        return score, ", ".join(details), budget_potential

# --- SCRAPER LOGIC ---

def parse_google_maps_data(html_content, max_results):
    """Parse Google Maps HTML to extract business listings"""
    soup = BeautifulSoup(html_content, 'html.parser')
    leads = []
    
    # Try to find business listings in the HTML
    # Google Maps uses various selectors - we'll try multiple approaches
    listings = []
    
    # Method 1: Look for place links
    place_links = soup.find_all('a', href=re.compile(r'/maps/place/'))
    for link in place_links[:max_results]:
        name = link.get_text(strip=True) or link.get('aria-label', 'Unknown')
        if name and name != 'Unknown' and len(name) > 2:
            place_id_match = re.search(r'/place/([^/]+)', link.get('href', ''))
            place_id = place_id_match.group(1) if place_id_match else None
            
            if place_id:
                listings.append({
                    'name': name,
                    'place_id': place_id,
                    'url': link.get('href', '')
                })
    
    # Method 2: Look for JSON-LD structured data
    json_scripts = soup.find_all('script', type='application/ld+json')
    for script in json_scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and data.get('@type') == 'LocalBusiness':
                listings.append({
                    'name': data.get('name', 'Unknown'),
                    'phone': data.get('telephone', 'N/A'),
                    'website': data.get('url', 'N/A'),
                    'rating': str(data.get('aggregateRating', {}).get('ratingValue', '0')),
                    'reviews': data.get('aggregateRating', {}).get('reviewCount', 0)
                })
        except:
            continue
    
    # Method 3: Extract from inline JSON data
    inline_scripts = soup.find_all('script')
    for script in inline_scripts:
        if script.string and 'window.APP_INITIALIZATION_STATE' in script.string:
            try:
                # Extract JSON data from Google Maps initialization
                json_match = re.search(r'\[null,null,\[\["([^"]+)"', script.string)
                if json_match:
                    # This is a simplified extraction - Google Maps uses complex nested JSON
                    pass
            except:
                continue
    
    return listings

def run_google_maps_scraper(keyword, search_location, latitude, longitude, zoom_level, max_results, progress_bar, status_text, reviews_threshold, vetting_threshold, use_api=False, api_key=None):
    """Main scraper function - now Vercel compatible"""
    leads = []
    vetter = VettingEngine()
    
    try:
        query = f"{keyword} in {search_location}"
        status_text.text(f"Searching for: {query} near ({latitude}, {longitude})")
        
        # Build Google Maps search URL
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.google.com/maps/search/{encoded_query}/@{latitude},{longitude},{zoom_level}z"
        
        # Fetch the page
        status_text.text("Fetching Google Maps data...")
        html_content = fetch_with_retry(url, use_scraper_api=use_api, api_key=api_key)
        
        if not html_content:
            status_text.text("Failed to fetch Google Maps. Consider using ScraperAPI or Google Maps Places API.")
            return []
        
        # Parse the HTML
        status_text.text("Parsing results...")
        parsed_listings = parse_google_maps_data(html_content, max_results)
        
        if not parsed_listings:
            # Fallback: Use Google Maps Places API if available
            places_api_key = os.getenv('GOOGLE_MAPS_API_KEY', '')
            if places_api_key:
                return fetch_from_places_api(keyword, latitude, longitude, max_results, reviews_threshold, vetting_threshold, vetter, status_text, progress_bar)
            else:
                status_text.text("No listings found. Google Maps may require JavaScript rendering. Consider using ScraperAPI or Google Maps Places API.")
                return []
        
        progress_step = 1.0 / len(parsed_listings) if parsed_listings else 0
        current_progress = 0.0
        
        for i, listing in enumerate(parsed_listings):
            try:
                name = listing.get('name', 'Unknown')
                
                # Try to get more details by fetching the place page
                phone = listing.get('phone', 'N/A')
                website = listing.get('website', 'N/A')
                rating = listing.get('rating', '0')
                reviews_count = listing.get('reviews', 0)
                
                # If we have a place URL, try to get more details
                if listing.get('url') and website == 'N/A':
                    place_url = f"https://www.google.com{listing['url']}" if listing['url'].startswith('/') else listing['url']
                    try:
                        place_html = fetch_with_retry(place_url, use_scraper_api=use_api, api_key=api_key)
                        if place_html:
                            place_soup = BeautifulSoup(place_html, 'html.parser')
                            
                            # Extract phone
                            if phone == 'N/A':
                                phone_elem = place_soup.find('button', attrs={'data-item-id': re.compile(r'phone:')})
                                if phone_elem:
                                    phone = phone_elem.get('aria-label', 'N/A').replace('Phone: ', '').strip()
                            
                            # Extract website
                            if website == 'N/A':
                                website_elem = place_soup.find('a', attrs={'data-item-id': 'authority'})
                                if website_elem:
                                    website = website_elem.get('href', 'N/A')
                            
                            # Extract rating and reviews
                            rating_elem = place_soup.find('span', attrs={'role': 'img', 'aria-label': re.compile(r'stars')})
                            if rating_elem:
                                rating = rating_elem.get('aria-label', '0').split(' ')[0]
                            
                            reviews_elem = place_soup.find('button', attrs={'aria-label': re.compile(r'reviews')})
                            if reviews_elem:
                                reviews_text = reviews_elem.get('aria-label', '0')
                                reviews_match = re.search(r'(\d+)', reviews_text.replace(',', ''))
                                if reviews_match:
                                    reviews_count = int(reviews_match.group(1))
                    except:
                        pass
                
                # Determine claimed status (heuristic)
                is_claimed = "Claimed" if website != "N/A" or reviews_count > 0 else "Unclaimed"
                
                # Lead filtering
                lead_status = "Standard"
                if reviews_count < reviews_threshold or is_claimed == "Unclaimed":
                    lead_status = "High Priority New Lead"
                
                # Vetting
                vetting_score = 0
                vetting_details = ""
                budget = "N/A"
                
                if website != "N/A":
                    vetting_score, vetting_details, _ = vetter.analyze_site(website)
                    
                    if vetting_score >= vetting_threshold:
                        budget = "High (Target Met)"
                    elif vetting_score >= (vetting_threshold / 2):
                        budget = "Medium"
                    else:
                        budget = "Low"
                
                lead = {
                    "Name": name,
                    "Phone": phone,
                    "Website": website,
                    "Reviews": reviews_count,
                    "Rating": rating,
                    "Status": is_claimed,
                    "Lead Type": lead_status,
                    "Vetting Score": vetting_score,
                    "Markers": vetting_details,
                    "Est. Budget": budget
                }
                leads.append(lead)
                
                current_progress += progress_step
                if progress_bar:
                    progress_bar.progress(min(current_progress, 1.0))
                status_text.text(f"Processed: {name}")
                
            except Exception as e:
                print(f"Error processing listing {i}: {e}")
                continue
        
    except Exception as e:
        st.error(f"Critical Scraper Error: {e}")
        import traceback
        st.code(traceback.format_exc())
    
    return leads

def fetch_from_places_api(keyword, latitude, longitude, max_results, reviews_threshold, vetting_threshold, vetter, status_text, progress_bar):
    """Fallback: Use Google Maps Places API"""
    api_key = os.getenv('GOOGLE_MAPS_API_KEY', '')
    if not api_key:
        return []
    
    try:
        # Use Places API Text Search
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            'query': keyword,
            'location': f"{latitude},{longitude}",
            'radius': 5000,
            'key': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get('status') != 'OK':
            return []
        
        leads = []
        places = data.get('results', [])[:max_results]
        progress_step = 1.0 / len(places) if places else 0
        current_progress = 0.0
        
        for place in places:
            name = place.get('name', 'Unknown')
            rating = str(place.get('rating', 0))
            reviews_count = place.get('user_ratings_total', 0)
            phone = 'N/A'
            website = 'N/A'
            
            # Get place details for phone and website
            place_id = place.get('place_id')
            if place_id:
                details_url = "https://maps.googleapis.com/maps/api/place/details/json"
                details_params = {
                    'place_id': place_id,
                    'fields': 'formatted_phone_number,website',
                    'key': api_key
                }
                details_response = requests.get(details_url, params=details_params, timeout=10)
                details_data = details_response.json()
                if details_data.get('status') == 'OK':
                    result = details_data.get('result', {})
                    phone = result.get('formatted_phone_number', 'N/A')
                    website = result.get('website', 'N/A')
            
            is_claimed = "Claimed" if website != "N/A" or reviews_count > 0 else "Unclaimed"
            lead_status = "Standard"
            if reviews_count < reviews_threshold or is_claimed == "Unclaimed":
                lead_status = "High Priority New Lead"
            
            vetting_score = 0
            vetting_details = ""
            budget = "N/A"
            
            if website != "N/A":
                vetting_score, vetting_details, _ = vetter.analyze_site(website)
                if vetting_score >= vetting_threshold:
                    budget = "High (Target Met)"
                elif vetting_score >= (vetting_threshold / 2):
                    budget = "Medium"
                else:
                    budget = "Low"
            
            lead = {
                "Name": name,
                "Phone": phone,
                "Website": website,
                "Reviews": reviews_count,
                "Rating": rating,
                "Status": is_claimed,
                "Lead Type": lead_status,
                "Vetting Score": vetting_score,
                "Markers": vetting_details,
                "Est. Budget": budget
            }
            leads.append(lead)
            
            current_progress += progress_step
            if progress_bar:
                progress_bar.progress(min(current_progress, 1.0))
            status_text.text(f"Processed: {name}")
        
        return leads
    except Exception as e:
        st.error(f"Places API Error: {e}")
        return []

# --- UI LAYOUT ---

def main():
    st.set_page_config(page_title="Local Maps Leads Pro", layout="wide", page_icon="🗺️")
    
    st.title("🗺️ Local Maps Leads Scraper & Vetting Tool")
    st.markdown("---")
    
    # API Configuration Info
    with st.expander("🔧 API Configuration (Optional but Recommended)"):
        st.info("""
        **For best results, configure one of these:**
        
        1. **ScraperAPI** (Recommended for web scraping):
           - Get free API key at https://www.scraperapi.com
           - Set environment variable: `SCRAPER_API_KEY`
        
        2. **Google Maps Places API** (Most reliable):
           - Enable Places API in Google Cloud Console
           - Get API key and set: `GOOGLE_MAPS_API_KEY`
           - More accurate data but requires billing setup
        """)
    
    # Sidebar
    st.sidebar.header("Configuration")
    
    st.sidebar.subheader("Filter & Budget Settings")
    reviews_threshold = st.sidebar.slider("New Lead Definition (Max Reviews)", 0, 100, 15, help="Businesses with fewer reviews than this are marked 'High Priority'.")
    vetting_threshold = st.sidebar.slider("High Budget Score Threshold", 0, 100, 50, help="Websites with a vetting score above this are marked 'High Budget'.")
    only_no_website = st.sidebar.checkbox("Only Show Leads Without Websites", help="Useful for selling web design services.")
    
    use_scraper_api = st.sidebar.checkbox("Use ScraperAPI (if configured)", value=False, help="Enable if you have SCRAPER_API_KEY set")
    
    with st.sidebar.form("search_form"):
        keyword = st.text_input("Industry / Keyword", "")
        
        st.markdown("### Location Settings")
        location_input = st.text_input("Center Address / City", "")
        radius_km = st.slider("Search Radius (Approx. km)", 1, 100, 10, help="Controls the initial map zoom level.")
        
        max_results = st.number_input("Max Results", min_value=1, max_value=50, value=5)
        
        submitted = st.form_submit_button("Start Scraping")
    
    st.sidebar.markdown("---")
    st.sidebar.info("💡 **Tip**: For best results, use Google Maps Places API or ScraperAPI")
    
    # Main Area
    if submitted:
        if not keyword or not location_input:
            st.error("Please enter both keyword and location.")
        else:
            # Geocoding
            try:
                geolocator = Nominatim(user_agent="maps_scraper_app_v1", timeout=10)
                location_data = geolocator.geocode(location_input)
                
                if not location_data:
                    st.error(f"Could not find coordinates for: {location_input}")
                else:
                    lat = location_data.latitude
                    lon = location_data.longitude
                    
                    st.success(f"📍 Found Location: {location_data.address} ({lat}, {lon})")
                    
                    # Convert Radius to Zoom Level
                    if radius_km <= 2: zoom = 15
                    elif radius_km <= 5: zoom = 14
                    elif radius_km <= 15: zoom = 13
                    elif radius_km <= 40: zoom = 12
                    elif radius_km <= 100: zoom = 10
                    else: zoom = 8

            except Exception as e:
                st.error(f"Geocoding Error: {e}")
                location_data = None

            if location_data:
                try:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    api_key = os.getenv('SCRAPER_API_KEY', '') if use_scraper_api else None
                    
                    with st.spinner("Scraping Google Maps... (This may take a moment)"):
                        data = run_google_maps_scraper(
                            keyword, 
                            location_input, 
                            lat, lon, zoom, 
                            max_results, 
                            progress_bar, 
                            status_text, 
                            reviews_threshold, 
                            vetting_threshold,
                            use_scraper_api=use_scraper_api,
                            api_key=api_key
                        )

                    if data:
                        st.success(f"Scraping Completed! Found {len(data)} leads.")
                        
                        df = pd.DataFrame(data)
                        
                        # Apply Filters
                        if only_no_website:
                            df = df[df['Website'] == "N/A"]
                            st.info(f"Filtered to {len(df)} leads without websites.")
                        
                        # Metric Cards
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Total Leads", len(df))
                        c2.metric("High Priority", len(df[df['Lead Type'] == "High Priority New Lead"]))
                        c3.metric("Sites Vetted", len(df[df['Website'] != "N/A"]))
                        
                        st.dataframe(df, use_container_width=True)
                        
                        # Export
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="Download Results (CSV)",
                            data=csv,
                            file_name=f"leads_{keyword}_{location_input}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.warning("No leads found. Try:")
                        st.markdown("""
                        - Using Google Maps Places API (most reliable)
                        - Using ScraperAPI for JavaScript rendering
                        - Adjusting your search terms or location
                        - Increasing wait times
                        """)
                
                except Exception as e:
                    import traceback
                    st.error(f"Execution Error: {e}")
                    st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
