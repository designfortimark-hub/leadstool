import streamlit as st
import pandas as pd
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from bs4 import BeautifulSoup
import time
import random
import re
import os
import sys
import asyncio

# Fix for Windows Event Loop Policy
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from geopy.geocoders import Nominatim

# --- CONFIGURATION & HELPERS ---

def random_sleep(min_seconds=2, max_seconds=5):
    """Human-like random sleep"""
    time.sleep(random.uniform(min_seconds, max_seconds))

def human_scroll(page, scroll_box_selector, scrolls=3):
    """Simulates human-like scrolling"""
    try:
        for i in range(scrolls):
            page.hover(scroll_box_selector)
            # Random scroll amount
            scroll_amount = random.randint(300, 800)
            page.mouse.wheel(0, scroll_amount)
            random_sleep(1, 3)
    except:
        pass

# --- VETTING ENGINE ---

class VettingEngine:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def analyze_site(self, url):
        """Analyzes website for wealth markers"""
        score = 0
        details = []
        budget_potential = "Unknown"
        
        wealth_markers = {
            'ads': [r'facebook\.com/tr', r'linkedin\.com/insight', r'adsbygoogle', r'google-analytics', r'googletagmanager'],
            'tech': [r'shopify', r'hubspot', r'salesforce', r'magento', r'woocommerce'],
            'keywords': [r'industrial', r'corporate', r'wholesale', r'enterprise', r'luxury', r'manufacturer', r'distributor']
        }
        
        low_budget_markers = [r'wix\.com', r'blogspot\.com', r'wordpress\.com', r'weebly\.com']

        try:
            import requests
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

# --- SCRAPER LOGIC WITH PLAYWRIGHT (HUMAN-LIKE) ---

def run_google_maps_scraper(keyword, search_location, latitude, longitude, zoom_level, max_results, progress_bar, status_text, reviews_threshold, vetting_threshold):
    """Scrapes Google Maps using Playwright with stealth - acts like a human"""
    leads = []
    
    with sync_playwright() as p:
        # Launch browser with human-like settings
        browser = p.chromium.launch(
            headless=True,  # Set to False to see the browser
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox"
            ]
        )
        
        # Create context with realistic settings
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            geolocation={'latitude': latitude, 'longitude': longitude},
            permissions=['geolocation'],
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # Apply stealth to avoid detection
        stealth_sync(context)
        
        page = context.new_page()
        
        try:
            query = f"{keyword} in {search_location}"
            status_text.text(f"🔍 Searching for: {query} near ({latitude}, {longitude})")
            
            # Build Google Maps URL
            import urllib.parse
            encoded_query = urllib.parse.quote(query)
            url = f"https://www.google.com/maps/search/{encoded_query}/@{latitude},{longitude},{zoom_level}z"
            
            status_text.text("🌐 Opening Google Maps (acting like a human browser)...")
            page.goto(url, timeout=60000, wait_until='networkidle')
            
            # Human-like wait
            random_sleep(3, 5)
            
            # Wait for results feed
            try:
                page.wait_for_selector('div[role="feed"]', timeout=15000)
                status_text.text("✅ Found results feed, scrolling to load more...")
            except:
                status_text.text("⚠️ Could not find results feed. Trying to continue...")
            
            # Human-like scrolling to load results
            feed_selector = 'div[role="feed"]'
            listing_selector = 'a[href^="https://www.google.com/maps/place"]'
            
            found_count = 0
            retries = 0
            max_retries = 5
            
            status_text.text("📜 Scrolling to load listings (human-like behavior)...")
            
            while found_count < max_results and retries < max_retries:
                listings = page.locator(listing_selector).all()
                found_count = len(listings)
                status_text.text(f"📊 Found {found_count} listings so far...")
                
                if found_count >= max_results:
                    break
                
                # Human-like scroll
                human_scroll(page, feed_selector, scrolls=2)
                random_sleep(2, 4)
                
                # Check if new listings appeared
                new_listings = page.locator(listing_selector).all()
                if len(new_listings) == found_count:
                    retries += 1
                else:
                    retries = 0
            
            # Get the listings
            listings = page.locator(listing_selector).all()[:max_results]
            status_text.text(f"✅ Found {len(listings)} listings. Extracting details...")
            
            vetter = VettingEngine()
            progress_step = 1.0 / len(listings) if listings else 0
            current_progress = 0.0

            for i, listing in enumerate(listings):
                try:
                    # Scroll listing into view (human-like)
                    listing.scroll_into_view_if_needed()
                    random_sleep(1, 2)
                    
                    # Get name from listing
                    name = listing.get_attribute("aria-label")
                    if not name or name == "Results":
                        name = listing.inner_text() or "Unknown"
                    name = name.strip()
                    
                    if not name or name == "Unknown":
                        continue
                    
                    status_text.text(f"🔎 Processing: {name} ({i+1}/{len(listings)})")
                    
                    # Click to open details (human-like)
                    listing.click()
                    random_sleep(2, 4)  # Human wait time
                    
                    # Wait for detail pane to load
                    try:
                        page.wait_for_selector('div[role="main"]', timeout=5000)
                    except:
                        pass
                    
                    # Get page content
                    content = page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Extract phone
                    phone_btn = soup.find('button', attrs={'data-item-id': re.compile(r'phone:')})
                    phone = phone_btn['aria-label'].replace("Phone: ", "").strip() if phone_btn else "N/A"
                    
                    # Extract website
                    website_btn = soup.find('a', attrs={'data-item-id': "authority"})
                    website = website_btn['href'] if website_btn else "N/A"
                    
                    # Extract rating
                    rating_span = soup.find('span', attrs={'role': 'img', 'aria-label': re.compile(r'stars')})
                    rating = rating_span['aria-label'].split(" ")[0] if rating_span else "0"
                    
                    # Extract reviews count
                    reviews_btn = soup.find('button', attrs={'aria-label': re.compile(r'reviews')})
                    reviews_text = reviews_btn['aria-label'] if reviews_btn else "0"
                    reviews_count = int(re.search(r'(\d+)', reviews_text.replace(',','')).group(1)) if re.search(r'\d+', reviews_text) else 0

                    # Claimed status
                    claimed_btn = soup.find('button', attrs={'data-item-id': 'merchant'})
                    is_claimed = "Unclaimed" if claimed_btn else "Claimed"
                    
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
                    progress_bar.progress(min(current_progress, 1.0))
                    status_text.text(f"✅ Processed: {name}")
                    
                    # Human-like pause between listings
                    random_sleep(1, 2)
                    
                except Exception as e:
                    st.warning(f"Error processing listing {i+1}: {e}")
                    continue

        except Exception as e:
            st.error(f"Critical Scraper Error: {e}")
            import traceback
            st.code(traceback.format_exc())
        finally:
            browser.close()
            
    return leads

