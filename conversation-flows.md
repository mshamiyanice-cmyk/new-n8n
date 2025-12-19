# Chatbot Conversation Flows - Sambora Kinigi Demo

## Core User Intents

1. **Gorilla Trekking Information**
2. **Accommodation Inquiries**
3. **Booking & Pricing**
4. **Permit Information**
5. **Activities & Experiences**
6. **Location & Accessibility**
7. **What to Pack / Preparation**
8. **Cancellation & Policies**
9. **General Inquiries**
10. **Ready to Book**

---

## Flow 1: Greeting & Initial Engagement

### Bot Opens
**Bot:** "Welcome to Sambora Kinigi Lodge! 🦍 I'm here to help you plan your unforgettable gorilla trekking adventure in Rwanda. Are you interested in learning about gorilla trekking, our luxury accommodations, or would you like to make a booking?"

### User Responses Path A: Gorilla Trekking
**User:** "Tell me about gorilla trekking"

**Bot:** "Gorilla trekking in Rwanda's Volcanoes National Park is truly a once-in-a-lifetime experience! You'll spend up to an hour with endangered mountain gorillas in their natural habitat.

Here's what you should know:
- Permits cost $1,500 per person
- Minimum age is 15 years
- We recommend booking 6 months in advance
- Sambora Kinigi is perfectly located near the park entrance

Would you like to know more about:
1. Permit booking process
2. What to expect on a trek
3. Best time to visit
4. What to pack"

### User Responses Path B: Accommodation
**User:** "Tell me about your accommodations"

**Bot:** "We offer luxury boutique accommodations designed for your ultimate comfort after an exhilarating day of trekking!

✨ Our all-inclusive rooms include:
- Private balconies with stunning garden views
- Complimentary 45-minute massage
- All meals featuring fresh, local cuisine
- House wines and stocked minibar
- Evening fires and warm bottles for your bed
- Professional boot cleaning after muddy treks

The rate is approximately $700 per person per night, covering everything you need for a worry-free stay.

Would you like to:
1. See room photos
2. Check availability
3. Learn about our dining
4. Ask about special services"

### User Responses Path C: Ready to Book
**User:** "I want to make a booking"

**Bot:** "Wonderful! I'd love to help you secure your gorilla trekking adventure. Let me gather a few details:

1. When are you planning to visit? (Specific dates or month)
2. How many guests will be traveling?
3. Do you need gorilla permits? (Remember to book 6 months ahead!)

Our reservations specialist can then provide availability and finalize your booking."

**[TRIGGER: High-Quality Lead Qualification]**

---

## Flow 2: Permit Information Deep Dive

### User Asks About Permits
**User:** "How do I get gorilla permits?"

**Bot:** "Great question! Gorilla permits are essential for your trek. Here's everything you need to know:

**Pricing:**
- $1,500 for international visitors
- $500 for foreign residents of Rwanda
- 💡 Special discount: 30% off if visiting Nov-May AND staying 2+ nights at other Rwanda parks

**Booking:**
- Book at least 6 months in advance
- Only 96 permits available per day
- We can help arrange permits for you

**What's Included:**
- Park entrance
- Guided trek
- 1 hour with gorillas

**Not Included:**
- Porter fees (recommended - they carry your daypack)
- Guide tips
- Accommodation (covered in our all-inclusive rate!)

Would you like me to connect you with our team to secure permits for your dates?"

**[IF YES → TRIGGER: Lead Capture & Routing to Booking Agent]**

---

## Flow 3: What to Pack / Preparation

### User Asks About Packing
**User:** "What should I pack for gorilla trekking?"

**Bot:** "Excellent question! Proper preparation ensures a comfortable and memorable trek. Here's your essential packing list:

