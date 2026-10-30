# Sewa Setu — Old Age Pension Portal

Handover copy. Vendor maintenance contract ended 31/01/2026.

## Running

```
docker compose up --build
```

- Portal: http://localhost:8000
- SMS gateway console (simulated telecom): http://localhost:8000/__gateway/ —
  "sent" OTPs appear here once delivered. The gateway runs on the internal
  network and is served through the portal, so only one port is exposed.
- Database: Postgres, loaded from `seed/seed.sql` on first boot

Production server logs (Jan–Jun 2026) are provided in `logs/`.

Listen to `dc-briefing.mp3` first (the DC's briefing), then read `BRIEF.md`.

# Sewa Setu – Fixed Issues

## 1. Security Issue

**Problem:** The portal had security issues that could put citizens' personal information at risk.

**What I Fixed:** I improved security so that one person cannot view or edit another person's application. I added protection against unauthorized access.

**Why I Fixed It:** I prioritized security first because the portal stores citizens' personal information, and it is really important to protect their information.

**Result:** Now there data are secured from unauthorized access.

## 2. Deemed Approval Issue

**Problem:** The form was not getting approved automatically after 15 days.

**What I Fixed:** According to the data, there were more than 4,870 pending applications. After security, I fixed this issue because long delays can create difficulties for citizens, and we already had so many applications pending.

**Why I Fixed It:** I prioritized this issue after security because long delays can create difficulties for citizens.

**Result:** After fixing this issue, the pending applications got deemed approval.

## 3. Server Slowdown Issue

**Problem:** Two or three days before the disbursement deadline, the server becomes very slow. 

**What I Fixed:** I worked on fixing the server slowdown issue.

**Why I Fixed:** If the server becomes slow, citizens may face delays or may not be able to submit their pension applications on time.

**Result:** After fixing it, the server will work properly, and citizens will not face issues related to a slow server.

## 4. Assamese Name Issue

**Problem:** Assamese names were not showing properly. 

**What I Fixed:** I fixed this issue.

**Why I Fixed:** It's very critical because if a citizen's name is different from the name on their ID proof, their application may get rejected

**Result:** Now, it will show Assamese names properly.

## 5. Application Form Issue

**Problem:** In the application form, the information was unclear, and the form was confusing too.

**What I Fixed:** I improved the information in the form and corrected form-fields. I also added an edit option to the application form so that if citizens make any mistakes while filling out the form, they can edit their information.

**Why I Fixed It:** Citizens should have clear information about the form, whether it is related to eligibility or the file types they need to submit. They should have clear and not confusing form so that they don't get any confusion while filling out the form.

**Result:** After fixing this issue, the form now has clear information and is less confusing.
