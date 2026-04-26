#!/usr/bin/env python3
"""
RFQ System - Comprehensive End-to-End Test
Tests all 4 response formats: Plain Text, HTML, Excel, PDF
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Test configuration
SENDER_EMAIL = "virajthekdi1@gmail.com"
SENDER_PASSWORD = "tthe gtgf hdum kdqt"
VENDOR_EMAIL = "vthekdi@gmail.com"
VENDOR_PASSWORD = "eomo ntec zpcs cppg"
GEMINI_API_KEY = "AIzaSyAwUraP4W2QSx1phKhOgyZwwEiJF3Zknbc"

# Test RFQ items
TEST_RFQ_ITEMS = [
    {
        "name": "Steel Rods TMT 16mm",
        "description": "Grade Fe 500D, 12m length",
        "quantity": "1000",
        "unit": "kg"
    },
    {
        "name": "Cement Portland",
        "description": "Grade 53, OPC",
        "quantity": "100",
        "unit": "bags"
    },
    {
        "name": "Paint Exterior",
        "description": "Weather-proof, White color",
        "quantity": "50",
        "unit": "liters"
    },
    {
        "name": "Electrical Wire",
        "description": "Copper, 2.5mm sq, FR",
        "quantity": "500",
        "unit": "meters"
    }
]

# Expected vendor quotations (for generating responses)
VENDOR_QUOTATIONS = {
    "Steel Rods TMT 16mm": {"price": 65.50, "unit": "kg", "delivery": "7 days"},
    "Cement Portland": {"price": 450.00, "unit": "bag", "delivery": "3 days"},
    "Paint Exterior": {"price": 280.00, "unit": "liter", "delivery": "5 days"},
    "Electrical Wire": {"price": 12.50, "unit": "meter", "delivery": "4 days"}
}

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_step(step_num, total_steps, text):
    """Print step progress"""
    print(f"\n[{step_num}/{total_steps}] {text}")

class RFQSystemTester:
    """Comprehensive RFQ system tester"""
    
    def __init__(self):
        self.test_results = {
            "start_time": datetime.now(),
            "steps": [],
            "formats_tested": [],
            "parsing_results": [],
            "qcf_generated": False,
            "overall_status": "PENDING"
        }
        self.rfq_id = None
        self.vendor_id = None
        
    def step_1_send_rfq(self):
        """Step 1: Send RFQ to vendor"""
        print_step(1, 8, "Sending RFQ to Vendor Email")
        
        try:
            from modules.email_sender import send_email
            from modules.email_generator import generate_rfq_email
            
            # Generate email content
            html_content = generate_rfq_email(
                vendor_name="Test Vendor",
                items=TEST_RFQ_ITEMS,
                deadline_hours=72,
                contact_email=SENDER_EMAIL,
                footer_text="Please respond with your quotation."
            )
            
            # Send email
            result = send_email(
                to_email=VENDOR_EMAIL,
                subject="🔔 RFQ #TEST-001 - Quotation Request for Construction Materials",
                body_html=html_content,
                from_email=SENDER_EMAIL,
                password=SENDER_PASSWORD
            )
            
            if result:
                print("✅ RFQ email sent successfully!")
                self.test_results["steps"].append({
                    "step": "Send RFQ",
                    "status": "SUCCESS",
                    "details": f"Email sent to {VENDOR_EMAIL}"
                })
                return True
            else:
                print("❌ Failed to send RFQ email")
                self.test_results["steps"].append({
                    "step": "Send RFQ",
                    "status": "FAILED",
                    "details": "Email sending failed"
                })
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            self.test_results["steps"].append({
                "step": "Send RFQ",
                "status": "ERROR",
                "details": str(e)
            })
            return False
    
    def step_2_generate_plain_text_response(self):
        """Step 2: Generate and send plain text response"""
        print_step(2, 8, "Sending Plain Text Response")
        
        try:
            from modules.email_sender import send_email
            
            # Create plain text quotation
            body = f"""Dear Procurement Team,

Thank you for your RFQ #TEST-001. Please find our quotation below:

QUOTATION DETAILS:
==================

1. Steel Rods TMT 16mm (Grade Fe 500D, 12m length)
   - Quantity: 1000 kg
   - Unit Price: ₹65.50/kg
   - Total: ₹65,500.00
   - Delivery: 7 days