**Clothing:**
- ✅ Hiking boots (we'll clean them after your trek!)
- ✅ Layered, moisture-wicking clothes
- ✅ Rain jacket (weather can change quickly)
- ✅ Hand gloves
- ✅ Long pants and long sleeves

**Equipment:**
- ✅ Good camera (no flash allowed)
- ✅ Binoculars
- ✅ Insect repellent
- ✅ Sunscreen

**Important Notes:**
- Mornings are cool, hiking can be hot
- Expect mist and rain
- We provide porter services to carry your daypack

**Trek Day Timeline:**
- 7:00 AM: Arrive at RDB offices in Kinigi for briefing
- We'll arrange early breakfast and transportation

Do you need help with:
1. Best camera recommendations
2. Local shopping for forgotten items
3. Porter booking
4. Transportation arrangements"

---

## Flow 4: Pricing & Value Proposition

### User Asks About Costs
**User:** "How much does everything cost?"

**Bot:** "I'm happy to break down the costs for you:

**Sambora Kinigi All-Inclusive Stay:**
- $700 per person/night
- Includes: all meals, drinks, wines, minibar, 45-min massage, WiFi, cultural performances

**Gorilla Permit:**
- $1,500 per person (book separately, 6 months ahead)
- 30% discount Nov-May with 2+ nights at other parks

**Additional Costs:**
- Porter: ~$15 (highly recommended)
- Guide tips: discretionary
- Transportation: varies

**Example 3-Day Package:**
- 2 nights accommodation: $1,400/person
- 1 gorilla trek permit: $1,500/person
- Total: ~$2,900/person (all-inclusive luxury!)

Many guests say this once-in-a-lifetime experience is priceless. The personalized service, gourmet meals, and unforgettable gorilla encounter make it worth every penny.

Would you like to:
1. Get a custom quote for your dates
2. Learn about our special services
3. See what previous guests say
4. Speak with our reservations team"

**[OPTIONS 3,4 → TRIGGER: Lead Qualification]**

---

## Flow 5: Best Time to Visit

### User Asks About Timing
**User:** "When is the best time to visit?"

**Bot:** "Rwanda is a year-round gorilla trekking destination, but there are some considerations:

**Dry Seasons (Peak Season):**
- June to September
- December to February
- Pros: Easier hiking conditions, less mud
- Cons: Higher demand for permits

**Wet Seasons (Green Season):**
- March to May
- October to November
- Pros: 30% permit discount available, lush scenery, fewer tourists
- Cons: Muddy trails (but we clean your boots!), occasional rain

**Pro Tip:** We recommend November-May for the discount AND beautiful landscapes. Our all-inclusive package means you'll be comfortable regardless of weather!

**Booking Timeline:**
Regardless of when you visit, book permits 6 months ahead.

Do you have specific dates in mind? I can check availability and help with permit coordination."

**[IF YES → TRIGGER: Lead Capture]**

---

## Flow 6: Activities Beyond Gorilla Trekking

### User Asks About Other Activities
**User:** "What else can we do besides gorilla trekking?"

**Bot:** "Sambora Kinigi and the surrounding area offer incredible experiences:

**Wildlife & Nature:**
- 🐒 Golden Monkey Tracking
- 🌋 Volcano Hikes (stunning views!)
- 🌿 Guided walks to Ellen DeGeneres - Dian Fossey Gorilla Center
- 🦅 Bird watching in wetlands

**At the Lodge:**
- 💆 Spa & wellness treatments (45-min massage included!)
- 🎭 Cultural performances
- 🚴 Cycling tours
- 🚶 Walking tours

**Historical:**
- Visit to Dian Fossey's tomb
- Learn about gorilla conservation efforts

Most guests do 1-2 treks and combine them with other activities for a 3-4 day itinerary.

Would you like help planning a multi-day itinerary?"

**[IF YES → TRIGGER: Transfer to Travel Planning Specialist]**

---

## Flow 7: Health & Safety Requirements

### User Asks About Requirements
**User:** "Are there any health requirements?"

**Bot:** "Yes, important health and safety guidelines to protect both you and the gorillas:

**Age Requirement:**
- Minimum 15 years old (strictly enforced)

**Health Rules:**
- ❌ Cannot trek if you have cold, flu, or contagious illness
- Must maintain 7-meter distance from gorillas
- This protects the gorillas who are susceptible to human diseases

**Physical Fitness:**
- Moderate fitness required
- Treks can be 2-6 hours depending on gorilla location
- Varying terrain and altitude
- Porters available to help carry your belongings

**Required Documents:**
- Valid passport
- Gorilla permit
- Show both at 7 AM briefing

**Good to Know:**
After your trek, enjoy our complimentary 45-minute massage to recover! Many guests say it's the perfect way to relax those hiking muscles.

Do you have specific health concerns or questions about trek difficulty?"

---

## Flow 8: Location & Getting There

### User Asks About Location
**User:** "Where are you located? How do we get there?"

**Bot:** "We're strategically located for your gorilla trekking adventure!

**Address:**
Sambora Kinigi Lodge
RN 18, Kinigi, Musanze, Rwanda

**Location Benefits:**
- ⭐ Near the entrance to Volcanoes National Park
- Just minutes from the gorilla trekking starting point
- Easy access to RDB briefing center (7 AM meeting point)

**Getting Here:**
- ~2.5 hours from Kigali (Rwanda's capital)
- ~15 minutes from Musanze town
- We can arrange transportation from Kigali airport

**What to Know:**
- Early morning treks mean you'll appreciate being so close!
- Our convenient location means more rest time, less travel

Would you like us to arrange:
1. Airport pickup
2. Transportation from Kigali
3. Directions if self-driving
4. Local area guidance"

**[OPTIONS 1,2 → TRIGGER: Lead Qualification]**

---

## Flow 9: Cancellation & Refund Policies

### User Asks About Cancellations
**User:** "What's your cancellation policy?"

**Bot:** "I want to be transparent about our policies:

**Gorilla Permit Cancellations:**
- ⚠️ No refunds for late arrivals, flight delays, or personal cancellations
- ✅ Exception: If trek fails due to gorilla group movement, you get another chance OR full refund

**Accommodation Cancellations:**
- [Policy would be inserted here based on actual Sambora policy]
- We recommend travel insurance for added protection

**Why the Strict Permit Policy:**
- Permits are limited (96/day for all of Rwanda)
- High demand means permits sell out months ahead
- Your unused permit could have gone to another traveler

**Our Recommendation:**
- Book when you're certain of dates
- Purchase comprehensive travel insurance
- Plan backup dates if possible
- Book 6+ months ahead for flexibility

Given these policies, do you have confirmed travel dates you'd like to book?"

---

## Flow 10: Social Proof & Testimonials

### User Asks About Reviews/Experiences
**User:** "What do other guests say?" / "Do you have reviews?"

**Bot:** "Our guests consistently rave about their experiences! Here are some highlights:

⭐⭐⭐⭐⭐ **Service Excellence:**
_"Top shelf staff - attentive and laser-focused on customer service. They worked hard to never say no!"_

⭐⭐⭐⭐⭐ **Accommodations:**
_"Stunning rooms full of character with a warm African touch. Super comfortable and thoughtfully designed."_

⭐⭐⭐⭐⭐ **Food & Dining:**
_"Amazing, healthy & fresh food prepared by a talented chef using local ingredients."_

⭐⭐⭐⭐⭐ **Special Touches:**
_"Every evening a fire was lit in our room. They even cleaned our boots after muddy treks - they looked brand new!"_

⭐⭐⭐⭐⭐ **Overall Experience:**
_"Nothing short of phenomenal - a 5-star experience in a boutique hotel. The perfect place to launch gorilla treks!"_

**Where to Read More:**
- TripAdvisor: Excellent ratings
- Booking.com: 44+ verified reviews
- Google Reviews: Highly rated

Would you like to experience this level of service yourself? I can connect you with our team to plan your stay!"

**[IF YES → TRIGGER: High-Quality Lead Routing]**

---

## Flow 11: Lead Qualification & Capture

### When User Shows Booking Intent
**Bot:** "Wonderful! Let me gather some information to provide you with the best assistance:

**Quick Questions:**
1. **Travel Dates:** When are you planning to visit? (Specific dates or approximate month/season)

2. **Group Size:** How many people will be traveling?

3. **Gorilla Trek Interest:** How many gorilla treks would you like to do? (Most guests do 1-2)

4. **Accommodation:** How many nights will you stay with us?

5. **Contact Information:**
   - Name:
   - Email:
   - Phone (optional):
   - Country:

6. **Special Requests:** Any dietary restrictions, accessibility needs, or special occasions (honeymoon, anniversary)?

**What Happens Next:**
Our reservations specialist will contact you within 24 hours to:
- Confirm availability
- Assist with gorilla permit booking
- Provide a detailed quote
- Answer any additional questions
- Finalize your booking

Is there anything else you'd like to know while I have your details?"

**[TRIGGER: Lead Scoring & Routing]**

---

## Flow 12: Objection Handling - Price

### User Says It's Too Expensive
**User:** "That seems expensive" / "Is there anything cheaper?"

**Bot:** "I completely understand - this is a significant investment. Let me share why our guests feel it's worth every penny:

**What You're Really Getting:**
1. **Once-in-a-Lifetime Experience:** Mountain gorillas exist in only 3 countries. There are fewer than 1,000 in the wild.

2. **All-Inclusive Luxury:** Unlike other lodges:
   - ✅ All meals & drinks included
   - ✅ 45-minute massage included
   - ✅ Cultural performances included
   - ✅ No hidden fees or surprise costs

3. **Unmatched Service:**
   - Boot cleaning, laundry, personalized attention
   - Small boutique lodge = individual care
   - Staff goes above and beyond

4. **Conservation Impact:**
   - Your permit fees directly fund gorilla conservation
   - Support local communities
   - Protect endangered species

**Ways to Save:**
- 💰 Visit Nov-May for 30% permit discount (saves $450!)
- 💰 Book direct for best rates
- 💰 Combine with other Rwanda parks for discount

**Cost Breakdown:**
For $2,900/person (3 days):
- 2 nights luxury all-inclusive: $1,400
- 1 gorilla permit: $1,500
- Unlimited memories: Priceless!

Many guests tell us months later it was the best money they ever spent. Would you like to explore dates during discount season to save on permits?"

**[CONTINUE ENGAGEMENT]**

---

## Flow 13: Objection Handling - Timing/Not Ready

### User Says "Not Ready to Book"
**User:** "I'm just looking" / "Not ready yet" / "Still researching"

**Bot:** "That's perfectly fine! Planning a trip like this should be thoughtful and well-researched.

**Here's how I can help today:**

1. **Send Information Package:** I can email you detailed info about:
   - Room photos and descriptions
   - Sample itineraries
   - Packing lists
   - Permit booking timeline
   - Guest testimonials

2. **Stay in Touch:** Join our newsletter for:
   - Special offers
   - Best time to book alerts
   - Gorilla trekking tips
   - Rwanda travel insights

3. **Permit Timeline Reminder:** Since permits must be booked 6 months ahead, knowing your rough timeline helps:
   - Traveling in next 6 months? → Permits may be limited
   - Traveling in 6-12 months? → Perfect planning window
   - Traveling beyond 12 months? → Plenty of time to research

**May I ask:**
- What's your approximate timeframe for this trip?
- What information would be most helpful right now?
- Would you like me to send you our information package?

**[COLLECT EMAIL → TRIGGER: Nurture Campaign Lead]**

---

## Lead Scoring Logic

### High-Priority Lead (Score: 80-100) → Route to Senior Booking Agent
- Has specific dates (within 6 months)
- Group size 2-8 people
- Expressed price acceptance
- Needs gorilla permits
- International traveler
- Asked about availability
- Mentioned special occasion

### Medium-Priority Lead (Score: 50-79) → Route to Travel Planning Specialist
- Flexible dates (6-12 months out)
- Solo traveler or couple
- Researching options
- Asking detailed questions
- Interested in multi-day itinerary
- Budget-conscious but interested

### Low-Priority Lead (Score: 0-49) → Add to Nurture Email Campaign
- No specific dates
- Just browsing
- Price shopping only
- Very distant travel dates (12+ months)
- General questions only
- Not responsive to qualification questions

### Immediate Response Needed → Route to Available Agent
- Existing booking modification
- Urgent question
- Complaint or issue
- VIP/returning guest

---

## Chatbot Personality & Voice

### Tone Guidelines
- **Warm & Welcoming:** Make users feel valued immediately
- **Enthusiastic but Professional:** Show genuine excitement about gorilla trekking without being pushy
- **Knowledgeable:** Demonstrate expertise in gorilla trekking and luxury travel
- **Helpful:** Anticipate needs and offer solutions
- **Authentic:** Reflect true Rwandan hospitality
- **Luxury-Appropriate:** Sophisticated but not pretentious

### Language Patterns
- Use "we" and "you" for connection
- Paint vivid pictures of experiences
- Use emojis sparingly (🦍 🌋 ⭐ ✨) for visual interest
- Ask open-ended questions to engage
- Acknowledge concerns empathetically
- Provide specific, concrete information

### Avoid
- Pressure tactics or urgency manipulation
- Over-promising
- Generic responses
- Ignoring questions
- Being overly technical
- Dismissing budget concerns

---

## Error Handling & Fallbacks

### When Bot Doesn't Understand
**Bot:** "I want to make sure I give you the right information. Could you rephrase your question?

Or, I can help with:
- Gorilla trekking information
- Accommodation details
- Booking and availability
- Permits and pricing
- Activities and experiences
- Preparation and packing

You can also reach our team directly:
📞 +250 794 416 409
📧 stay@samborakinigi.com"

### When Outside Business Hours
**Bot:** "Thanks for reaching out! Our team is currently offline (East Africa Time: [TIME]).

**Operating Hours:**
- Monday-Sunday: 7 AM - 9 PM EAT

**In the meantime:**
- I can answer questions about gorilla trekking, accommodations, and pricing
- You can email us: stay@samborakinigi.com
- WhatsApp: +44 7960 040 859

**Would you like to:**
1. Continue chatting with me
2. Leave a message for our team
3. Schedule a call back

Your message is important - we'll respond within 24 hours!"

### Complex Questions Beyond Bot Capability
**Bot:** "That's a great question that deserves a detailed answer from our expert team.

I'd like to connect you with [Specialist Name/Type] who can give you comprehensive information about [topic].

**May I have:**
- Your name:
- Email:
- Best time to reach you:

They'll contact you within 24 hours to discuss [specific topic] in detail.

**Or, if you prefer:**
- Call us now: +250 794 416 409
- WhatsApp: +44 7960 040 859
- Email: stay@samborakinigi.com"

**[TRIGGER: Specialist Routing]**

---

## Integration Points for n8n Workflow

### 1. **Lead Capture Trigger**
- Fires when user provides contact information
- Stores in CRM/database
- Triggers lead scoring

### 2. **Lead Scoring Calculation**
- Calculates score based on conversation data
- Assigns priority level
- Determines routing destination

### 3. **Agent Routing**
- Routes to appropriate agent based on:
  - Lead score
  - Inquiry type
  - Agent availability
  - Agent expertise
  - Time of day

### 4. **Email Notifications**
- Notifies agent of new qualified lead
- Sends confirmation to user
- Triggers follow-up sequence

### 5. **CRM Update**
- Logs conversation transcript
- Updates lead status
- Records qualification data
- Tracks conversion metrics

### 6. **Analytics Tracking**
- Conversation completion rate
- Lead qualification rate
- Intent distribution
- Common questions/topics
- Conversion funnel metrics
