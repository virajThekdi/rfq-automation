# 🚀 RFQ Automation System - 24/7 Automated Procurement

A **fully automated** Request for Quotation (RFQ) management system with intelligent email monitoring, smart follow-ups, and AI-powered response parsing.

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://supabase.com/)

---

## ✨ Features

### 🎯 Core Functionality
- **RFQ Creation**: Upload Excel files or enter items manually
- **Automated Email Sending**: Send professional HTML emails to vendors via Gmail
- **Smart Email Monitoring**: Automatically check Gmail for vendor responses (24/7)
- **Intelligent Parsing**: Parse responses in multiple formats:
  - HTML tables (FREE - BeautifulSoup)
  - Excel files (FREE - pandas)
  - PDF documents (AI-powered)
  - Plain text (AI-powered with Gemini)
- **Automatic Follow-ups**: Smart reminder system with urgency levels
- **QCF Report Generation**: Side-by-side vendor comparison in Excel

### 🤖 24/7 Automation
- **Background Workers**: Check emails every 30 minutes via GitHub Actions
- **Smart Follow-ups**: Automatically send reminders based on time and deadline
- **Real-time Updates**: Database syncs between web app and workers
- **Zero Manual Work**: Completely hands-off after RFQ creation

### 💎 Smart Features
- **Follow-up Intelligence**:
  - Time-based intervals (12/24/48/72 hours)
  - Deadline-aware (stops after deadline)
  - Urgency levels (Blue → Orange → Red)
  - Max follow-up limits (prevents spam)
  
- **Cost Optimization**:
  - FREE for HTML/Excel parsing (rule-based)
  - AI only for complex formats (~$0.001-0.002 per parse)
  - Estimated: **$0.10-0.20/month** for 100 RFQs

---

## 🏗️ Architecture

```
┌────────────────────────────┐
│   STREAMLIT WEB APP        │
│   (User Interface)         │
│   • Create RFQs            │
│   • View Responses         │
│   • Generate Reports       │
└──────────┬─────────────────┘
           │
           │ (Shared Database)
           │
           ▼
    ┌──────────────┐
    │  SUPABASE    │
    │  PostgreSQL  │
    └──────┬───────┘
           │
           │
           ▼
┌────────────────────────────┐
│  GITHUB ACTIONS WORKER     │
│  (24/7 Automation)         │
│  • Email Monitoring        │
│  • Response Parsing        │
│  • Follow-up Sending       │
└────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
1. **GitHub Account** (FREE)
2. **Gmail Account** with App Password
3. **Gemini API Key** (FREE from [Google AI Studio](https://makersuite.google.com/app/apikey))
4. **Supabase Account** (FREE - 500MB database)

### Deploy in 15 Minutes (100% FREE!)

See **[📖 DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** for complete step-by-step instructions.

**TL;DR:**
1. Set up Supabase database
2. Push code to GitHub
3. Add GitHub secrets (5 credentials)
4. Deploy to Streamlit Cloud
5. Done! System runs 24/7 automatically ✅

---

## 📦 Project Structure

```
rfq_streamlit/
├── app.py                      # Main Streamlit dashboard
├── automation_worker.py        # 24/7 background worker
├── requirements.txt            # Python dependencies
│
├── .github/workflows/
│   └── rfq_automation.yml      # GitHub Actions config (24/7)
│
├── database/
│   ├── schema.sql              # PostgreSQL schema
│   └── db_manager.py           # Database operations
│
├── modules/
│   ├── email_sender.py         # Gmail SMTP integration
│   ├── email_generator.py      # HTML email templates
│   ├── email_monitor.py        # IMAP email checking
│   ├── followup_manager.py     # Smart follow-up logic
│   ├── parser_engine.py        # Response parsing
│   ├── format_detector.py      # Format detection
│   ├── ai_parser.py            # Gemini AI integration
│   └── qcf_enhanced.py         # Report generation
│
└── pages/
    ├── 1_📤_Create_RFQ.py      # RFQ creation + follow-up config
    ├── 2_📊_Active_RFQs.py     # Monitoring + manual controls
    ├── 3_💬_Responses.py       # View responses + reports
    ├── 4_📜_History.py         # Completed RFQs
    └── 5_⚙️_Settings.py        # Configuration