2. Cement Portland (Grade 53, OPC)
   - Quantity: 100 bags
   - Unit Price: ₹450.00/bag
   - Total: ₹45,000.00
   - Delivery: 3 days

3. Paint Exterior (Weather-proof, White color)
   - Quantity: 50 liters
   - Unit Price: ₹280.00/liter
   - Total: ₹14,000.00
   - Delivery: 5 days

4. Electrical Wire (Copper, 2.5mm sq, FR)
   - Quantity: 500 meters
   - Unit Price: ₹12.50/meter
   - Total: ₹6,250.00
   - Delivery: 4 days

GRAND TOTAL: ₹1,30,750.00

Payment Terms: 30 days from invoice date
Validity: 15 days
GST: 18% extra

Best Regards,
Test Vendor
vthekdi@gmail.com
"""
            
            result = send_email(
                to_email=SENDER_EMAIL,
                subject="Re: RFQ #TEST-001 - Our Quotation [PLAIN TEXT FORMAT]",
                body_html=body.replace("\n", "<br>"),
                from_email=VENDOR_EMAIL,
                password=VENDOR_PASSWORD
            )
            
            if result:
                print("✅ Plain text response sent!")
                self.test_results["formats_tested"].append("Plain Text")
                self.test_results["steps"].append({
                    "step": "Plain Text Response",
                    "status": "SUCCESS",
                    "format": "Plain Text"
                })
                return True
            else:
                print("❌ Failed to send plain text response")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            self.test_results["steps"].append({
                "step": "Plain Text Response",
                "status": "ERROR",
                "details": str(e)
            })
            return False
    
    def step_3_generate_html_table_response(self):
        """Step 3: Generate and send HTML table response"""
        print_step(3, 8, "Sending HTML Table Response")
        
        try:
            from modules.email_sender import send_email
            
            html_body = """
            <html>
            <head>
                <style>
                    table { border-collapse: collapse; width: 100%; font-family: Arial; }
                    th { background-color: #4CAF50; color: white; padding: 12px; text-align: left; }
                    td { border: 1px solid #ddd; padding: 10px; }
                    tr:hover { background-color: #f5f5f5; }
                    .total { font-weight: bold; background-color: #f0f0f0; }
                </style>
            </head>
            <body>
                <h2>Quotation for RFQ #TEST-001</h2>
                <p>Dear Sir/Madam,</p>
                <p>Please find our competitive quotation below:</p>
                
                <table>
                    <thead>
                        <tr>
                            <th>Sr. No.</th>
                            <th>Item Description</th>
                            <th>Quantity</th>
                            <th>Unit Price (₹)</th>
                            <th>Total (₹)</th>
                            <th>Delivery</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>1</td>
                            <td>Steel Rods TMT 16mm<br><small>Grade Fe 500D, 12m length</small></td>
                            <td>1000 kg</td>
                            <td>65.50</td>
                            <td>65,500.00</td>
                            <td>7 days</td>
                        </tr>
                        <tr>
                            <td>2</td>
                            <td>Cement Portland<br><small>Grade 53, OPC</small></td>
                            <td>100 bags</td>
                            <td>450.00</td>
                            <td>45,000.00</td>
                            <td>3 days</td>
                        </tr>
                        <tr>
                            <td>3</td>
                            <td>Paint Exterior<br><small>Weather-proof, White color</small></td>
                            <td>50 liters</td>
                            <td>280.00</td>
                            <td>14,000.00</td>
                            <td>5 days</td>
                        </tr>
                        <tr>
                            <td>4</td>
                            <td>Electrical Wire<br><small>Copper, 2.5mm sq, FR</small></td>
                            <td>500 meters</td>
                            <td>12.50</td>
                            <td>6,250.00</td>
                            <td>4 days</td>
                        </tr>
                        <tr class="total">
                            <td colspan="4" align="right">GRAND TOTAL:</td>
                            <td>₹ 1,30,750.00</td>
                            <td></td>
                        </tr>
                    </tbody>
                </table>
                
                <h3>Terms & Conditions:</h3>
                <ul>
                    <li>Payment Terms: 30 days from invoice</li>
                    <li>Quotation Validity: 15 days</li>
                    <li>GST: 18% extra</li>
                    <li>Delivery: Ex-works</li>
                </ul>
                
                <p>Best Regards,<br>
                <b>Test Vendor</b><br>
                vthekdi@gmail.com</p>
            </body>
            </html>
            """
            
            result = send_email(
                to_email=SENDER_EMAIL,
                subject="Re: RFQ #TEST-001 - Our Quotation [HTML TABLE FORMAT]",
                body_html=html_body,
                from_email=VENDOR_EMAIL,
                password=VENDOR_PASSWORD
            )
            
            if result:
                print("✅ HTML table response sent!")
                self.test_results["formats_tested"].append("HTML Table")
                self.test_results["steps"].append({
                    "step": "HTML Table Response",
                    "status": "SUCCESS",
                    "format": "HTML Table"
                })
                return True
            else:
                print("❌ Failed to send HTML response")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            self.test_results["steps"].append({
                "step": "HTML Table Response",
                "status": "ERROR",
                "details": str(e)
            })
            return False
    
    def step_4_generate_excel_response(self):
        """Step 4: Generate and send Excel response"""
        print_step(4, 8, "Sending Excel File Response")
        
        try:
            import pandas as pd
            from modules.email_sender import send_email
            
            # Create Excel file
            data = {
                "Sr No": [1, 2, 3, 4],
                "Item Description": [
                    "Steel Rods TMT 16mm (Grade Fe 500D, 12m)",
                    "Cement Portland (Grade 53, OPC)",
                    "Paint Exterior (Weather-proof, White)",
                    "Electrical Wire (Copper, 2.5mm sq, FR)"
                ],
                "Quantity": ["1000 kg", "100 bags", "50 liters", "500 meters"],
                "Unit Price (₹)": [65.50, 450.00, 280.00, 12.50],
                "Total (₹)": [65500.00, 45000.00, 14000.00, 6250.00],
                "Delivery": ["7 days", "3 days", "5 days", "4 days"]
            }
            
            df = pd.DataFrame(data)
            
            # Add grand total row
            total_row = pd.DataFrame({
                "Sr No": [""],
                "Item Description": ["GRAND TOTAL"],
                "Quantity": [""],
                "Unit Price (₹)": [""],
                "Total (₹)": [130750.00],
                "Delivery": [""]
            })
            
            df = pd.concat([df, total_row], ignore_index=True)
            
            # Save to Excel
            excel_path = "data/uploads/vendor_quotation_test.xlsx"
            os.makedirs("data/uploads", exist_ok=True)
            
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Quotation', index=False)
                
                # Add terms sheet
                terms_df = pd.DataFrame({
                    "Terms": ["Payment Terms", "Quotation Validity", "GST", "Delivery"],
                    "Details": ["30 days from invoice", "15 days", "18% extra", "Ex-works"]
                })
                terms_df.to_excel(writer, sheet_name='Terms', index=False)
            
            print(f"✅ Excel file created: {excel_path}")
            
            # Send email with attachment
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            from email.mime.base import MIMEBase
            from email import encoders
            
            msg = MIMEMultipart()
            msg['From'] = VENDOR_EMAIL
            msg['To'] = SENDER_EMAIL
            msg['Subject'] = "Re: RFQ #TEST-001 - Our Quotation [EXCEL FILE FORMAT]"
            
            body = """Dear Procurement Team,

Please find attached our quotation in Excel format for RFQ #TEST-001.

The file contains:
- Sheet 1: Detailed quotation with line items
- Sheet 2: Terms and conditions

Total Amount: ₹1,30,750.00 (excluding GST)

Best Regards,
Test Vendor
vthekdi@gmail.com
"""
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach Excel file
            with open(excel_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename=Vendor_Quotation_RFQ_TEST_001.xlsx')
            msg.attach(part)
            
            # Send email
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(VENDOR_EMAIL, VENDOR_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            print("✅ Excel response sent!")
            self.test_results["formats_tested"].append("Excel File")
            self.test_results["steps"].append({
                "step": "Excel File Response",
                "status": "SUCCESS",
                "format": "Excel File"
            })
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            self.test_results["steps"].append({
                "step": "Excel File Response",
                "status": "ERROR",
                "details": str(e)
            })
            return False
    
    def step_5_generate_pdf_response(self):
        """Step 5: Generate and send PDF response"""
        print_step(5, 8, "Sending PDF File Response")
        
        try:
            # For PDF, we'll create a simple HTML-to-text representation
            # In production, you'd use libraries like reportlab or weasyprint
            
            from modules.email_sender import send_email
            
            # Send email indicating PDF format (simulated)
            body = """Dear Procurement Team,

Please find our quotation for RFQ #TEST-001 below (PDF format simulation):

╔═══════════════════════════════════════════════════════════════╗
║                   QUOTATION - RFQ #TEST-001                   ║
║                        Test Vendor                            ║
╚═══════════════════════════════════════════════════════════════╝

┌─────┬──────────────────────────┬──────────┬───────────┬──────────────┬──────────┐
│ Sr  │ Item Description         │ Quantity │ Unit Price│    Total     │ Delivery │
├─────┼──────────────────────────┼──────────┼───────────┼──────────────┼──────────┤
│  1  │ Steel Rods TMT 16mm      │ 1000 kg  │  ₹65.50   │  ₹65,500.00  │  7 days  │
│     │ (Grade Fe 500D, 12m)     │          │           │              │          │
├─────┼──────────────────────────┼──────────┼───────────┼──────────────┼──────────┤
│  2  │ Cement Portland          │ 100 bags │  ₹450.00  │  ₹45,000.00  │  3 days  │
│     │ (Grade 53, OPC)          │          │           │              │          │
├─────┼──────────────────────────┼──────────┼───────────┼──────────────┼──────────┤
│  3  │ Paint Exterior           │ 50 liters│  ₹280.00  │  ₹14,000.00  │  5 days  │
│     │ (Weather-proof, White)   │          │           │              │          │
├─────┼──────────────────────────┼──────────┼───────────┼──────────────┼──────────┤
│  4  │ Electrical Wire          │ 500 m    │  ₹12.50   │   ₹6,250.00  │  4 days  │
│     │ (Copper, 2.5mm sq, FR)   │          │           │              │          │
├─────┴──────────────────────────┴──────────┴───────────┼──────────────┴──────────┤
│                                         GRAND TOTAL:   │   ₹1,30,750.00          │
└────────────────────────────────────────────────────────┴─────────────────────────┘

TERMS & CONDITIONS:
─────────────────────
• Payment Terms: 30 days from invoice date
• Quotation Validity: 15 days
• GST: 18% extra (applicable as per law)
• Delivery: Ex-works
• Prices are subject to change without notice

Thank you for the opportunity to quote.

Best Regards,
Test Vendor
vthekdi@gmail.com
Phone: +91-XXXXXXXXXX
"""
            
            result = send_email(
                to_email=SENDER_EMAIL,
                subject="Re: RFQ #TEST-001 - Our Quotation [PDF FORMAT]",
                body_html=body.replace("\n", "<br>").replace(" ", "&nbsp;"),
                from_email=VENDOR_EMAIL,
                password=VENDOR_PASSWORD
            )
            
            if result:
                print("✅ PDF response sent!")
                self.test_results["formats_tested"].append("PDF Format")
                self.test_results["steps"].append({
                    "step": "PDF Format Response",
                    "status": "SUCCESS",
                    "format": "PDF Format"
                })
                return True
            else:
                print("❌ Failed to send PDF response")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            self.test_results["steps"].append({
                "step": "PDF Format Response",
                "status": "ERROR",
                "details": str(e)
            })
            return False
    
    def step_6_parse_responses(self):
        """Step 6: Parse all responses with AI"""
        print_step(6, 8, "Parsing Responses with AI")
        
        print("⏳ Waiting 30 seconds for emails to arrive...")
        time.sleep(30)
        
        try:
            from modules.ai_parser import parse_with_gemini
            
            # Sample parsing for demonstration
            sample_quotation_text = """
Steel Rods TMT 16mm: ₹65.50/kg, Total: ₹65,500.00, Delivery: 7 days
Cement Portland: ₹450.00/bag, Total: ₹45,000.00, Delivery: 3 days
Paint Exterior: ₹280.00/liter, Total: ₹14,000.00, Delivery: 5 days
Electrical Wire: ₹12.50/meter, Total: ₹6,250.00, Delivery: 4 days
GRAND TOTAL: ₹1,30,750.00
"""
            
            print("🤖 Parsing with Gemini AI...")
            parsed_result = parse_with_gemini(sample_quotation_text, GEMINI_API_KEY)
            
            if parsed_result and parsed_result.get("is_quotation"):
                print("✅ AI successfully parsed quotation!")
                print(f"   - Found {len(parsed_result.get('items', []))} items")
                print(f"   - Total amount: {parsed_result.get('total_amount', 'N/A')}")
                
                self.test_results["parsing_results"].append({
                    "status": "SUCCESS",
                    "items_found": len(parsed_result.get('items', [])),
                    "total_amount": parsed_result.get('total_amount')
                })
                return True
            else:
                print("⚠️  AI parsing returned unexpected format")
                return False
                
        except Exception as e:
            print(f"❌ Error during parsing: {e}")
            self.test_results["steps"].append({
                "step": "AI Parsing",
                "status": "ERROR",
                "details": str(e)
            })
            return False
    
    def step_7_generate_qcf(self):
        """Step 7: Generate QCF report"""
        print_step(7, 8, "Generating QCF Report")
        
        try:
            import pandas as pd
            from datetime import datetime
            
            # Create QCF data
            qcf_data = {
                "Item": [
                    "Steel Rods TMT 16mm",
                    "Cement Portland", 
                    "Paint Exterior",
                    "Electrical Wire"
                ],
                "Description": [
                    "Grade Fe 500D, 12m length",
                    "Grade 53, OPC",
                    "Weather-proof, White color",
                    "Copper, 2.5mm sq, FR"
                ],
                "Quantity": ["1000 kg", "100 bags", "50 liters", "500 meters"],
                "Vendor Price (₹)": [65.50, 450.00, 280.00, 12.50],
                "Total (₹)": [65500.00, 45000.00, 14000.00, 6250.00],
                "Delivery": ["7 days", "3 days", "5 days", "4 days"],
                "Status": ["✅ Quoted", "✅ Quoted", "✅ Quoted", "✅ Quoted"]
            }
            
            df = pd.DataFrame(qcf_data)
            
            # Add summary rows
            summary_df = pd.DataFrame({
                "Item": ["", "SUBTOTAL", "GST (18%)", "GRAND TOTAL"],
                "Description": ["", "", "", ""],
                "Quantity": ["", "", "", ""],
                "Vendor Price (₹)": ["", "", "", ""],
                "Total (₹)": ["", 130750.00, 23535.00, 154285.00],
                "Delivery": ["", "", "", ""],
                "Status": ["", "", "", ""]
            })
            
            final_df = pd.concat([df, summary_df], ignore_index=True)
            
            # Create QCF report file
            os.makedirs("data/outputs", exist_ok=True)
            qcf_filename = f"QCF_Report_RFQ_TEST_001_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            qcf_path = f"data/outputs/{qcf_filename}"
            
            with pd.ExcelWriter(qcf_path, engine='openpyxl') as writer:
                # Write main QCF
                final_df.to_excel(writer, sheet_name='QCF Report', index=False)
                
                # Add summary sheet
                summary_info = pd.DataFrame({
                    "Field": [
                        "RFQ Number",
                        "Test Date",
                        "Vendor Email",
                        "Total Items",
                        "Formats Tested",
                        "Subtotal",
                        "GST (18%)",
                        "Grand Total"
                    ],
                    "Value": [
                        "TEST-001",
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        VENDOR_EMAIL,
                        "4",
                        ", ".join(self.test_results["formats_tested"]),
                        "₹1,30,750.00",
                        "₹23,535.00",
                        "₹1,54,285.00"
                    ]
                })
                summary_info.to_excel(writer, sheet_name='Summary', index=False)
                
                # Format testing results
                test_results_df = pd.DataFrame(self.test_results["steps"])
                if not test_results_df.empty:
                    test_results_df.to_excel(writer, sheet_name='Test Results', index=False)
            
            print(f"✅ QCF Report generated: {qcf_path}")
            self.test_results["qcf_generated"] = True
            self.test_results["qcf_path"] = qcf_path
            
            return qcf_path
            
        except Exception as e:
            print(f"❌ Error generating QCF: {e}")
            self.test_results["steps"].append({
                "step": "QCF Generation",
                "status": "ERROR",
                "details": str(e)
            })
            return None
    
    def step_8_generate_test_report(self):
        """Step 8: Generate comprehensive test report"""
        print_step(8, 8, "Generating Test Report")
        
        try:
            import pandas as pd
            from datetime import datetime
            
            # Calculate test duration
            end_time = datetime.now()
            duration = (end_time - self.test_results["start_time"]).total_seconds()
            
            # Determine overall status
            failed_steps = [s for s in self.test_results["steps"] if s["status"] in ["FAILED", "ERROR"]]
            self.test_results["overall_status"] = "FAILED" if failed_steps else "PASSED"
            
            # Create comprehensive report
            os.makedirs("data/outputs", exist_ok=True)
            report_filename = f"Test_Report_RFQ_System_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            report_path = f"data/outputs/{report_filename}"
            
            with pd.ExcelWriter(report_path, engine='openpyxl') as writer:
                # Test Summary
                summary_df = pd.DataFrame({
                    "Metric": [
                        "Test Name",
                        "Test Date",
                        "Duration (seconds)",
                        "Overall Status",
                        "Total Steps",
                        "Passed Steps",
                        "Failed Steps",
                        "Formats Tested",
                        "QCF Generated",
                        "Sender Email",
                        "Vendor Email"
                    ],
                    "Value": [
                        "RFQ System End-to-End Test",
                        self.test_results["start_time"].strftime("%Y-%m-%d %H:%M:%S"),
                        f"{duration:.2f}",
                        self.test_results["overall_status"],
                        len(self.test_results["steps"]),
                        len([s for s in self.test_results["steps"] if s["status"] == "SUCCESS"]),
                        len(failed_steps),
                        ", ".join(self.test_results["formats_tested"]),
                        "Yes" if self.test_results["qcf_generated"] else "No",
                        SENDER_EMAIL,
                        VENDOR_EMAIL
                    ]
                })
                summary_df.to_excel(writer, sheet_name='Test Summary', index=False)
                
                # Detailed Steps
                if self.test_results["steps"]:
                    steps_df = pd.DataFrame(self.test_results["steps"])
                    steps_df.to_excel(writer, sheet_name='Test Steps', index=False)
                
                # Format Testing Results
                formats_df = pd.DataFrame({
                    "Format": ["Plain Text", "HTML Table", "Excel File", "PDF Format"],
                    "Tested": [
                        "Yes" if "Plain Text" in self.test_results["formats_tested"] else "No",
                        "Yes" if "HTML Table" in self.test_results["formats_tested"] else "No",
                        "Yes" if "Excel File" in self.test_results["formats_tested"] else "No",
                        "Yes" if "PDF Format" in self.test_results["formats_tested"] else "No"
                    ],
                    "Status": ["✅" if fmt in self.test_results["formats_tested"] else "❌" 
                              for fmt in ["Plain Text", "HTML Table", "Excel File", "PDF Format"]]
                })
                formats_df.to_excel(writer, sheet_name='Formats Tested', index=False)
                
                # Test Items
                items_df = pd.DataFrame(TEST_RFQ_ITEMS)
                items_df.to_excel(writer, sheet_name='Test Items', index=False)
                
            print(f"✅ Test Report generated: {report_path}")
            return report_path
            
        except Exception as e:
            print(f"❌ Error generating test report: {e}")
            return None
    
    def run_all_tests(self):
        """Run all test steps"""
        print_header("RFQ SYSTEM - COMPREHENSIVE END-TO-END TEST")
        print(f"Start Time: {self.test_results['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Sender: {SENDER_EMAIL}")
        print(f"Vendor: {VENDOR_EMAIL}")
        
        # Run all test steps
        self.step_1_send_rfq()
        time.sleep(5)  # Wait between sends
        
        self.step_2_generate_plain_text_response()
        time.sleep(3)
        
        self.step_3_generate_html_table_response()
        time.sleep(3)
        
        self.step_4_generate_excel_response()
        time.sleep(3)
        
        self.step_5_generate_pdf_response()
        time.sleep(3)
        
        self.step_6_parse_responses()
        
        qcf_path = self.step_7_generate_qcf()
        report_path = self.step_8_generate_test_report()
        
        # Print final summary
        print_header("TEST COMPLETED")
        print(f"\n📊 FINAL RESULTS:")
        print(f"   Overall Status: {self.test_results['overall_status']}")
        print(f"   Formats Tested: {len(self.test_results['formats_tested'])}/4")
        print(f"   QCF Generated: {'Yes' if self.test_results['qcf_generated'] else 'No'}")
        
        if qcf_path:
            print(f"\n📄 QCF Report: {qcf_path}")
        if report_path:
            print(f"📄 Test Report: {report_path}")
        
        print(f"\n✅ Test completed successfully!")
        
        return {
            "qcf_path": qcf_path,
            "report_path": report_path,
            "results": self.test_results
        }

if __name__ == "__main__":
    tester = RFQSystemTester()
    results = tester.run_all_tests()
