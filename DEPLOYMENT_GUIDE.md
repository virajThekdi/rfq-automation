# 🚀 Complete Deployment Guide - 24/7 RFQ Automation System

## 📋 Table of Contents

1. [Quick Start (FREE - 15 minutes)](#quick-start)
2. [Understanding the Architecture](#architecture)
3. [Step-by-Step Deployment](#deployment)
4. [24/7 Automation Setup](#automation)
5. [Troubleshooting](#troubleshooting)

---

## 🎯 Quick Start (FREE - 15 minutes) <a name="quick-start"></a>

### What You'll Get:
- ✅ Web interface on Streamlit Cloud (FREE)
- ✅ 24/7 automatic email checking (FREE via GitHub Actions)
- ✅ Automatic follow-up sending (FREE via GitHub Actions)
- ✅ Cloud database (FREE via Supabase)
- **Total Cost: $0/month**

### Prerequisites:
1. GitHub account (free)
2. Gmail account with App Password
3. Gemini API key (free from Google AI Studio)

---

## 🏗️ Understanding the Architecture <a name="architecture"></a>

```
┌─────────────────────────────────────────────────────────┐
│         STREAMLIT WEB APP (Streamlit Cloud)             │
│  • Create RFQs                                          │
│  • View responses                                       │
│  • Generate reports                                     │
│  • Manual controls                                      │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ (Shared Database)
                   │
                   ▼
         ┌─────────────────────┐
         │  SUPABASE DATABASE  │
         │   (PostgreSQL)      │
         │   • RFQs            │
         │   • Vendors         │
         │   • Responses       │
         └──────────┬──────────┘
                    │
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│      BACKGROUND WORKER (GitHub Actions)                 │
│  Runs every 30 minutes automatically                    │
│  • Check emails for vendor responses                    │
│  • Parse responses (HTML/Excel/PDF)                     │
│  • Send follow-up reminders                             │
│  • Update database                                      │
└─────────────────────────────────────────────────────────┘
```

---

## 📝 Step-by-Step Deployment <a name="deployment"></a>

### Step 1: Set Up Supabase Database (5 minutes)

1. Go to https://supabase.com/
2. Sign up (FREE - no credit card required)
3. Click "New Project"
   - Name: `rfq-automation`
   - Database Password: (save this!)
   - Region: Choose closest to you
4. Wait 2 minutes for database to initialize
5. Go to Settings → API
6. Copy these values:
   - Project URL: `https://xxxxx.supabase.co`
   - `anon` `public` key: `eyJhbGciOiJ...`

7. In Supabase, go to SQL Editor and run:
   ```sql
   -- Copy the contents from database/schema.sql
   -- (It will create all tables: rfqs, items, vendors, responses, quotations)
   ```

### Step 2: Create GitHub Repository (3 minutes)

1. Go to https://github.com/new
2. Repository name: `rfq-automation`
3. Choose: Public (for FREE GitHub Actions)
4. Don't initialize with README
5. Click "Create repository"

### Step 3: Push Code to GitHub (2 minutes)

```bash
cd /Workspace/Users/virajthekdi1@gmail.com/rfq_streamlit

# Initialize git
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - RFQ Automation System with 24/7 workers"

# Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/rfq-automation.git

# Push
git branch -M main
git push -u origin main
```

### Step 4: Add GitHub Secrets (3 minutes)

1. Go to your GitHub repository
2. Click Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add these secrets one by one:

 Secret Name | Value |
-------------|-------|
 `EMAIL_ADDRESS` | `virajthekdi1@gmail.com` |
 `EMAIL_PASSWORD` | `tthe gtgf hdum kdqt` |
 `GEMINI_API_KEY` | `AIzaSyAwUraP4W2QSx1phKhOgyZwwEiJF3Zknbc` |
 `SUPABASE_URL` | `https://xxxxx.supabase.co` (from Step 1) |
 `SUPABASE_KEY` | `eyJhbGciOiJ...` (from Step 1) |

### Step 5: Deploy to Streamlit Cloud (5 minutes)

1. Go to https://share.streamlit.io/
2. Sign in with GitHub
3. Click "New app"
4. Fill in:
   - Repository: `YOUR_USERNAME/rfq-automation`
   - Branch: `main`
   - Main file path: `app.py`
5. Click "Advanced settings"
6. In "Secrets" section, paste:
   ```toml
   EMAIL_ADDRESS = "virajthekdi1@gmail.com"
   EMAIL_PASSWORD = "tthe gtgf hdum kdqt"
   GEMINI_API_KEY = "AIzaSyAwUraP4W2QSx1phKhOgyZwwEiJF3Zknbc"
   SUPABASE_URL = "https://xxxxx.supabase.co"
   SUPABASE_KEY = "eyJhbGciOiJ..."
   ```
7. Click "Deploy!"
8. Wait 2-3 minutes
9. Your app will be live! 🎉

### Step 6: Verify Automation (2 minutes)

1. Go to your GitHub repository
2. Click "Actions" tab
3. You should see "RFQ Email Automation - 24/7"
4. Click on it
5. Click "Run workflow" → "Run workflow" to test manually
6. Watch it run!

---

## 🤖 24/7 Automation Setup <a name="automation"></a>

### How It Works:

GitHub Actions will automatically run every 30 minutes:
- **:00, :30** - Check emails and send follow-ups

You can also trigger manually:
1. Go to GitHub → Actions
2. Select "RFQ Email Automation"
3. Click "Run workflow"

### What Gets Automated:

✅ **Email Monitoring:**
- Connects to Gmail IMAP
- Checks for vendor responses
- Parses HTML tables, Excel files, PDFs
- Saves to database
- Updates vendor status

✅ **Follow-up Reminders:**
- Checks pending vendors
- Calculates time since last contact
- Sends reminders based on interval (12/24/48/72 hours)
- Respects max follow-up count
- Stops after deadline

✅ **Smart Logic:**
- Only sends if enough time has passed
- Adds urgency based on deadline proximity
- Skips vendors who already responded
- Prevents duplicate emails

### Monitoring Your Automation:

1. **GitHub Actions Tab:**
   - See all runs (successful/failed)
   - View logs
   - Check timing

2. **Streamlit App:**
   - View responses in real-time
   - See vendor status
   - Check follow-up counts

---

## 🔧 Troubleshooting <a name="troubleshooting"></a>

### Issue: GitHub Actions Not Running

**Check:**
1. Repository is PUBLIC (private requires paid plan)
2. Workflow file is in `.github/workflows/`
3. Secrets are added correctly
4. No syntax errors in YAML

**Solution:**
- Go to Actions → Enable workflows if disabled
- Check workflow syntax
- Manually trigger to test

### Issue: Email Check Fails

**Check:**
1. Gmail App Password is correct
2. IMAP is enabled in Gmail
3. No special characters in password

**Solution:**
- Generate new App Password
- Update GitHub secret
- Re-run workflow

### Issue: Supabase Connection Error

**Check:**
1. SUPABASE_URL is correct (https://xxxxx.supabase.co)
2. SUPABASE_KEY is the `anon` `public` key
3. Tables were created

**Solution:**
- Verify secrets match Supabase dashboard
- Re-run schema.sql in Supabase SQL Editor
- Check Supabase project is active

### Issue: Streamlit App Crashes

**Check:**
1. All secrets added correctly
2. requirements.txt has all packages
3. Database accessible

**Solution:**
- Check Streamlit logs (click "Manage app" → "Logs")
- Verify secrets syntax (TOML format)
- Restart app

---

## 🎯 Success Checklist

- [ ] Supabase project created
- [ ] Database schema deployed
- [ ] GitHub repository created
- [ ] Code pushed to GitHub
- [ ] GitHub secrets added (5 secrets)
- [ ] Streamlit app deployed
- [ ] Streamlit secrets added
- [ ] GitHub Actions workflow running
- [ ] Test: Create RFQ via app
- [ ] Test: Manually trigger workflow
- [ ] Verify: Check emails working
- [ ] Verify: Follow-ups working

---

## 💡 Tips for Production Use

1. **Monitor GitHub Actions:**
   - Check daily for failed runs
   - Review logs for issues

2. **Database Maintenance:**
   - Supabase FREE tier: 500MB limit
   - Archive old RFQs periodically
   - Export important data

3. **Email Best Practices:**
   - Don't exceed Gmail limits (500 emails/day)
   - Use professional email templates
   - Monitor spam complaints

4. **Cost Optimization:**
   - GitHub Actions: 2,000 free minutes/month
   - Each run: ~2 minutes
   - 30-minute interval: 48 runs/day = 96 minutes/day
   - Total: ~2,880 minutes/month (within limit!)

---

## 🆘 Need Help?

1. Check logs in GitHub Actions
2. Check logs in Streamlit Cloud
3. Review Supabase dashboard for database issues
4. Test components individually

---

## 🎉 You're Done!

Your RFQ Automation System is now running 24/7 completely FREE!

**What happens automatically:**
- Emails checked every 30 minutes
- Responses parsed and saved
- Follow-ups sent on schedule
- Everything logged and tracked

**What you can do manually:**
- Create RFQs via web interface
- View responses in real-time
- Generate comparison reports
- Override automation anytime

**Enjoy your fully automated RFQ system! 🚀**
