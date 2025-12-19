# Testing Guide: Voiceflow + n8n System
## Sambora Kinigi Inquiry Management

Use this guide to test your complete system after setup.

---

## 🎯 Test Scenarios

### Scenario 1: High-Intent Lead (Should Score 80+)

**Test this conversation in Voiceflow:**

```
You: Hi, I want to book a gorilla trekking trip

Bot: [Welcome and asks questions]

You: We want to visit March 15-18, 2025

You: There will be 4 of us

You: Yes, we need help with gorilla permits

You: My email is test@example.com

You: My name is Test User
```

**Expected Results:**
- ✅ Lead appears in Google Sheets within 30 seconds
- ✅ Lead Score: 80-95
- ✅ Priority: HIGH
- ✅ Assigned to: Senior Booking Agent
- ✅ Email sent to agent
- ✅ Slack notification (if configured)

**Check Google Sheets:**
- Row added with all data
- Travel Dates: "March 15-18, 2025"
- Group Size: 4
- Email: test@example.com
- Status: "New"

---

### Scenario 2: Research-Phase Lead (Should Score 50-70)

**Test this conversation:**

```
You: How much does gorilla trekking cost?

Bot: [Provides pricing info]

You: What's included in the accommodation?

Bot: [Explains amenities]

You: What should I pack?

Bot: [Packing list]

You: Thanks, I'll think about it
```

**Expected Results:**
- ✅ Lead captured if email provided
- ✅ Lead Score: 40-60
- ✅ Priority: MEDIUM
- ✅ Assigned to: Travel Planning Specialist
- ⚠️ No immediate Slack alert (only high priority)

---

### Scenario 3: Low-Intent Lead (Should Score < 50)

**Test this conversation:**

```
You: Where are you located?

Bot: [Location info]

You: What activities do you offer?

Bot: [Lists activities]

You: OK thanks
```

**Expected Results:**
- ✅ Captured only if email provided
- ✅ Lead Score: 15-40
- ✅ Priority: LOW
- ✅ Assigned to: Nurture Campaign
- ❌ No email alert
- ❌ No Slack alert

---

## ✅ System Health Checks

### Daily Checks (First 2 Weeks)

**Every Morning:**
1. [ ] Open Google Sheets - check for new leads
2. [ ] Check n8n Executions - all green?
3. [ ] Test chatbot on website - still working?
4. [ ] Agent inbox - notifications arriving?

**Weekly:**
1. [ ] Review lead quality in Google Sheets
2. [ ] Check average lead score (target: 60+)
3. [ ] Verify conversion tracking
4. [ ] Agent feedback session

---

## 🐛 Common Issues & Fixes

### Issue: No Data in Google Sheets

**Diagnostic Steps:**
```
1. Go to n8n → Workflows → Voiceflow Integration
2. Check if workflow is Active (toggle should be ON)
3. Click "Executions" tab
4. Do you see any executions?
```

**If NO executions:**
- Voiceflow isn't sending data
- Check Voiceflow API block configuration
- Verify webhook URL is correct

**If YES but FAILED executions:**
- Click the failed execution
- Look for red nodes
- Common errors:
  - Google Sheets: Wrong Sheet ID or credentials
  - Email: Invalid credentials
  - Slack: Wrong webhook URL

---

### Issue: Wrong Lead Scores

**Example**: Obvious high-intent lead scores only 30

**Fix**:
1. Open n8n workflow
2. Find "Process Voiceflow Data" node
3. Check if Voiceflow is sending `lead_score` correctly
4. Adjust scoring logic if needed:
   ```javascript
   // Find these lines and adjust values:
   if (extractedData.hasEmail) finalScore += 25;
   if (extractedData.hasSpecificDates) finalScore += 20;
   ```

---

### Issue: Agents Not Getting Emails

**Check:**
1. n8n → Credentials → Email credentials valid?
2. Agent emails correct in workflow?
3. Gmail blocking? (check spam, enable app passwords)