```

---

## 💡 How It Works

### 1️⃣ User Creates RFQ
- Upload Excel file or enter manually
- Configure follow-ups (count, interval)
- Set deadline (1-30 days)
- System sends emails immediately

### 2️⃣ Automated Email Monitoring (24/7)
- GitHub Actions runs every 30 minutes
- Connects to Gmail IMAP
- Searches for vendor replies
- Parses responses automatically:
  - HTML tables → BeautifulSoup (FREE)
  - Excel files → pandas (FREE)
  - PDFs → PyPDF2 + AI (low cost)
  - Plain text → Gemini AI (low cost)
- Saves to database
- Updates vendor status

### 3️⃣ Smart Follow-ups (24/7)
- Checks which vendors are pending
- Calculates time since last contact
- Sends reminders if:
  - Enough time passed (interval met)
  - Not exceeded max follow-ups
  - Deadline not passed
- Adds urgency based on time remaining:
  - 🟦 Blue: 3+ days remaining
  - 🟧 Orange: 1-3 days remaining
  - 🟥 Red: < 24 hours remaining

### 4️⃣ User Views Results
- Real-time dashboard shows responses
- Vendor status (pending/responded)
- Follow-up history
- Generate QCF comparison report

---

## 🎯 Use Cases

### Perfect For:
- **Small Businesses**: Automate procurement without hiring staff
- **Procurement Teams**: Handle 100+ RFQs with ease
- **Manufacturing**: Get quotes from multiple suppliers
- **Construction**: Compare subcontractor bids
- **Distributors**: Source products from vendors

### Not For:
- Enterprise with strict compliance (use dedicated ERP)
- Extremely high volume (1000+ RFQs/day)
- Industries requiring complex approval workflows

---

## 📊 Cost Breakdown

 Service | Free Tier | Cost |
---------|-----------|------|
 **Streamlit Cloud** | 1 app | **$0** |
 **GitHub Actions** | 2,000 min/month | **$0** |
 **Supabase** | 500MB database | **$0** |
 **Gemini AI** | HTML/Excel parsing | **$0** |
 **Gemini AI** | PDF/Text parsing | **~$0.10-0.20/month** |
 **TOTAL** | - | **~$0.10-0.20/month** |

**For 100 RFQs/month with mixed response formats**

---

## 🔒 Security

- ✅ Credentials stored as GitHub/Streamlit secrets
- ✅ Environment variables not committed to repo
- ✅ Gmail App Passwords (not real password)
- ✅ Supabase Row Level Security (RLS)
- ✅ HTTPS for all connections
- ✅ No sensitive data in logs

---

## 📈 Scalability

### Current Limits (FREE tier):
- **GitHub Actions**: 2,000 minutes/month
- **Supabase**: 500MB database
- **Gmail**: 500 emails/day send limit
- **Streamlit Cloud**: 1GB RAM, 1 CPU

### Expected Performance:
- **RFQs**: 500-1,000/month
- **Vendors**: 5,000-10,000 total
- **Responses**: 10,000-20,000/month
- **Storage**: ~100-200MB/year

### To Scale Beyond:
1. Upgrade Supabase ($25/month for 8GB)
2. Use dedicated SMTP service (SendGrid, Mailgun)
3. Optimize GitHub Actions schedule

---

## 🛠️ Tech Stack

### Frontend
- **Streamlit** - Web framework
- **Pandas** - Data manipulation
- **Plotly** - Visualizations

### Backend
- **Python 3.11+**
- **PostgreSQL** (Supabase)
- **SQLite** (local development)

### Email & Parsing
- **Gmail SMTP/IMAP**
- **BeautifulSoup** - HTML parsing
- **openpyxl** - Excel handling
- **PyPDF2** - PDF parsing
- **Gemini AI** - Unstructured text

### Automation
- **GitHub Actions** - 24/7 scheduling
- **Python-dotenv** - Environment management

---

## 📝 Development

### Local Setup

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/rfq-automation.git
cd rfq-automation

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your credentials

# Run Streamlit app
streamlit run app.py
```

### Test Automation Worker

```bash
# Check emails
python automation_worker.py check-emails

# Send follow-ups
python automation_worker.py send-followups

# Both
python automation_worker.py both
```

---

## 🐛 Troubleshooting

See **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** → Troubleshooting section

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📜 License

MIT License - See [LICENSE](LICENSE) file

---

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Powered by [Google Gemini AI](https://ai.google.dev/)
- Hosted on [Streamlit Cloud](https://streamlit.io/cloud)
- Database by [Supabase](https://supabase.com/)
- Automation via [GitHub Actions](https://github.com/features/actions)

---

## 📧 Support

For questions or issues:
1. Check [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
2. Review [GitHub Issues](https://github.com/YOUR_USERNAME/rfq-automation/issues)
3. Open a new issue

---

**Made with ❤️ for procurement automation**

🚀 **Deploy in 15 minutes • Run 24/7 • 100% FREE**
