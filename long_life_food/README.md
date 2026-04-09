# Long Life Food Scraper

Automated scraper for https://www.sheeel.com/ar/long-life-food.html with S3 integration and daily scheduling.

## 🎯 Features

- ✅ **Complete data extraction** - 25+ fields per product
- ✅ **Pagination support** - Scrapes all pages automatically
- ✅ **Image download** - Downloads all product images
- ✅ **S3 integration** - Uploads to AWS S3 with date partitioning
- ✅ **Excel export** - Organized data in Excel format
- ✅ **Daily automation** - GitHub Actions workflow
- ✅ **Production ready** - Error handling, logging, retries

## 📁 Project Structure

```
long_life_food/
├── scraper.py              # Main scraper script
├── requirements.txt        # Python dependencies
├── test_scraper.py         # Local testing
├── .gitignore             # Git exclusions
└── .env.example           # Config template
```

## 📊 S3 Output Structure

```
s3://bucket/sheeel_data/
└── year=YYYY/month=MM/day=DD/long_life_food/
    ├── excel-files/
    │   └── long_life_food_TIMESTAMP.xlsx
    └── images/
        ├── 226950.jpg
        └── ...
```

## 🚀 Quick Start

**Local testing:**
```bash
cd Codinity/long_life_food
pip install -r requirements.txt
playwright install chromium
python test_scraper.py
```

**GitHub Actions:**
- Workflow: `.github/workflows/daily-long-life-food.yml`
- Runs daily at 2:00 AM UTC
- Requires GitHub Secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET_NAME`

## 📈 Extracted Data

25+ fields including:
- Product ID, SKU, name, URL
- Prices: old_price, special_price, discount_percent
- Images: image_url, s3_image_path
- Stock: stock_status, quantity_left, times_bought
- Additional: deal_time_left, short_description, badges

## 🔧 Environment Variables

```bash
AWS_ACCESS_KEY_ID       # AWS access key
AWS_SECRET_ACCESS_KEY   # AWS secret key
S3_BUCKET_NAME          # S3 bucket name
```

---

**Category:** Long Life Food  
**URL:** https://www.sheeel.com/ar/long-life-food.html  
**S3 Folder:** `long_life_food`
