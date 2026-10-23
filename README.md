# Seva Setu — Old Age Pension Portal

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

# Seva Setu – Fixes and Decisions

## First Fix: Clear Information on the Welcome Page and About the Scheme Page

**Problem:** The instructions on the Welcome Page and the About the Scheme page were unclear.

**What I Fixed:** On the Welcome Page, I clarified that people aged 60 years or older are eligible. On the About the Scheme page, I clarified the rules and age eligibility information and arranged the information in a proper order.

**Why I Fixed It:** I chose this issue as my first priority because users need to understand the purpose of the portal, its eligibility criteria, and its rules before proceeding. The portal must clearly explain who it is for and what citizens need to do.

**Result:** The portal now provides clearer information and better-organized rules for citizens.

## Second Fix: Weak Security Before OTP Verification

**Problem:** The security check before OTP verification was very weak.

**What I Fixed:** I replaced the simple calculation-based check with CAPTCHA.

**Why I Fixed It:** Initially, the security check involved easy calculations, such as 3 + 5. I considered making the calculations more difficult, but bots can also solve complex calculations easily. CAPTCHA can help distinguish real human users from automated bots.

**Result:** The portal now has a stronger security check than the basic calculation-based method.

## Third Fix: Inclusive Personal Details Form

**Problem:** The Personal Details form had fields for “Husband’s Name” and “Husband’s Employer.”

**What I Fixed:** I replaced “Husband’s Name” with “Spouse’s Name” and “Husband’s Employer” with “Spouse’s Employer.”

**Why I Fixed It:** Although this is an old-age pension form, it is not intended only for women. The previous labels could confuse male citizens filling out the form. Using “Spouse” makes the fields suitable for both men and women.

**Result:** The Personal Details form is clearer and more inclusive.

## Fourth Fix: Improved Address Details Form

**Problem:** The Address Details form had only two fields: Village and Block. The Block field also had a dropdown with limited options.

**What I Fixed:** I added and arranged the address fields in the following order:

House → Village → Post Office → Block → District → State → PIN Code

**Why I Fixed It:** The previous form did not collect enough information to provide a complete address. Since the form is intended for people from Purvanchal, Uttar Pradesh, I researched the region and found that Uttar Pradesh has more than 70 districts and over 800 blocks. Therefore, the address form needed more complete details rather than limited options.

**Result:** The form now collects more complete address information and presents the fields in a clear order, reducing confusion for citizens.

## Fifth Fix: Document Verification Error and Application Editing

**Problem:** During document verification, the portal displayed the `ERR_VAL_47` error. Additionally, citizens could not edit their applications after submitting them.

**What I Fixed:** I modified the document upload function in `app.py` to address the `ERR_VAL_47` error. I also added a new route in `app.py` and created a new template named `edit_application.html` to allow citizens to edit their submitted applications.

**Why I Fixed It:**

**For the `ERR_VAL_47` error:** This error prevented citizens from submitting their documents and proceeding to the next stage. Since the application process has six stages, successful document submission is necessary to continue. I wanted to improve the process further by checking whether the submitted identity proof was valid, but I could not implement that functionality.

**For application editing:** This was a serious issue because, as I learned from the audio briefing, citizens sometimes submitted applications with mistakes and then had to visit a help desk to request deletion of their applications so they could correct them. In some cases, names appeared incorrectly even when citizens had entered them correctly. The editing option allows citizens to correct mistakes, including errors in their names.

**Result:** Citizens can upload their documents without encountering the identified error and proceed to the declaration stage. They can also edit their applications to correct mistakes.
