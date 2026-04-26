# 🧪 Local Testing Guide - RFQ Streamlit App

## 📋 Pre-Test Checklist

Before testing, make sure you have:
- ✅ Python 3.11+ installed (check: `python --version`)
- ✅ pip installed (check: `pip --version`)
- ✅ 5-10 minutes for testing

---

## 🚀 Quick Start (5 Steps)

### Step 1: Extract & Navigate
```bash
# Extract the zip file
# Navigate to folder
cd rfq_streamlit
```

### Step 2: Create Virtual Environment
```bash
# Windows:
python -m venv venv
venv\Scripts\activate

# Mac/Linux:
python3 -m venv venv
source venv/bin/activate
```

**Success indicator:** You should see `(venv)` in your terminal prompt.

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed streamlit-1.32.0 pandas-2.2.3 ...
```

**If installation fails:**
```bash
# Try this:
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt --no-cache-dir
```

### Step 4: Configure Credentials

Edit the `.env` file:
```bash
# Open .env in any text editor
# Your credentials are already there!

EMAIL_ADDRESS=virajthekdi1@gmail.com
EMAIL_PASSWORD=tthe gtgf hdum kdqt
GEMINI_API_KEY=AIzaSyAwUraP4W2QSx1phKhOgyZwwEiJF3Zknbc
```

**✅ These are already configured!** Just verify they're correct.

### Step 5: Run the App
```bash
streamlit run app.py
```

**Expected output:**
```
You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

**Your browser should automatically open to:** `http://localhost:8501`

---

## 🎯 What to Test

### Test 1: Dashboard (Home Page)
✅ **Should see:**
- 4 metric cards (Active RFQs, Pending Responses, etc.)
- Quick action buttons
- Active RFQs overview (will be empty initially)

✅ **Try:**
- Click each quick action button
- Verify page navigation works

---

### Test 2: Create RFQ Page
✅ **Navigate to:** "📤 Create RFQ" (sidebar or button)

✅ **Test Manual Entry:**
1. Select "Manual Entry"
2. Add 2-3 vendors:
   - Name: Test Vendor 1, Email: test1@example.com
   - Name: Test Vendor 2, Email: test2@example.com
3. Add 2-3 items:
   - Item: Steel Rods, Desc: 16mm, Qty: 100, Unit: kg
   - Item: Cement, Desc: Grade 43, Qty: 50, Unit: bags
4. Configure email:
   - Subject: Test RFQ
   - Body: This is a test
   - Footer: Thank you
5. Set deadline: 3 days
6. Click "Create & Send RFQ"

✅ **Should see:**
- Success message: "RFQ #1 created successfully!"
- Balloons animation 🎈

**Note:** Emails won't actually be sent in local testing (that's OK!).

---

### Test 3: Active RFQs Page
✅ **Navigate to:** "📊 Active RFQs"

✅ **Should see:**
- Your test RFQ listed
- Vendor table with status "Pending"
- Items table
- Progress bar showing 0/2 vendors responded

✅ **Try:**
- Expand/collapse RFQ details
- Click "View Responses" button

---

### Test 4: Responses Page
✅ **Navigate to:** "💬 Responses"

✅ **Should see:**
- Dropdown to select RFQ
- Message: "No responses yet for this RFQ" (expected for new RFQ)

**Note:** To test responses, you'd need to manually add test data to database or wait for real vendor emails.

---

### Test 5: Settings Page
✅ **Navigate to:** "⚙️ Settings"

✅ **Should see:**
- Email configuration (pre-filled with your Gmail)
- AI configuration (Gemini key visible)
- "Save Settings" button

✅ **Try:**
- Change a setting
- Click "Save Settings"
- Verify success message

---

## 🐛 Troubleshooting

### App won't start
**Error:** `ModuleNotFoundError: No module named 'streamlit'`
**Fix:**
```bash
# Make sure virtual environment is activated
# You should see (venv) in prompt
pip install streamlit
```

**Error:** `[Errno 2] No such file or directory: 'database/schema.sql'`
**Fix:**
```bash
# Make sure you're in the rfq_streamlit folder
cd rfq_streamlit
streamlit run app.py
```

### Database errors
**Error:** `sqlite3.OperationalError: no such table: rfqs`
**Fix:**
```bash
# Delete database and restart (it will auto-recreate)
rm database/rfq_system.db
streamlit run app.py
```

### Import errors
**Error:** `ModuleNotFoundError: No module named 'modules'`
**Fix:**
```bash
# Make sure you're running from the correct directory
pwd  # Should show: .../rfq_streamlit
streamlit run app.py
```

### Port already in use
**Error:** `OSError: [Errno 48] Address already in use`
**Fix:**
```bash
# Use a different port
streamlit run app.py --server.port 8502
```

---

## ✅ Success Criteria

Your local test is successful if:
- ✅ App starts without errors
- ✅ All 5 pages load correctly
- ✅ Can create a test RFQ
- ✅ RFQ appears in "Active RFQs" page
- ✅ Dashboard shows correct metrics
- ✅ Navigation between pages works

---

## 🚀 Next Steps After Testing

Once local testing works:

1. **Option A: Keep using locally**
   - Run `streamlit run app.py` whenever you need it
   - Keep terminal open while using
   - PC must stay on for monitoring

2. **Option B: Deploy to cloud (Recommended)**
   - See `DEPLOYMENT_GUIDE.md`
   - Push to GitHub
   - Deploy to Streamlit Cloud (FREE)
   - App runs 24/7, PC can be off

---

## 🔥 Quick Commands

```bash
# Start app
streamlit run app.py

# Start on different port
streamlit run app.py --server.port 8502

# Stop app
Ctrl + C (in terminal)

# Deactivate virtual environment
deactivate

# Reactivate later
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

---

## 📊 Expected Performance

- **Startup time:** 2-5 seconds
- **Page load:** < 1 second
- **Create RFQ:** < 2 seconds
- **Memory usage:** ~100-200 MB

---

## ❓ FAQ

**Q: Do I need to keep the terminal open?**
A: Yes, for local testing. The app stops when you close the terminal or press Ctrl+C.

**Q: Will it send actual emails?**
A: Yes, if your Gmail credentials are correct and the background scheduler is running. For pure UI testing, emails won't send unless the scheduler is active.

**Q: Can others access my local app?**
A: Only if they're on the same network and you share the Network URL. It's not accessible from the internet.

**Q: How do I stop the app?**
A: Press `Ctrl + C` in the terminal.

**Q: Can I test without Gmail credentials?**
A: Yes! The UI will work fine. You just won't be able to send actual emails.

---

## 🎉 You're Ready!

Happy testing! If everything works locally, you're ready to deploy to the cloud.
