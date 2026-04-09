"""
Long Life Food Scraper - Complete Production Version
Scrapes https://www.sheeel.com/ar/long-life-food.html with pagination
Saves data to S3 with date partitioning and downloads images
"""

from playwright.sync_api import sync_playwright
import json
import re
import os
import requests
from datetime import datetime
from pathlib import Path
import time
import pandas as pd
import boto3
from urllib.parse import urlparse
import hashlib

class LongLifeFoodScraper:
    def __init__(self, s3_bucket=None, aws_access_key=None, aws_secret_key=None):
        self.base_url = "https://www.sheeel.com/ar/long-life-food.html"
        self.category = "long_life_food"
        self.products = []
        self.s3_bucket = s3_bucket
        
        # Setup S3 if credentials provided
        if s3_bucket and aws_access_key and aws_secret_key:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key
            )
        else:
            self.s3_client = None
        
        # Date partitioning
        now = datetime.now()
        self.year = now.strftime("%Y")
        self.month = now.strftime("%m")
        self.day = now.strftime("%d")
        
        # Local folders
        self.local_data_dir = Path("data")
        self.local_images_dir = self.local_data_dir / "images"
        self.local_data_dir.mkdir(exist_ok=True)
        self.local_images_dir.mkdir(exist_ok=True)
    
    def extract_product_from_element(self, product_element):
        """Extract all available fields from a product element"""
        
        try:
            product_data = {}
            
            # ===== BASIC INFO =====
            product_data['element_id'] = product_element.get_attribute('id') or ''
            
            # Extract numeric ID
            id_match = re.search(r'product-item-info_(\d+)', product_data['element_id'])
            product_data['product_id'] = int(id_match.group(1)) if id_match else None
            
            # Product name
            name_el = product_element.query_selector('.product-item-name a, .product-item-link')
            product_data['name'] = name_el.inner_text().strip() if name_el else None
            
            # Product URL
            url_el = product_element.query_selector('a.product-item-link')
            product_data['url'] = url_el.get_attribute('href') if url_el else None
            
            # SKU
            form_el = product_element.query_selector('form[data-product-sku]')
            product_data['sku'] = form_el.get_attribute('data-product-sku') if form_el else None
            
            # Product type
            product_data['type'] = form_el.get_attribute('data-product-type') if form_el else None
            
            # ===== PRICING =====
            # Old/Regular price
            old_price_el = product_element.query_selector('.old-price .price')
            if old_price_el:
                old_price_text = old_price_el.inner_text().strip()
                price_match = re.search(r'([\d.]+)', old_price_text)
                product_data['old_price'] = float(price_match.group(1)) if price_match else None
                product_data['old_price_text'] = old_price_text
            else:
                product_data['old_price'] = None
                product_data['old_price_text'] = None
            
            # Special/Final price
            special_price_el = product_element.query_selector('.special-price .price, .price-final_price .price')
            if special_price_el:
                special_price_text = special_price_el.inner_text().strip()
                price_match = re.search(r'([\d.]+)', special_price_text)
                product_data['special_price'] = float(price_match.group(1)) if price_match else None
                product_data['special_price_text'] = special_price_text
            else:
                any_price_el = product_element.query_selector('.price')
                if any_price_el:
                    price_text = any_price_el.inner_text().strip()
                    price_match = re.search(r'([\d.]+)', price_text)
                    product_data['special_price'] = float(price_match.group(1)) if price_match else None
                    product_data['special_price_text'] = price_text
                else:
                    product_data['special_price'] = None
                    product_data['special_price_text'] = None
            
            # Calculate discount
            if product_data['old_price'] and product_data['special_price']:
                product_data['discount_amount'] = round(product_data['old_price'] - product_data['special_price'], 3)
                product_data['discount_percent'] = round((product_data['discount_amount'] / product_data['old_price']) * 100, 1)
            else:
                product_data['discount_amount'] = None
                product_data['discount_percent'] = None
            
            # ===== IMAGES =====
            img_el = product_element.query_selector('img.product-image-photo')
            if img_el:
                product_data['image_url'] = img_el.get_attribute('src') or img_el.get_attribute('data-src')
                product_data['image_alt'] = img_el.get_attribute('alt')
                product_data['image_width'] = img_el.get_attribute('width')
                product_data['image_height'] = img_el.get_attribute('height')
            else:
                product_data['image_url'] = None
                product_data['image_alt'] = None
                product_data['image_width'] = None
                product_data['image_height'] = None
            
            # ===== BADGES & LABELS =====
            discount_badge_el = product_element.query_selector('.discount-percent-item')
            product_data['discount_badge'] = discount_badge_el.inner_text().strip() if discount_badge_el else None
            
            availability_el = product_element.query_selector('.availability.only')
            if availability_el:
                availability_text = availability_el.inner_text().strip()
                product_data['availability_badge'] = availability_text
                qty_match = re.search(r'\d+', availability_text)
                product_data['quantity_left'] = int(qty_match.group()) if qty_match else None
            else:
                product_data['availability_badge'] = None
                product_data['quantity_left'] = None
            
            bought_el = product_element.query_selector('.x-bought-count')
            product_data['times_bought'] = bought_el.inner_text().strip() if bought_el else None
            
            stock_status_el = product_element.query_selector('.timer-expired-label span')
            product_data['stock_status'] = stock_status_el.inner_text().strip() if stock_status_el else None
            
            # ===== DEAL TIMER =====
            timer_el = product_element.query_selector('.product-deal-time .time')
            product_data['deal_time_left'] = timer_el.inner_text().strip() if timer_el else None
            
            # ===== DESCRIPTION =====
            desc_el = product_element.query_selector('.product-short-description')
            product_data['short_description'] = desc_el.inner_text().strip() if desc_el else None
            
            # ===== CART INFO =====
            cart_form = product_element.query_selector('form[data-role="tocart-form"]')
            if cart_form:
                product_data['add_to_cart_url'] = cart_form.get_attribute('action')
                form_key_input = cart_form.query_selector('input[name="form_key"]')
                product_data['form_key'] = form_key_input.get_attribute('value') if form_key_input else None
            else:
                product_data['add_to_cart_url'] = None
                product_data['form_key'] = None
            
            # ===== METADATA =====
            product_data['category'] = self.category
            product_data['scraped_at'] = datetime.now().isoformat()
            product_data['scraped_date'] = datetime.now().strftime("%Y-%m-%d")
            
            return product_data
            
        except Exception as e:
            print(f"  ⚠ Error extracting product: {e}")
            return None
    
    def get_total_pages(self, page):
        """Extract total number of pages from pagination"""
        
        try:
            # Find all page links
            page_links = page.query_selector_all('.pages-items .item a.page')
            
            if not page_links:
                return 1
            
            # Extract page numbers
            page_numbers = []
            for link in page_links:
                span = link.query_selector('span:last-child')
                if span:
                    try:
                        page_num = int(span.inner_text().strip())
                        page_numbers.append(page_num)
                    except:
                        pass
            
            return max(page_numbers) if page_numbers else 1
            
        except Exception as e:
            print(f"  ⚠ Error getting total pages: {e}")
            return 1
    
    def scrape_page(self, page, page_num):
        """Scrape a single page"""
        
        print(f"\n{'='*70}")
        print(f"📄 SCRAPING PAGE {page_num}")
        print("="*70)
        
        try:
            # Wait for products
            page.wait_for_selector('[id^="product-item-info_"]', timeout=10000)
            
            # Scroll to load all products
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            
            # Get products
            products = page.query_selector_all('[id^="product-item-info_"]')
            print(f"✓ Found {len(products)} products on page {page_num}")
            
            # Extract data
            page_products = []
            for i, product in enumerate(products, 1):
                product_data = self.extract_product_from_element(product)
                if product_data:
                    product_data['page_number'] = page_num
                    page_products.append(product_data)
                    
                if i % 10 == 0:
                    print(f"  Processed {i}/{len(products)} products...")
            
            print(f"✓ Successfully extracted {len(page_products)} products from page {page_num}")
            return page_products
            
        except Exception as e:
            print(f"❌ Error scraping page {page_num}: {e}")
            return []
    
    def scrape_all_pages(self):
        """Scrape all pages with pagination"""
        
        print("\n" + "="*70)
        print("🚀 LONG LIFE FOOD SCRAPER - WITH PAGINATION")
        print("="*70)
        print(f"\nURL: {self.base_url}\n")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = context.new_page()
            
            try:
                # Load first page
                print("📡 Loading first page...")
                page.goto(self.base_url, wait_until='networkidle', timeout=30000)
                print(f"✓ Page loaded: {page.title()}\n")
                
                # Get total pages
                total_pages = self.get_total_pages(page)
                print(f"📊 Total pages found: {total_pages}\n")
                
                # Scrape first page
                page_products = self.scrape_page(page, 1)
                self.products.extend(page_products)
                
                # Scrape remaining pages
                for page_num in range(2, total_pages + 1):
                    print(f"\n⏳ Waiting 2s before next page...")
                    time.sleep(2)
                    
                    # Navigate to next page
                    next_url = f"{self.base_url}?p={page_num}"
                    print(f"📡 Loading {next_url}")
                    page.goto(next_url, wait_until='networkidle', timeout=30000)
                    
                    # Scrape this page
                    page_products = self.scrape_page(page, page_num)
                    self.products.extend(page_products)
                
                print("\n" + "="*70)
                print("✅ ALL PAGES SCRAPED SUCCESSFULLY")
                print("="*70)
                print(f"\nTotal products scraped: {len(self.products)}")
                print(f"Across {total_pages} pages")
                
            except Exception as e:
                print(f"\n❌ Error during scraping: {e}")
                import traceback
                traceback.print_exc()
                
            finally:
                context.close()
                browser.close()
    
    def download_image(self, image_url, product_id):
        """Download product image"""
        
        if not image_url:
            return None
        
        try:
            # Download image
            response = requests.get(image_url, timeout=10, stream=True)
            response.raise_for_status()
            
            # Detect proper extension from Content-Type header
            content_type = response.headers.get('Content-Type', '').lower()
            if 'jpeg' in content_type or 'jpg' in content_type:
                ext = '.jpg'
            elif 'png' in content_type:
                ext = '.png'
            elif 'gif' in content_type:
                ext = '.gif'
            elif 'webp' in content_type:
                ext = '.webp'
            else:
                # Fallback to URL extension or .jpg
                ext = os.path.splitext(urlparse(image_url).path)[1] or '.jpg'
            
            filename = f"{product_id}{ext}"
            
            # Save locally
            local_path = self.local_images_dir / filename
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return str(local_path)
            
        except Exception as e:
            print(f"  ⚠ Error downloading image for product {product_id}: {e}")
            return None
    
    def download_all_images(self):
        """Download all product images"""
        
        print("\n" + "="*70)
        print("📥 DOWNLOADING PRODUCT IMAGES")
        print("="*70)
        
        total = len(self.products)
        successful = 0
        
        for i, product in enumerate(self.products, 1):
            if product.get('image_url'):
                local_path = self.download_image(product['image_url'], product['product_id'])
                if local_path:
                    product['local_image_path'] = local_path
                    successful += 1
                    
                if i % 10 == 0:
                    print(f"  Downloaded {i}/{total} images...")
        
        print(f"\n✓ Downloaded {successful}/{total} images")
    
    def save_to_excel(self, include_s3_paths=False):
        """Save data to Excel file"""
        
        print("\n" + "="*70)
        print("💾 SAVING TO EXCEL")
        print("="*70)
        
        if not self.products:
            print("⚠ No products to save")
            return None
        
        # Create DataFrame
        df = pd.DataFrame(self.products)
        
        # Remove local_image_path column if S3 is configured
        if include_s3_paths and 'local_image_path' in df.columns:
            df = df.drop(columns=['local_image_path'])
            print("✓ Removed 'local_image_path' column")
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"long_life_food_{timestamp}.xlsx"
        local_path = self.local_data_dir / filename
        
        # Save to Excel
        df.to_excel(local_path, index=False, engine='openpyxl')
        print(f"✓ Saved to: {local_path}")
        print(f"  Rows: {len(df)}")
        print(f"  Columns: {len(df.columns)}")
        
        return str(local_path)
    
    def upload_to_s3(self, local_file, s3_key):
        """Upload file to S3"""
        
        if not self.s3_client:
            print("⚠ S3 not configured, skipping upload")
            return False
        
        try:
            self.s3_client.upload_file(local_file, self.s3_bucket, s3_key)
            print(f"✓ Uploaded to s3://{self.s3_bucket}/{s3_key}")
            return True
        except Exception as e:
            print(f"❌ Error uploading to S3: {e}")
            return False
    
    def upload_results_to_s3(self):
        """Upload Excel and images to S3 with date partitioning"""
        
        if not self.s3_client:
            print("\n⚠ S3 not configured, skipping S3 upload")
            return None
        
        print("\n" + "="*70)
        print("☁️  UPLOADING TO S3")
        print("="*70)
        
        # Upload images first and add S3 paths
        print(f"\n📷 Uploading images...")
        uploaded_images = 0
        for product in self.products:
            if product.get('local_image_path') and os.path.exists(product['local_image_path']):
                image_filename = os.path.basename(product['local_image_path'])
                image_s3_key = f"sheeel_data/year={self.year}/month={self.month}/day={self.day}/{self.category}/images/{image_filename}"
                
                if self.upload_to_s3(product['local_image_path'], image_s3_key):
                    product['s3_image_path'] = f"s3://{self.s3_bucket}/{image_s3_key}"
                    uploaded_images += 1
                    
                if uploaded_images % 10 == 0:
                    print(f"  Uploaded {uploaded_images} images...")
        
        print(f"\n✓ Uploaded {uploaded_images} images to S3")
        
        # Create ONE Excel file with S3 paths (without local_image_path column)
        print(f"\n📊 Creating Excel file with S3 paths...")
        df = pd.DataFrame(self.products)
        
        # Remove local_image_path column
        if 'local_image_path' in df.columns:
            df = df.drop(columns=['local_image_path'])
            print("✓ Removed 'local_image_path' column")
        
        # Save locally
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_filename = f"long_life_food_{timestamp}.xlsx"
        excel_local_path = str(self.local_data_dir / excel_filename)
        df.to_excel(excel_local_path, index=False, engine='openpyxl')
        print(f"✓ Saved to: {excel_local_path}")
        print(f"  Rows: {len(df)}, Columns: {len(df.columns)}")
        
        # Upload to S3
        excel_s3_key = f"sheeel_data/year={self.year}/month={self.month}/day={self.day}/{self.category}/excel-files/{excel_filename}"
        self.upload_to_s3(excel_local_path, excel_s3_key)
        
        return excel_local_path
    
    def run(self):
        """Main execution flow"""
        
        print("\n" + "="*70)
        print("🥫 LONG LIFE FOOD SCRAPER - PRODUCTION")
        print("="*70)
        print(f"\nDate: {self.year}-{self.month}-{self.day}")
        print(f"Category: {self.category}")
        print(f"S3 Bucket: {self.s3_bucket or 'Not configured'}")
        print()
        
        # Step 1: Scrape all pages
        self.scrape_all_pages()
        
        if not self.products:
            print("\n❌ No products scraped, exiting")
            return
        
        # Step 2: Download images
        self.download_all_images()
        
        # Step 3: Save to Excel and upload to S3
        if self.s3_client:
            # Use S3 upload which creates Excel with S3 paths
            excel_path = self.upload_results_to_s3()
        else:
            # Local only - save Excel with local paths
            excel_path = self.save_to_excel()
        
        # Summary
        print("\n" + "="*70)
        print("📊 FINAL SUMMARY")
        print("="*70)
        print(f"\n✅ Total products: {len(self.products)}")
        print(f"✅ Excel file: {excel_path}")
        print(f"✅ Images downloaded: {sum(1 for p in self.products if p.get('local_image_path'))}")
        
        if self.s3_client:
            print(f"\n☁️  S3 Paths:")
            print(f"  Excel: s3://{self.s3_bucket}/sheeel_data/year={self.year}/month={self.month}/day={self.day}/{self.category}/excel-files/")
            print(f"  Images: s3://{self.s3_bucket}/sheeel_data/year={self.year}/month={self.month}/day={self.day}/{self.category}/images/")
        
        print("\n" + "="*70)
        print("✅ SCRAPING COMPLETE!")
        print("="*70 + "\n")

if __name__ == "__main__":
    # Get configuration from environment or use defaults
    s3_bucket = os.getenv('S3_BUCKET_NAME')
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    
    # Run scraper
    scraper = LongLifeFoodScraper(
        s3_bucket=s3_bucket,
        aws_access_key=aws_access_key,
        aws_secret_key=aws_secret_key
    )
    
    scraper.run()