# --- UI LAYOUT ---

def main():
    st.set_page_config(page_title="Local Maps Leads Pro", layout="wide", page_icon="🗺️")
    
    st.title("🗺️ Local Maps Leads Scraper & Vetting Tool")
    st.markdown("**Human-like browsing with Playwright + Stealth**")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.header("Configuration")
    
    st.sidebar.subheader("Filter & Budget Settings")
    reviews_threshold = st.sidebar.slider("New Lead Definition (Max Reviews)", 0, 100, 15, help="Businesses with fewer reviews than this are marked 'High Priority'.")
    vetting_threshold = st.sidebar.slider("High Budget Score Threshold", 0, 100, 50, help="Websites with a vetting score above this are marked 'High Budget'.")
    only_no_website = st.sidebar.checkbox("Only Show Leads Without Websites", help="Useful for selling web design services.")
    
    with st.sidebar.form("search_form"):
        keyword = st.text_input("Industry / Keyword", "")
        
        st.markdown("### Location Settings")
        location_input = st.text_input("Center Address / City", "")
        radius_km = st.slider("Search Radius (Approx. km)", 1, 100, 10, help="Controls the initial map zoom level.")
        
        max_results = st.number_input("Max Results", min_value=1, max_value=50, value=5)
        
        submitted = st.form_submit_button("🚀 Start Scraping")
    
    st.sidebar.markdown("---")
    st.sidebar.info("💡 Uses Playwright with stealth to browse like a human")
    st.sidebar.warning("⚠️ Make sure Playwright browsers are installed:\n`playwright install chromium`")
    
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
                    
                    with st.spinner("🤖 Initializing human-like browser (Playwright + Stealth)..."):
                        data = run_google_maps_scraper(
                            keyword, 
                            location_input, 
                            lat, lon, zoom, 
                            max_results, 
                            progress_bar, 
                            status_text, 
                            reviews_threshold, 
                            vetting_threshold
                        )

                    if data:
                        st.success(f"✅ Scraping Completed! Found {len(data)} leads.")
                        
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
                            label="📥 Download Results (CSV)",
                            data=csv,
                            file_name=f"leads_{keyword}_{location_input}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.warning("No leads found. Try a different location or increase wait times.")
                
                except Exception as e:
                    import traceback
                    st.error(f"Execution Error: {e}")
                    st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
