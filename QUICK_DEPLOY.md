# 🚀 QUICK DEPLOYMENT GUIDE - Your Supabase Already Set Up!

Since you already have Supabase configured, deployment is even simpler!

---

## ✅ WHAT YOU ALREADY HAVE:

- ✅ Supabase Database: `https://rmnapdydwcnqxztgphvc.supabase.co`
- ✅ Email: `virajthekdi1@gmail.com` (with App Password)
- ✅ Gemini API Key: Configured
- ✅ All code files ready
- ✅ .env file configured

**You're 90% done! Just 3 steps left:**

---

## 📋 3 SIMPLE STEPS TO DEPLOY (10 MINUTES):

### STEP 1: Ensure Supabase Has Your Schema (2 minutes)

1. Go to https://supabase.com/dashboard/project/rmnapdydwcnqxztgphvc
2. Click "SQL Editor" (left sidebar)
3. Copy the contents of your `database/schema.sql` file
4. Paste into SQL Editor
5. Click "Run"
6. Verify tables created: rfqs, items, vendors, responses, quotations, settings

**If tables already exist, you'll see "already exists" errors - that's OK!**

---

### STEP 2: Push to GitHub (3 minutes)

```bash
# Navigate to your project
cd /Workspace/Users/virajthekdi1@gmail.com/rfq_streamlit

# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "RFQ Automation System - 24/7 with Supabase"

# Create GitHub repo first at: https://github.com/new
# Then add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/rfq-automation.git

# Push
git branch -M main
git push -u origin main
```

**Important:** Make your repo PUBLIC (for free GitHub Actions) or use private with paid plan.

---

### STEP 3A: Add GitHub Secrets (2 minutes)

1. Go to your GitHub repository
2. Click: **Settings** → **Secrets and variables** → **Actions**
3. Click "New repository secret"
4. Add these 5 secrets (one by one):

 Secret Name | Value |
-------------|-------|
 `EMAIL_ADDRESS` | `virajthekdi1@gmail.com` |
 `EMAIL_PASSWORD` | `tthe gtgf hdum kdqt` |
 `GEMINI_API_KEY` | `AIzaSyAwUraP4W2QSx1phKhOgyZwwEiJF3Zknbc` |
 `SUPABASE_URL` | `https://rmnapdydwcnqxztgphvc.supabase.co` |
 `SUPABASE_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJtbmFwZHlkd2NucXh6dGdwaHZjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU4MzgxMzUsImV4cCI6MjA2MTQxNDEzNX0.sb_publishable_4iNiPXExr5N03rAbZEM2WQ_PNK8Obav` |

---

### STEP 3B: Deploy to Streamlit Cloud (3 minutes)

1. Go to https://share.streamlit.io/
2. Sign in with GitHub
3. Click "New app"
4. Fill in:
   - **Repository:** YOUR_USERNAME/rfq-automation
   - **Branch:** main
   - **Main file path:** app.py
5. Click "Advanced settings"
6. In "Secrets" box, paste:

```toml
EMAIL_ADDRESS = "virajthekdi1@gmail.com"
EMAIL_PASSWORD = "tthe gtgf hdum kdqt"
GEMINI_API_KEY = "AIzaSyAwUraP4W2QSx1phKhOgyZwwEiJF3Zknbc"
SUPABASE_URL = "https://rmnapdydwcnqxztgphvc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJtbmFwZHlkd2NucXh6dGdwaHZjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU4MzgxMzUsImV4cCI6MjA2MTQxNDEzNX0.sb_publishable_4iNiPXExr5N03rAbZEM2WQ_PNK8Obav"
```

7. Click **Deploy!**
8. Wait 2-3 minutes
9. Your app will be live at: `https://your-app-name.streamlit.app`

---

## 🤖 VERIFY 24/7 AUTOMATION:

After deployment:

1. Go to your GitHub repository
2. Click **Actions** tab
3. You should see: "RFQ Email Automation - 24/7"
4. Click on it
5. Click "Run workflow" → "Run workflow" to test manually
6. Watch the logs - should complete successfully!

**Now it will run automatically every 30 minutes! 🎉**

---

## ✅ SUCCESS CHECKLIST:

After completing above steps, verify:

- [ ] Supabase tables exist (rfqs, items, vendors, responses, quotations)
- [ ] Code pushed to GitHub (public repo)
- [ ] 5 GitHub secrets added
- [ ] Streamlit app deployed and accessible
- [ ] GitHub Actions workflow visible in Actions tab
- [ ] Manual workflow run completes successfully
- [ ] App shows empty dashboard (ready for first RFQ)

---

## 🎯 WHAT HAPPENS NOW:

### Automatic (24/7 - No Human Needed):
✅ **Every 30 minutes:**
   - Check Gmail for vendor responses
   - Parse responses (HTML, Excel, PDF)
   - Save to Supabase database
   - Send follow-up reminders (if needed)
   - Update vendor status

### Manual (Through Web App):
✅ **You can:**
   - Create new RFQs (upload Excel or enter manually)
   - Configure follow-up settings (2 reminders, 24h interval)
   - View responses in real-time
   - Generate QCF comparison reports
   - Manually trigger email checks or follow-ups

---

## 💰 COST:

- **Streamlit Cloud:** FREE (1 app)
- **GitHub Actions:** FREE (2,000 minutes/month)
- **Supabase:** FREE (500MB - you already have this!)
- **Gemini AI:** ~$0.10-0.20/month (for PDF/text parsing)

**Total: ~$0.10-0.20/month** 🎉

---

## 🆘 TROUBLESHOOTING:

### GitHub Actions Not Running?
- Check repo is PUBLIC (or upgrade to GitHub Team)
- Verify all 5 secrets added correctly
- Manually trigger workflow to test

### Streamlit App Error?
- Click "Manage app" → "Logs"
- Check if all secrets match exactly
- Verify Supabase is accessible

### Database Connection Error?
- Verify Supabase project is active
- Check API key is the `anon` `public` key (not `service_role`)
- Test connection from Supabase dashboard

---

## 🎉 YOU'RE DONE!

Your RFQ system is now:
- ✅ Running 24/7 automatically
- ✅ Checking emails every 30 minutes
- ✅ Sending smart follow-ups
- ✅ Costing almost nothing ($0.10-0.20/month)

**Access your app at:** `https://your-app-name.streamlit.app`

**Monitor automation at:** `https://github.com/YOUR_USERNAME/rfq-automation/actions`

---

## 📞 NEXT STEPS:

1. Create your first test RFQ
2. Send to 2-3 test vendors
3. Reply to yourself (from vendor email)
4. Wait 30 min (or manually trigger GitHub Action)
5. Check responses appear in app!

**Enjoy your automated procurement system! 🚀**
