# ✅ Local Testing Checklist

Use this checklist to verify everything works:

## Pre-Test Setup
- [ ] Extracted zip file
- [ ] Navigated to rfq_streamlit folder
- [ ] Python 3.11+ installed (`python --version`)
- [ ] pip installed (`pip --version`)

## Installation
- [ ] Created virtual environment (`python -m venv venv`)
- [ ] Activated virtual environment (see `(venv)` in prompt)
- [ ] Installed dependencies (`pip install -r requirements.txt`)
- [ ] No installation errors

## App Startup
- [ ] Ran `streamlit run app.py` (or `./start.bat` on Windows)
- [ ] App started without errors
- [ ] Browser opened automatically to http://localhost:8501
- [ ] Dashboard page loaded

## UI Testing

### Dashboard Page
- [ ] See 4 metric cards (Active RFQs, Pending, Responses, Rate)
- [ ] See quick action buttons
- [ ] All buttons clickable
- [ ] Navigation works

### Create RFQ Page
- [ ] Page loads
- [ ] Can select "Manual Entry"
- [ ] Can add vendors (name + email)
- [ ] Can add items (name, description, qty, unit)
- [ ] Can set email subject/body/footer
- [ ] Can set deadline
- [ ] "Create & Send RFQ" button works
- [ ] Success message appears
- [ ] Balloons animation appears 🎈

### Active RFQs Page
- [ ] Page loads
- [ ] Created RFQ appears in list
- [ ] Can expand RFQ details
- [ ] Vendor table shows with "Pending" status
- [ ] Items table shows
- [ ] Progress bar displays (0/N vendors)
- [ ] "View Responses" button clickable

### Responses Page
- [ ] Page loads
- [ ] Can select RFQ from dropdown
- [ ] Shows "No responses yet" (expected)

### History Page
- [ ] Page loads
- [ ] Shows "Coming soon" message (expected)

### Settings Page
- [ ] Page loads
- [ ] Email fields populated
- [ ] API key fields populated
- [ ] "Save Settings" button works
- [ ] Success message on save

## Navigation
- [ ] Sidebar navigation works
- [ ] Can navigate between all pages
- [ ] Back/forward works
- [ ] No page load errors

## Database
- [ ] database/rfq_system.db file created
- [ ] RFQ data persists (refresh page, data still there)
- [ ] Can create multiple RFQs

## Performance
- [ ] Pages load in < 2 seconds
- [ ] No lag when clicking buttons
- [ ] No memory errors
- [ ] App responsive

## Cleanup
- [ ] Can stop app with Ctrl+C
- [ ] Terminal returns to normal
- [ ] Can restart app successfully

## Overall
- [ ] No critical errors
- [ ] All core features working
- [ ] Ready for production use

---

## Notes
Write any issues or observations here:




---

## Test Result
- [ ] ✅ PASSED - Ready to deploy to cloud!
- [ ] ⚠️  PARTIAL - Some issues, but usable
- [ ] ❌ FAILED - Needs fixes before deployment

**Date:** __________
**Tested by:** __________