**Test Manually:**
1. In n8n workflow, click "Email Agent" node
2. Click "Execute Node" button
3. Check for errors

---

### Issue: Voiceflow API Call Failing

**Symptoms**:
- Conversation completes but no lead in Google Sheets
- Voiceflow shows error after collecting email

**Check:**
1. Voiceflow logs (in project settings)
2. Look for API call errors
3. Common issues:
   - Wrong webhook URL
   - n8n workflow not active
   - Variables not mapped correctly

**Fix:**
1. Copy webhook URL from n8n again
2. Paste into Voiceflow API block
3. Ensure variables match: `{user_email}` not `{email}`

---

## 📊 Performance Benchmarks

### Week 1 Targets:

| Metric | Target | Actual |
|--------|--------|--------|
| Total Conversations | 20+ | ___ |
| Leads Captured | 10+ | ___ |
| High Priority | 20% | ___% |
| Medium Priority | 50% | ___% |
| Low Priority | 30% | ___% |
| Avg Lead Score | 50+ | ___ |
| System Uptime | 99%+ | ___% |
| Agent Response Time (High) | < 2hr | ___ |

---

## 🧪 Test Data Generator

Use these test profiles:

**Test Lead 1: Honeymoon Couple (High Intent)**
```
Name: Emily & James Williams
Email: test1@example.com
Dates: June 10-14, 2025
Group: 2
Permits: Yes
Special: Honeymoon
Expected Score: 90+
```

**Test Lead 2: Family Trip (Medium Intent)**
```
Name: The Johnsons
Email: test2@example.com
Dates: August 2025 (flexible)
Group: 5
Permits: Not sure
Expected Score: 65
```

**Test Lead 3: Solo Research (Low Intent)**
```
Name: Alex Chen
Email: (not provided)
Dates: (not provided)
Group: 1
Just browsing
Expected Score: 25
```

---

## 🎭 Role-Play Testing Script

**Tester 1 (Customer)**: Go through booking flow
**Tester 2 (Agent)**: Monitor dashboard and respond

### Test 1: Perfect Flow
1. Customer starts chat
2. Expresses booking interest
3. Provides all details
4. Agent sees lead in dashboard
5. Agent updates status to "Contacted"
6. Agent sends follow-up email

**Pass if**: Lead captured, scored correctly, agent can update status

### Test 2: Interrupted Flow
1. Customer starts chat
2. Asks questions
3. Closes chat mid-conversation
4. Returns later (new session)
5. Continues and completes booking

**Pass if**: Both sessions tracked, final data captured

### Test 3: Difficult Customer
1. Customer asks complex questions
2. Bot doesn't know answer
3. Customer requests human agent
4. Lead captured even without full details

**Pass if**: Lead created with partial data, flagged for follow-up

---

## 📱 Mobile Testing

Test on different devices:

- [ ] iPhone Safari
- [ ] Android Chrome
- [ ] iPad
- [ ] Desktop Chrome
- [ ] Desktop Firefox
- [ ] Desktop Safari

**Check**:
- Chat widget visible and clickable?
- Conversation scrolls properly?
- Email input works?
- Submit successful?

---

## 🔐 Security Testing

### Test 1: Data Privacy
1. Complete conversation with fake email
2. Check Google Sheet - data appears
3. Ask to delete data (GDPR test)
4. Verify you can delete the row

**Pass if**: Data can be deleted on request

### Test 2: Invalid Input
Try to break the system:
```
- Enter "asdf" as email → Should reject
- Enter negative group size → Should reject
- Enter code in name field → Should sanitize
- Send very long messages → Should handle
```

**Pass if**: All handled gracefully without crashes

### Test 3: Rate Limiting
1. Send 50 messages rapidly
2. System should still respond
3. No crashes or data loss

**Pass if**: System stable under load

---

## 📈 Analytics Review

**After 1 Week, Review:**

### In Google Sheets:
1. Open "Analytics" sheet
2. Check:
   - Total leads
   - Priority distribution
   - Average lead score
   - Conversion rate
   - Leads by source

