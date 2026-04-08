# Emergency Needs Scraper

Automated scraper for https://www.sheeel.com/ar/emergency-needs.html with S3 integration and daily scheduling.

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
emergency_need/
├── scraper.py              # Main scraper script
├── requirements.txt        # Python dependencies
├── .github/
│   └── workflows/
│       └── daily-scraper.yml  # GitHub Actions workflow
├── data/                   # Local data folder (created on run)
│   ├── images/            # Downloaded images
│   └── *.xlsx             # Excel files
└── README.md              # This file
```

## 📊 Extracted Data Fields (25+)

### Basic Info
- product_id, sku, name, url, type, category

### Pricing
- old_price, special_price, discount_amount, discount_percent
- old_price_text, special_price_text

### Images
- image_url, image_alt, image_width, image_height
- local_image_path, s3_image_path

### Availability
- stock_status, quantity_left, times_bought
- discount_badge, availability_badge

### Additional
- deal_time_left, short_description
- add_to_cart_url, form_key
- page_number, scraped_at, scraped_date

## 🚀 Setup Instructions

### 1. Local Setup

```bash
# Navigate to project folder
cd Codinity/emergency_need

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Set environment variables (optional for local testing)
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export S3_BUCKET_NAME="your_bucket_name"

# Run scraper
python scraper.py
```

### 2. GitHub Actions Setup

1. **Add Repository Secrets:**
   - Go to: Repository → Settings → Secrets and variables → Actions
   - Add three secrets:
     - `AWS_ACCESS_KEY_ID` - Your AWS access key
     - `AWS_SECRET_ACCESS_KEY` - Your AWS secret key
     - `S3_BUCKET_NAME` - Your S3 bucket name (e.g., `my-bucket`)

2. **Enable GitHub Actions:**
   - Go to: Repository → Actions
   - Enable workflows if disabled

3. **Push code to GitHub:**
   ```bash
   git add .
   git commit -m "Add emergency needs scraper"
   git push origin main
   ```

4. **The workflow runs:**
   - **Automatically** every day at 2:00 AM UTC
   - **Manually** via Actions tab → Daily Emergency Needs Scraper → Run workflow
   - **On push** when files in `emergency_need/` change

## ☁️ S3 Structure

Data is partitioned by date:

```
s3://your-bucket/sheeel_data/
├── year=2026/
│   └── month=04/
│       └── day=08/
│           └── emergency_need/
│               ├── excel-files/
│               │   ├── emergency_needs_20260408_140530.xlsx
│               │   └── emergency_needs_with_s3_paths.xlsx
│               └── images/
│                   ├── 226950.jpg
│                   ├── 227604.jpg
│                   └── ...
```

## 📈 Output Files

### Excel Files

1. **emergency_needs_TIMESTAMP.xlsx**
   - All scraped data
   - Local image paths

2. **emergency_needs_with_s3_paths.xlsx**
   - All scraped data
   - S3 image paths included

### Excel Columns

| Column | Type | Description |
|--------|------|-------------|
| product_id | int | Unique product ID |
| sku | str | Product SKU |
| name | str | Product name (Arabic) |
| url | str | Product page URL |
| old_price | float | Original price (KWD) |
| special_price | float | Sale price (KWD) |
| discount_percent | float | Discount percentage |
| image_url | str | CDN image URL |
| local_image_path | str | Local file path |
| s3_image_path | str | S3 path (s3://...) |
| stock_status | str | Stock status |
| quantity_left | int | Remaining quantity |
| times_bought | str | Purchase count |
| short_description | str | Product description |
| ... | ... | +10 more fields |

## 🔧 Configuration

### Environment Variables

```bash
AWS_ACCESS_KEY_ID       # AWS access key (required for S3)
AWS_SECRET_ACCESS_KEY   # AWS secret key (required for S3)
S3_BUCKET_NAME          # S3 bucket name (required for S3)
```

### Customize Scraper

Edit `scraper.py`:

```python
# Change base URL
self.base_url = "https://www.sheeel.com/ar/your-category.html"

# Change category name
self.category = "your_category"

# Adjust delays between pages
time.sleep(2)  # Change delay
```

## 🐛 Troubleshooting

### Issue: No products scraped
**Solution:** Check if selectors changed. Run locally and inspect HTML.

### Issue: S3 upload fails
**Solution:** 
- Verify AWS credentials are correct
- Check S3 bucket exists and has correct permissions
- Ensure bucket policy allows PutObject

### Issue: Images not downloading
**Solution:**
- Check internet connection
- Verify image URLs are accessible
- Check disk space

### Issue: GitHub Action fails
**Solution:**
- Check secrets are set correctly
- Review workflow logs in Actions tab
- Ensure Playwright browsers installed

## 📅 Scheduling

The scraper runs daily at 2:00 AM UTC.

To change schedule, edit `.github/workflows/daily-scraper.yml`:

```yaml
schedule:
  - cron: '0 2 * * *'  # Minute Hour Day Month DayOfWeek
```

Examples:
- `'0 0 * * *'` - Daily at midnight UTC
- `'0 */6 * * *'` - Every 6 hours
- `'0 9 * * 1'` - Every Monday at 9 AM UTC

## 🔒 Security

- ✅ AWS credentials stored as GitHub Secrets
- ✅ Secrets never logged or exposed
- ✅ Local data folder in .gitignore
- ✅ No hardcoded credentials

## 📊 Monitoring

### Check scraper status:
1. Go to: Repository → Actions
2. View workflow runs
3. Check logs for any errors

### Download results:
- Artifacts are uploaded for 7 days
- Download from Actions → Workflow run → Artifacts

## 🚀 Usage Examples

### Run locally
```bash
python scraper.py
```

### Run with custom configuration
```python
scraper = EmergencyNeedsScraper(
    s3_bucket="my-bucket",
    aws_access_key="KEY",
    aws_secret_key="SECRET"
)
scraper.run()
```

### Access S3 data
```bash
# List files
aws s3 ls s3://my-bucket/sheeel_data/year=2026/month=04/day=08/emergency_need/

# Download Excel
aws s3 cp s3://my-bucket/sheeel_data/.../emergency_needs.xlsx .

# Download images
aws s3 sync s3://my-bucket/sheeel_data/.../images/ ./images/
```

## 📈 Future Enhancements

- [ ] Add more categories
- [ ] Email notifications on completion
- [ ] Data validation and quality checks
- [ ] Compare with previous runs
- [ ] Price tracking and alerts
- [ ] Database integration

## 📝 License

MIT License

## 👤 Author

Created for automated product data collection from sheeel.com

## 🆘 Support

For issues, questions, or suggestions:
1. Check troubleshooting section
2. Review GitHub Actions logs
3. Open an issue on GitHub

---

**Last Updated:** April 8, 2026  
**Version:** 1.0.0  
**Status:** ✅ Production Ready
