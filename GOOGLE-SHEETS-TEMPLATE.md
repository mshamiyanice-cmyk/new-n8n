# Google Sheets Dashboard Template for Sambora Leads

## Setup Instructions

### Step 1: Create New Google Sheet

1. Go to [Google Sheets](https://sheets.google.com)
2. Click "+ Blank" to create new spreadsheet
3. Name it: **"Sambora Leads - Inquiry Management"**

---

## Sheet 1: Leads Dashboard

### Column Headers (Row 1):

| A | B | C | D | E | F | G | H | I | J | K | L | M | N |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Timestamp | Lead Name | Email | Travel Dates | Group Size | Need Permits | Lead Score | Priority | Assigned To | Status | Source | Session ID | Response Time | Special Notes |

### Column Details:

1. **A: Timestamp**
   - Format: `yyyy-MM-dd HH:mm:ss`
   - When lead was received

2. **B: Lead Name**
   - Customer's name
   - Text format

3. **C: Email**
   - Customer's email address
   - Email format (validates automatically)

4. **D: Travel Dates**
   - Preferred travel dates
   - Text or Date format

5. **E: Group Size**
   - Number of travelers
   - Number format

6. **F: Need Permits**
   - Yes/No/Not asked
   - Text format

7. **G: Lead Score**
   - Score from 0-100
   - Number format
   - Conditional formatting:
     - 80-100: Green background
     - 50-79: Yellow background
     - 0-49: Gray background

8. **H: Priority**
   - High/Medium/Low
   - Text format
   - Conditional formatting:
     - High: Red text, bold
     - Medium: Orange text
     - Low: Gray text

9. **I: Assigned To**
   - Agent name
   - Text format

10. **J: Status**
    - New/Contacted/In Progress/Qualified/Booked/Lost
    - Dropdown list

11. **K: Source**
    - voiceflow/website/email/phone
    - Text format

12. **L: Session ID**
    - Unique conversation identifier
    - Text format

13. **M: Response Time**
    - Expected response timeframe
    - Text format (e.g., "1 hour", "24 hours")

14. **N: Special Notes**
    - Honeymoon, Anniversary, VIP, etc.
    - Text format

---

## Conditional Formatting Rules

### For Lead Score Column (G):

1. **High Score (80-100)**:
   - Format cells if: `Custom formula is`
   - Formula: `=AND($G2>=80, $G2<=100)`
   - Background: Light green (#d9ead3)
   - Text: Dark green (#38761d)

2. **Medium Score (50-79)**:
   - Format cells if: `Custom formula is`
   - Formula: `=AND($G2>=50, $G2<80)`
   - Background: Light yellow (#fff2cc)
   - Text: Dark yellow (#bf9000)

3. **Low Score (0-49)**:
   - Format cells if: `Custom formula is`
   - Formula: `=$G2<50`
   - Background: Light gray (#efefef)
   - Text: Dark gray (#666666)

### For Priority Column (H):

1. **High Priority**:
   - Format cells if: `Text contains`
   - Value: `high`
   - Text: Bold, Red (#cc0000)

2. **Medium Priority**:
   - Format cells if: `Text contains`
   - Value: `medium`
   - Text: Bold, Orange (#e69138)

3. **Low Priority**:
   - Format cells if: `Text contains`
   - Value: `low`
   - Text: Gray (#666666)

---

## Sheet 2: Analytics Dashboard

### Create Summary Statistics

**Row 1-2: Title**
```
A1: "Sambora Leads Analytics"
(Merge A1:F1, Center align, Bold, Size 18)
```

**Row 4: Total Leads**
```
A4: "Total Leads"
B4: =COUNTA(Leads!B:B)-1
```

**Row 5: High Priority**
```
A5: "High Priority Leads"
B5: =COUNTIF(Leads!H:H,"high")
C5: =B5/B4
(Format C5 as percentage)
```

**Row 6: Medium Priority**
```
A6: "Medium Priority Leads"
B6: =COUNTIF(Leads!H:H,"medium")
C6: =B6/B4
(Format C6 as percentage)
```

**Row 7: Low Priority**
```
A7: "Low Priority Leads"
B7: =COUNTIF(Leads!H:H,"low")
C7: =B7/B4
(Format C7 as percentage)
```

**Row 9: Average Lead Score**
```
A9: "Average Lead Score"
B9: =AVERAGE(Leads!G:G)
(Format as number, 1 decimal place)
```

**Row 10: Conversion Tracking**
```
A10: "Booked"
B10: =COUNTIF(Leads!J:J,"Booked")
C10: =B10/B4
(Format C10 as percentage)
```

**Row 12: Leads by Source**
```
A12: "Voiceflow"
B12: =COUNTIF(Leads!K:K,"voiceflow")

A13: "Website"
B13: =COUNTIF(Leads!K:K,"website")

A14: "Email"
B14: =COUNTIF(Leads!K:K,"email")
```

**Row 16: This Week's Leads**
```
A16: "Leads This Week"
B16: =COUNTIFS(Leads!A:A,">="&TODAY()-7,Leads!A:A,"<="&TODAY())
```

**Row 17: This Month's Leads**
```
A17: "Leads This Month"
B17: =COUNTIFS(Leads!A:A,">="&DATE(YEAR(TODAY()),MONTH(TODAY()),1))
```

---

## Sheet 3: Agent Performance

### Column Headers:

| A | B | C | D | E |
|---|---|---|---|---|
| Agent Name | Total Assigned | Contacted | Booked | Conversion Rate |

### Formulas (assuming agent names):

**Row 2: Sarah Mitchell**
```
A2: Sarah Mitchell
B2: =COUNTIF(Leads!I:I,"Sarah Mitchell")
C2: =COUNTIFS(Leads!I:I,"Sarah Mitchell",Leads!J:J,"Contacted")+COUNTIFS(Leads!I:I,"Sarah Mitchell",Leads!J:J,"In Progress")+COUNTIFS(Leads!I:I,"Sarah Mitchell",Leads!J:J,"Booked")
D2: =COUNTIFS(Leads!I:I,"Sarah Mitchell",Leads!J:J,"Booked")
E2: =IF(B2>0,D2/B2,0)
(Format E2 as percentage)
```

**Row 3: James Uwimana**
```
A3: James Uwimana
B3: =COUNTIF(Leads!I:I,"James Uwimana")
C3: =COUNTIFS(Leads!I:I,"James Uwimana",Leads!J:J,"Contacted")+COUNTIFS(Leads!I:I,"James Uwimana",Leads!J:J,"In Progress")+COUNTIFS(Leads!I:I,"James Uwimana",Leads!J:J,"Booked")
D3: =COUNTIFS(Leads!I:I,"James Uwimana",Leads!J:J,"Booked")
E3: =IF(B3>0,D3/B3,0)
```

(Repeat for other agents)

---

## Data Validation

### Status Column (J) - Dropdown List

1. Select entire column J (except header)
2. Data → Data validation
3. Criteria: List of items
4. Values (separated by commas):
   ```
   New,Contacted,In Progress,Qualified,Booked,Lost
   ```
5. Check "Reject input" on invalid data
6. Save

---

## Filter Views

### Create Filter: High Priority Only

1. Click any cell in the data range
2. Data → Create a filter
3. Click filter icon on Priority column (H)
4. Uncheck "medium" and "low"
5. Click OK
6. Data → Filter views → Save as "High Priority Only"

### Create Filter: Today's Leads

1. Click filter icon on Timestamp column (A)
2. Filter by condition → Date is → Today
3. Data → Filter views → Save as "Today's Leads"

### Create Filter: Pending Response

1. Click filter icon on Status column (J)
2. Check only "New"
3. Data → Filter views → Save as "Needs Response"

---

## Sharing & Permissions

### For Agents:

1. Click "Share" button (top right)
2. Add agent email addresses
3. Role: **Editor** (can edit and update status)
4. Uncheck "Notify people"
5. Click "Send"

### For Management:

1. Add management emails
2. Role: **Viewer** (read-only)
3. Click "Send"

---

## Mobile Access

Agents can use the Google Sheets mobile app:

1. Download Google Sheets app (iOS/Android)
2. Open the "Sambora Leads" sheet
3. Use filters to view assigned leads
4. Update status on the go

---

## Automation Tips

### Email Notifications for New High-Priority Leads

1. Tools → Script editor
2. Paste this script:

```javascript
function onEdit(e) {
  var sheet = e.source.getActiveSheet();

  // Only run on Leads sheet
  if (sheet.getName() !== "Leads") return;

  var row = e.range.getRow();
  var col = e.range.getColumn();

  // Column H is Priority (column 8)
  if (col === 8) {
    var priority = e.range.getValue();
    var leadName = sheet.getRange(row, 2).getValue();
    var assignedTo = sheet.getRange(row, 9).getValue();

    if (priority === "high") {
      // Send email notification
      MailApp.sendEmail({
        to: getAgentEmail(assignedTo),
        subject: "🔔 High Priority Lead: " + leadName,
        body: "A new high priority lead has been assigned to you. Check the dashboard for details."
      });
    }
  }
}

function getAgentEmail(agentName) {
  var agents = {
    "Sarah Mitchell": "sarah@sambora.com",
    "James Uwimana": "james@sambora.com",
    "Michael Ngabo": "michael@sambora.com"
  };
  return agents[agentName] || "reservations@sambora.com";
}
```

3. Save and authorize the script

---

## Sample Data (for testing)

Once set up, add this sample data to test:

```
Row 2:
2025-01-15 14:23:00 | Emma Johnson | emma.j@example.com | March 15-18, 2025 | 4 | Yes, please | 92 | high | Sarah Mitchell | New | voiceflow | vf_12345 | 1 hour | Honeymoon

Row 3:
2025-01-15 15:10:00 | David Chen | david.c@example.com | June 2025 | 2 | Not sure yet | 68 | medium | Michael Ngabo | New | voiceflow | vf_12346 | 24 hours |

Row 4:
2025-01-15 16:45:00 | Guest_7834 | | Not specified | 0 | Not asked | 25 | low | Nurture Campaign | New | voiceflow | vf_12347 | 48 hours |
```

---

## Dashboard Customization

### Add Chart: Lead Score Distribution

1. Select data range (Column G: Lead Scores)
2. Insert → Chart
3. Chart type: Histogram
4. Customize:
   - Title: "Lead Score Distribution"
   - Bucket size: 10
   - Colors: Green gradient
5. Move chart to Analytics sheet

### Add Chart: Conversion Funnel

1. Create data for funnel:
   ```
   New: =COUNTIF(Leads!J:J,"New")
   Contacted: =COUNTIF(Leads!J:J,"Contacted")
   In Progress: =COUNTIF(Leads!J:J,"In Progress")
   Booked: =COUNTIF(Leads!J:J,"Booked")
   ```
2. Insert → Chart
3. Chart type: Column chart
4. Place on Analytics sheet

---

## Connecting to n8n

Once this sheet is set up:

1. Copy the Sheet URL
2. Extract the Sheet ID from URL:
   ```
   https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit
   ```
3. Paste Sheet ID in n8n Google Sheets node
4. Configure n8n credentials (see SETUP-GUIDE.md)

---

## Best Practices

✅ **Update lead status regularly** - Keep the pipeline accurate
✅ **Add notes in Special Notes column** - Document important details
✅ **Use filters** - Focus on your assigned leads
✅ **Check daily** - Review new leads each morning
✅ **Archive old data** - Move booked/lost leads to archive sheet monthly

---

## Troubleshooting

**Issue**: Formulas not calculating
- **Fix**: File → Spreadsheet settings → Calculation → On change

**Issue**: Can't edit cells
- **Fix**: Check you have Editor permissions

**Issue**: Data not appearing from n8n
- **Fix**:
  1. Check n8n Google Sheets credentials
  2. Verify Sheet ID is correct
  3. Check sheet name is "Leads" (case-sensitive)

---

## Quick Reference: Status Meanings

- **New**: Just received, not contacted yet
- **Contacted**: Initial response sent
- **In Progress**: Actively discussing details
- **Qualified**: Ready to book, awaiting confirmation
- **Booked**: Confirmed booking
- **Lost**: Did not convert

---

**Your Google Sheets dashboard is now ready! 📊**

Next: See SETUP-GUIDE.md to connect Voiceflow → n8n → Google Sheets
