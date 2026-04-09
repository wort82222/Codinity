"""
Quick test script to verify scraper works
Tests scraping without S3 upload
"""

from scraper import LongLifeFoodScraper

if __name__ == "__main__":
    print("🧪 Testing Long Life Food Scraper (Local Only)\n")
    
    # Create scraper without S3
    scraper = LongLifeFoodScraper()
    
    # Run scraper
    scraper.run()
    
    print("\n✅ Test complete! Check the 'data' folder for results.")
