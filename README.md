# BBMP Smart Light Ticket Tracker & Automated Analytics Reporter

An automated solution for fetching BBMP (Bruhat Bengaluru Mahanagara Palike) Smart Light ticket data from Firestore, generating executive analytics digests with responsive HTML email templates, and auto-dispatching daily reports to designated officials.

---

## Features

- **Firestore & ThingsBoard Integration**: Fetches ticket documents from Firebase Firestore and ThingsBoard APIs.
- **Analytics Digest**: Calculates total tickets, resolution rate, zone-wise breakdown, aging analysis (> 7 days & > 30 days), and equipment metrics (SLC Panels vs. Lamps).
- **Executive HTML Email Report**: Clean, responsive email template formatted for all major email clients.
- **Automated Excel & CSV Attachments**: Automatically generates multi-tab Excel workbooks containing itemized ticket breakdowns.
- **Email Threading Support**: Maintains RFC 2822 email headers (`In-Reply-To`, `References`) so daily emails group neatly into a single thread.
- **GitHub Actions Automation**: Daily scheduled execution via GitHub Actions cron job.

---

## GitHub Actions Setup & Secrets

The repository includes a GitHub Actions workflow defined at [`.github/workflows/daily_report.yml`](.github/workflows/daily_report.yml) that executes daily at **02:30 UTC / 8:00 AM IST**.

### 1. Add Repository Secrets

Navigate to your GitHub Repository:
`https://github.com/sharath-00/bbmp_daily_ticket_report` -> **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**.

Add the following secrets:

| Secret Name | Description | Example |
| :--- | :--- | :--- |
| `SMTP_SERVER` | SMTP host server | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP server port | `587` |
| `SMTP_USE_TLS` | Enable TLS encryption | `true` |
| `SMTP_USERNAME` | SMTP account username / email | `your-email@gmail.com` |
| `SMTP_PASSWORD` | App Password (Gmail 16-character App Password) | `xxxx xxxx xxxx xxxx` |
| `SENDER_EMAIL` | Display sender email address | `your-email@gmail.com` |
| `RECIPIENT_EMAILS` | Comma-separated recipient list | `official1@example.com, official2@example.com` |
| `EMAIL_SUBJECT_PREFIX` | Subject prefix for reports | `[BBMP Smart Light Ticket Report]` |

---

### 2. Manual Workflow Execution

You can trigger the report manually at any time:
1. Go to the **Actions** tab in `https://github.com/sharath-00/bbmp_daily_ticket_report`.
2. Select **BBMP Daily Ticket Analytics Email Report** workflow.
3. Click **Run workflow**, set optional parameters (such as `dry_run` or `target_date`), and click **Run workflow**.

---

## Local Development & Testing

### Installation
```bash
pip install -r requirements.txt
```

### Environment Configuration
Copy `.env.example` to `.env` and update credentials:
```bash
cp .env.example .env
```

### Run Tests
```bash
python -m unittest test_ticket_engine.py
```

### Run Daily Report Locally
```bash
# Dry run (generate preview without sending email)
python send_daily_report.py --dry-run

# Dispatch email report
python send_daily_report.py
```
