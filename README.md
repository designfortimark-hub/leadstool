# Google Maps Lead & Vetting Scraper

A web application for scraping Google Maps business listings and vetting websites for lead qualification. **100% Vercel deployable** with all functions working perfectly.

## 🚀 Vercel Deployment

This app is fully configured for Vercel deployment with a modern HTML frontend and serverless API functions.

### Quick Deploy

1. **Install Vercel CLI** (if not already installed):
   ```bash
   npm i -g vercel
   ```

2. **Deploy to Vercel**:
   ```bash
   vercel
   ```

3. **Set Environment Variables** (optional but recommended):
   - `SCRAPER_API_KEY` - For ScraperAPI (get free key at https://www.scraperapi.com)
   - `GOOGLE_MAPS_API_KEY` - For Google Maps Places API (most reliable option)

### Manual Deployment via Vercel Dashboard

1. Push your code to GitHub
2. Import project in Vercel dashboard
3. Add environment variables in project settings:
   - Go to Project Settings → Environment Variables
   - Add `SCRAPER_API_KEY` and/or `GOOGLE_MAPS_API_KEY`
4. Deploy!

## 📋 Features

- **Google Maps Scraping**: Extract business listings with location-based search
- **Website Vetting**: Analyze websites for wealth markers (ads, premium tech, keywords)
- **Lead Qualification**: Filter leads by reviews, claimed status, and budget potential
- **Export to CSV**: Download results for further analysis
- **Modern UI**: Beautiful, responsive HTML frontend
- **Vercel Compatible**: Fully optimized for serverless deployment
- **Dual Mode**: Works as Streamlit app locally or web app on Vercel

## 🔧 Setup

### Local Development (Streamlit)

1. **Install Python 3.9+**

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Streamlit App**:
   ```bash
   streamlit run app.py
   ```

### Local Development (Web App)

1. **Install Dependencies** (same as above)

2. **Run a local server**:
   ```bash
   # Using Python's built-in server
   python -m http.server 8000
   # Then open http://localhost:8000
   ```

## 🔑 API Configuration (Optional but Recommended)

For best results, configure one of these APIs:

### Option 1: ScraperAPI (Recommended for Web Scraping)
- Sign up at https://www.scraperapi.com (free tier available)
- Get your API key
- Set environment variable: `SCRAPER_API_KEY`
- Enable "Use ScraperAPI" checkbox in the UI

### Option 2: Google Maps Places API (Most Reliable)
- Enable Places API in Google Cloud Console
- Create API key with Places API enabled
- Set environment variable: `GOOGLE_MAPS_API_KEY`
- The app will automatically use this if available
- Note: Requires billing setup but provides most accurate data

## 📝 Usage

1. Enter a keyword/industry (e.g., "restaurants", "dentists")
2. Enter a location (city, address, etc.)
3. Adjust search radius and max results
4. Configure filters (reviews threshold, budget threshold)
5. Optionally enable ScraperAPI if configured
6. Click "Start Scraping"
7. View results in the table
8. Download results as CSV

## 🎯 Lead Filtering

- **High Priority Leads**: Businesses with low reviews or unclaimed status
- **Budget Estimation**: Based on website analysis (ads, premium tech, keywords)
- **Website Vetting**: Scores websites for potential budget capacity
- **Filter Options**: Show only leads without websites (useful for web design services)

## 📦 Project Structure

```
.
├── app.py              # Main application logic (used by both Streamlit and API)
├── index.html          # Modern HTML frontend for Vercel
├── api/
│   ├── scrape.py       # Vercel serverless function for scraping
│   └── vet.py          # Vercel serverless function for website vetting
├── requirements.txt    # Python dependencies
├── vercel.json         # Vercel configuration
├── .vercelignore       # Files to ignore in deployment
└── README.md           # This file
```

## 🛠️ Troubleshooting

**No results found?**
- Try using Google Maps Places API (most reliable)
- Enable ScraperAPI for JavaScript rendering
- Adjust search terms or location
- Check that environment variables are set correctly in Vercel dashboard

**Vercel deployment issues?**
- Ensure all dependencies are in `requirements.txt`
- Check that `vercel.json` is properly configured
- Verify environment variables are set in Vercel dashboard (Project Settings → Environment Variables)
- Check build logs in Vercel dashboard for specific errors

**API errors?**
- Verify your API keys are set correctly
- Check API rate limits (especially for free tiers)
- Ensure CORS is properly configured (already handled in the code)

## 🧹 Clean Project

All junk files have been removed:
- ✅ Build artifacts (`build/`, `dist/`)
- ✅ Debug files (`debug_*.py`)
- ✅ Build scripts (`build_app.py`, `wrapper.py`)
- ✅ PyInstaller spec files (`*.spec`)

## 📄 License

MIT License - feel free to use and modify as needed.

## 🎉 Ready to Deploy!

Your project is now 100% ready for Vercel deployment. Just run `vercel` and you're good to go!
