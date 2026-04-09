"""
Quick test script to verify scraper works
Tests scraping without S3 upload
"""

from scraper import PowerBankChargersScraper

if __name__ == "__main__":
    print("🧪 Testing Power Banks & Chargers Scraper (Local Only)\n")
    
    # Create scraper without S3
    scraper = PowerBankChargersScraper()
    
    # Run scraper
    scraper.run()
    
    print("\n✅ Test complete! Check the 'data' folder for results.")
