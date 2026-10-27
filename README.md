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

## Sewa Setu – Fixes and Decisions

### 1. Security Improvements

**Problem:** The portal had security problems that could put citizens' personal information at risk.

**What I Fixed:** I improved security so that one person cannot view or edit another person's application. I improved password security, added OTP verification for password resets, checked that only admins can approve or reject applications, added protection against unsafe inputs, and kept secret information out of the code.

**Why I Fixed It:** I prioritized security because the portal stores citizens' personal information. It is important to protect this information from unauthorized access.

**Result:** The portal has improved security, and all my security tests are passing.

### 2. Clear Information and Application Form

**Problem:** The information on the Welcome Page and About the Scheme page was unclear, and some form fields were confusing.

**What I Fixed:** I clarified the age eligibility on the Welcome Page and organized the scheme rules on the About the Scheme page. I also improved the order of form fields and corrected confusing options.

**Why I Fixed It:** Citizens need to understand the scheme, its rules, and its eligibility requirements before applying. The form should also be easy to understand and fill out.

**Result:** Citizens can understand the scheme more easily, and the application form is clearer and better organized.

### 3. Edit Application

**Problem:** Citizens could not edit their applications after submitting them.

**What I Fixed:** I added a new route in `app.py` and created a new template called `edit_application.html` to allow citizens to edit their submitted applications.

**Why I Fixed It:** As per the information provided in the audio briefing, citizens sometimes made mistakes while filling out their applications. They then had to visit a help desk and request the deletion of their applications to correct those mistakes. The editing option helps them correct mistakes without requesting deletion.

**Result:** Citizens can edit their submitted applications and correct incorrect information.

### 4. Assamese Name Issue

**Problem:** Some Assamese characters were displayed as question marks (`????`) in the application form.

**What I Fixed:** I fixed the issue that caused Assamese characters to display incorrectly.

**Why I Fixed It:** Citizens should be able to enter and display their names correctly. Incorrect characters can cause problems with their personal information.

**Result:** The fix helps citizens display their names correctly, including names containing Assamese characters.

### 5. Deemed Approval System

**Problem:** The automatic approval script was looking for the wrong configuration file and could not read the approval settings.

**What I Fixed:** I corrected the configuration file path and added a test to check the issue. The system is designed to automatically approve eligible applications that remain pending for more than 15 days.

**Why I Fixed It:** I worked on this issue because long delays can create difficulties for citizens. The automatic approval system is intended to reduce unnecessary delays for eligible applicants.

**Result:** The script now looks for the correct configuration file, and a test has been added to check the issue.