### In n8n:
1. Workflows → Executions
2. Sort by date
3. Check success rate
4. Any patterns in failures?

### In Voiceflow:
1. Project → Analytics
2. Check:
   - Total conversations
   - Completion rate
   - Drop-off points
   - Common questions

**Action Items**:
- Low completion rate? → Simplify flow
- Common questions unanswered? → Update knowledge base
- Low lead scores? → Adjust scoring logic
- High drop-off at email capture? → Rephrase request

---

## 🔄 Optimization Cycle

**Every 2 Weeks:**

1. **Gather Data**:
   - Export Google Sheets data
   - Review conversion rates
   - Agent feedback

2. **Identify Issues**:
   - Where do users drop off?
   - What questions confuse the bot?
   - Which leads convert best?

3. **Implement Changes**:
   - Update Voiceflow responses
   - Adjust lead scoring
   - Refine email templates

4. **Test Changes**:
   - Run test scenarios
   - Monitor for 3 days
   - Compare metrics

5. **Repeat**

---

## 🎯 Success Criteria

### System is "Production Ready" when:

- ✅ 95%+ of test leads appear in Google Sheets
- ✅ 100% of high-priority leads trigger notifications
- ✅ Lead scores match intent (test vs actual)
- ✅ Agents can access dashboard on mobile
- ✅ Average response time < 2 hours for high priority
- ✅ No critical errors in n8n executions
- ✅ Chatbot widget loads < 2 seconds
- ✅ 90%+ customer completion rate on booking flow

---

## 🚨 Emergency Procedures

### If System Goes Down:

**Immediate**:
1. Post notice on website: "Chat temporarily unavailable - please email stay@samborakinigi.com"
2. Check n8n status
3. Check Voiceflow status

**Diagnose**:
1. n8n → Executions → Look for errors
2. Voiceflow → Logs → Check API calls
3. Google Sheets → Can you access it?

**Escalate**:
- n8n Cloud down? → Check status.n8n.io
- Voiceflow down? → Check status.voiceflow.com
- Everything working but no data? → Check webhook connectivity

**Temporary Workaround**:
- Set up simple contact form
- Route to email
- Manual entry to Google Sheets
- Resume automated system when fixed

---

## 📞 Support Contacts

**n8n Issues**:
- Community: https://community.n8n.io
- Docs: https://docs.n8n.io
- Status: https://status.n8n.io

**Voiceflow Issues**:
- Discord: https://discord.gg/voiceflow
- Docs: https://www.voiceflow.com/docs
- Support: support@voiceflow.com

**Google Sheets Issues**:
- Help Center: https://support.google.com/sheets
- API Status: https://www.google.com/appsstatus

---

## ✅ Final Test Checklist

Before going live to customers:

**Voiceflow**:
- [ ] All conversation flows tested
- [ ] Knowledge base accurate
- [ ] No broken paths
- [ ] Error handling works
- [ ] Handoff to human works

**n8n**:
- [ ] Workflow active
- [ ] Test execution successful
- [ ] All credentials valid
- [ ] Email notifications sending
- [ ] Google Sheets writing correctly

**Google Sheets**:
- [ ] Formatting applied
- [ ] Formulas working
- [ ] Agents have access
- [ ] Can update statuses
- [ ] Mobile access works

**Integration**:
- [ ] End-to-end test passes
- [ ] High-intent lead → Agent email < 5 min
- [ ] Data accuracy 100%
- [ ] No data loss
- [ ] System handles 10 concurrent users

**Website**:
- [ ] Chatbot visible
- [ ] Loads quickly
- [ ] Works on mobile
- [ ] Matches brand
- [ ] Privacy policy updated

---

**🎉 System is tested and ready for launch!**

**Next**: Monitor closely for first 48 hours, then weekly reviews.

---

**Remember**: Perfect is the enemy of good. Launch with 90% confidence, then iterate based on real user feedback!

Good luck! 🚀🦍
