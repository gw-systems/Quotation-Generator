# Email Configuration Guide

## Quick Setup (Gmail)

### Step 1: Create a Gmail App Password

1. Go to your Google Account settings: https://myaccount.google.com/
2. Navigate to **Security** → **2-Step Verification** (enable if not already)
3. Scroll down to **App passwords**
4. Create a new app password for "Mail"
5. Copy the 16-character password

### Step 2: Configure Environment Variables

Edit your `.env` file (create if it doesn't exist):

```env
# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-company-email@gmail.com
EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx
DEFAULT_FROM_EMAIL=your-company-email@gmail.com
```

Replace:
- `your-company-email@gmail.com` with your actual Gmail address
- `xxxx xxxx xxxx xxxx` with the app password you created

### Step 3: Set Admin Email

Run this command to set the admin user's email:

```bash
python manage.py set_user_email admin your-email@gmail.com
```

### Step 4: Test Email Configuration

```bash
python manage.py test_email your-personal-email@gmail.com
```

This will send a test email to verify everything is working.

---

## How It Works

When a user creates a quotation and sends it via email:

1. **FROM:** The email comes from the user who created the quotation
2. **TO:** The client's email address
3. **ATTACHMENTS:** DOCX and/or PDF quotation files
4. **REPLY-TO:** Set to the creator's email

### Example Flow

```
User "admin" (admin@company.com) creates quotation #GW-Q-20260113-0001
User clicks "Send Email"
Email is sent:
  FROM: admin@company.com
  TO: client@example.com  
  SUBJECT: Quotation GW-Q-20260113-0001 from Godamwale
  ATTACHMENTS: quotation.pdf
```

---

## Management Commands

### Set User Email
```bash
python manage.py set_user_email <username> <email>
```

Example:
```bash
python manage.py set_user_email admin admin@godamwale.com
```

### Test Email
```bash
python manage.py test_email <recipient-email>
```

Example:
```bash
python manage.py test_email myemail@gmail.com
```

---

## Troubleshooting

### Common Issues

**1. "SMTPAuthenticationError"**
- Make sure you're using an App Password, not your regular Gmail password
- Verify 2-Step Verification is enabled
- Double-check EMAIL_HOST_USER matches the Gmail account

**2. "SMTPConnectError"**
- Check your firewall allows outgoing connections on port 587
- Verify EMAIL_HOST and EMAIL_PORT are correct

**3. "User has no email address"**
- Set the user's email using: `python manage.py set_user_email <username> <email>`
- Or update in Django admin panel

**4. Email not received**
- Check spam/junk folder
- Verify recipient email address is correct
- Check Gmail's "Sent" folder to confirm it was sent

---

## Gmail Sending Limits

- **Free Gmail:** 500 emails per day
- **Google Workspace:** 2,000 emails per day

For higher volumes, consider:
- SendGrid (100 emails/day free)
- Amazon SES (pay-as-you-go)
- Mailgun (5,000 emails/month free)

---

## Security Best Practices

1. ✅ Never commit `.env` file to git (already in `.gitignore`)
2. ✅ Use App Passwords, not regular passwords
3. ✅ Rotate passwords periodically
4. ✅ Limit who has access to production credentials
5. ✅ Monitor email sending for suspicious activity
