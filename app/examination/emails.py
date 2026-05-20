from django.core.mail import EmailMultiAlternatives
from django.conf import settings


BRAND = "ZKAI"
BRAND_COLOR = "#4F46E5"


def _send(to_email: str, subject: str, text_body: str, html_body: str):
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
    )
    msg.attach_alternative(html_body, "text/html")
    try:
        msg.send(fail_silently=False)
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send to {to_email}: {e}")


def _base_html(title: str, content: str) -> str:
    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
</head>
<body style="margin:0;padding:0;background:#f4f4f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:40px 16px;">
      <table width="600" cellpadding="0" cellspacing="0"
             style="background:#ffffff;border-radius:12px;overflow:hidden;
                    box-shadow:0 4px 24px rgba(0,0,0,0.08);max-width:600px;width:100%;">
        <!-- Header -->
        <tr>
          <td style="background:{BRAND_COLOR};padding:28px 40px;">
            <h1 style="margin:0;color:#ffffff;font-size:22px;font-weight:700;
                       letter-spacing:-0.3px;">{BRAND}</h1>
            <p style="margin:4px 0 0;color:rgba(255,255,255,0.75);font-size:13px;">
              Examination & Result Verification System
            </p>
          </td>
        </tr>
        <!-- Body -->
        <tr>
          <td style="padding:36px 40px;">
            {content}
          </td>
        </tr>
        <!-- Footer -->
        <tr>
          <td style="background:#f9fafb;padding:20px 40px;border-top:1px solid #e5e7eb;">
            <p style="margin:0;font-size:12px;color:#9ca3af;text-align:center;">
              This is an automated message from {BRAND} Examination System.<br>
              Please do not reply to this email.
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""


def _info_row(label: str, value: str) -> str:
    return f"""
<tr>
  <td style="padding:8px 0;border-bottom:1px solid #f3f4f6;">
    <span style="font-size:12px;color:#6b7280;display:block;">{label}</span>
    <span style="font-size:14px;color:#111827;font-weight:500;">{value}</span>
  </td>
</tr>"""


def _badge(text: str, color: str, bg: str) -> str:
    return (f'<span style="display:inline-block;padding:4px 12px;border-radius:999px;'
            f'font-size:12px;font-weight:600;color:{color};background:{bg};">{text}</span>')


# ─────────────────────────────────────────────────────────────────
# Email 1 — Registration Submitted
# ─────────────────────────────────────────────────────────────────

def send_registration_submitted(registration):
    subject = f"[{BRAND}] Registration Received — {registration.reference_number}"

    content = f"""
<h2 style="margin:0 0 8px;font-size:20px;color:#111827;">Application Received</h2>
<p style="margin:0 0 24px;color:#6b7280;font-size:14px;line-height:1.6;">
  Thank you <strong>{registration.full_name}</strong>, your exam registration has been
  successfully submitted and is under review.
</p>
<table width="100%" cellpadding="0" cellspacing="0"
       style="border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;margin-bottom:24px;">
  <tbody>
    {_info_row("Reference Number", registration.reference_number)}
    {_info_row("Exam Applied", registration.exam.title if registration.exam else "N/A")}
    {_info_row("Education Level", registration.education_level.title())}
    {_info_row("Submitted At", registration.submitted_at.strftime("%d %b %Y, %I:%M %p UTC"))}
    {_info_row("Status", "Pending Review")}
  </tbody>
</table>
<div style="background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:16px;margin-bottom:24px;">
  <p style="margin:0;font-size:13px;color:#92400e;">
    <strong>What's next?</strong> Our admin team will review your documents and
    notify you via email once a decision has been made.
  </p>
</div>
"""

    text = (f"Registration Received\n\nHello {registration.full_name},\n\n"
            f"Your registration has been submitted.\n"
            f"Reference Number: {registration.reference_number}\n"
            f"Exam: {registration.exam.title if registration.exam else 'N/A'}\n"
            f"Status: Pending Review\n\n"
            f"You will be notified when a decision is made.")

    _send(registration.email, subject, text, _base_html(subject, content))


# ─────────────────────────────────────────────────────────────────
# Email 2 — Registration Approved
# ─────────────────────────────────────────────────────────────────

def send_registration_approved(registration):
    exam = registration.exam
    subject = f"[{BRAND}] Registration Approved ✅ — {registration.reference_number}"

    content = f"""
<h2 style="margin:0 0 8px;font-size:20px;color:#111827;">Registration Approved</h2>
{_badge("APPROVED", "#065f46", "#d1fae5")}
<p style="margin:16px 0 24px;color:#6b7280;font-size:14px;line-height:1.6;">
  Congratulations <strong>{registration.full_name}</strong>! Your registration has been
  approved. Please find your exam details and Decentralized Identity (DID) below.
</p>

<h3 style="font-size:14px;font-weight:600;color:#374151;margin:0 0 12px;
           text-transform:uppercase;letter-spacing:0.05em;">Exam Details</h3>
<table width="100%" cellpadding="0" cellspacing="0"
       style="border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;margin-bottom:24px;">
  <tbody>
    {_info_row("Exam", exam.title if exam else "N/A")}
    {_info_row("Date", exam.date.strftime("%A, %d %B %Y") if exam else "N/A")}
    {_info_row("Time", exam.time.strftime("%I:%M %p") if exam else "N/A")}
    {_info_row("Venue", exam.venue if exam else "N/A")}
    {_info_row("Duration", f"{exam.duration_minutes} minutes" if exam else "N/A")}
    {_info_row("Reference Number", registration.reference_number)}
  </tbody>
</table>

<h3 style="font-size:14px;font-weight:600;color:#374151;margin:0 0 12px;
           text-transform:uppercase;letter-spacing:0.05em;">Your Decentralized Identity (DID)</h3>
<div style="background:#eef2ff;border:1px solid #c7d2fe;border-radius:8px;padding:16px;margin-bottom:24px;">
  <p style="margin:0 0 8px;font-size:12px;color:#4338ca;font-weight:600;">DID Identifier</p>
  <code style="font-size:12px;color:#312e81;word-break:break-all;display:block;
               background:#e0e7ff;padding:10px;border-radius:6px;line-height:1.6;">
    {registration.did or "Not assigned yet"}
  </code>
  <p style="margin:12px 0 0;font-size:12px;color:#6366f1;line-height:1.5;">
    This is your unique blockchain-linked identifier. After your exam result is published,
    this DID will be linked to your result hash for tamper-proof verification.
    Anyone can verify your result using your Certificate ID — without seeing your private details.
  </p>
</div>

<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:16px;">
  <p style="margin:0;font-size:13px;color:#166534;">
    <strong>Important:</strong> Bring a valid ID on exam day. Arrive 30 minutes before the
    scheduled time. Your face will be verified at check-in.
  </p>
</div>
"""

    text = (f"Registration Approved\n\nHello {registration.full_name},\n\n"
            f"Your registration has been APPROVED.\n\n"
            f"Exam: {exam.title if exam else 'N/A'}\n"
            f"Date: {exam.date.strftime('%d %B %Y') if exam else 'N/A'}\n"
            f"Time: {exam.time.strftime('%I:%M %p') if exam else 'N/A'}\n"
            f"Venue: {exam.venue if exam else 'N/A'}\n"
            f"Your DID: {registration.did}\n\n"
            f"Your DID is your blockchain identity. After results are published, "
            f"you can verify your result using your Certificate ID.")

    _send(registration.email, subject, text, _base_html(subject, content))


# ─────────────────────────────────────────────────────────────────
# Email 3 — Registration Rejected
# ─────────────────────────────────────────────────────────────────

def send_registration_rejected(registration):
    subject = f"[{BRAND}] Registration Update — {registration.reference_number}"

    content = f"""
<h2 style="margin:0 0 8px;font-size:20px;color:#111827;">Registration Status Update</h2>
{_badge("NOT APPROVED", "#991b1b", "#fee2e2")}
<p style="margin:16px 0 24px;color:#6b7280;font-size:14px;line-height:1.6;">
  Dear <strong>{registration.full_name}</strong>, after reviewing your application,
  we regret to inform you that your registration could not be approved at this time.
</p>
<table width="100%" cellpadding="0" cellspacing="0"
       style="border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;margin-bottom:24px;">
  <tbody>
    {_info_row("Reference Number", registration.reference_number)}
    {_info_row("Exam Applied", registration.exam.title if registration.exam else "N/A")}
    {_info_row("Reason", registration.rejection_reason or "Not specified")}
  </tbody>
</table>
<div style="background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:16px;">
  <p style="margin:0;font-size:13px;color:#9a3412;line-height:1.5;">
    If you believe this decision is incorrect or wish to re-apply, please contact
    the examination office with your reference number.
  </p>
</div>
"""

    text = (f"Registration Not Approved\n\nHello {registration.full_name},\n\n"
            f"Your registration ({registration.reference_number}) was not approved.\n"
            f"Reason: {registration.rejection_reason or 'Not specified'}\n\n"
            f"Contact the examination office if you have questions.")

    _send(registration.email, subject, text, _base_html(subject, content))


# ─────────────────────────────────────────────────────────────────
# Email 4 — Result Published (Full Details — Student Only)
# ─────────────────────────────────────────────────────────────────

def send_result_published(result):
    registration = result.registration
    exam = result.exam
    frontend_url = __import__("django.conf", fromlist=["settings"]).settings.FRONTEND_URL
    verify_url = f"{frontend_url}/verify?cert={result.certificate_id}"

    passed = result.result_status == "pass"
    status_badge = (_badge("PASS", "#065f46", "#d1fae5") if passed
                    else _badge("FAIL", "#991b1b", "#fee2e2"))
    percentage = round(result.marks_obtained / result.total_marks * 100, 1) if result.total_marks else 0

    subject = f"[{BRAND}] Your Result is Published — {exam.title}"

    content = f"""
<h2 style="margin:0 0 8px;font-size:20px;color:#111827;">Your Result is Published</h2>
{status_badge}
<p style="margin:16px 0 24px;color:#6b7280;font-size:14px;line-height:1.6;">
  Dear <strong>{registration.full_name}</strong>, your result for
  <strong>{exam.title}</strong> has been published and recorded on the blockchain.
</p>

<h3 style="font-size:14px;font-weight:600;color:#374151;margin:0 0 12px;
           text-transform:uppercase;letter-spacing:0.05em;">Your Result</h3>
<table width="100%" cellpadding="0" cellspacing="0"
       style="border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;margin-bottom:24px;">
  <tbody>
    {_info_row("Student Name", registration.full_name)}
    {_info_row("Exam", exam.title)}
    {_info_row("Marks Obtained", f"{result.marks_obtained} / {result.total_marks}")}
    {_info_row("Percentage", f"{percentage}%")}
    {_info_row("Grade", result.grade)}
    {_info_row("Result Status", result.result_status.upper())}
    {_info_row("Certificate ID", result.certificate_id)}
  </tbody>
</table>

<h3 style="font-size:14px;font-weight:600;color:#374151;margin:0 0 12px;
           text-transform:uppercase;letter-spacing:0.05em;">Blockchain Verification</h3>
<div style="background:#eef2ff;border:1px solid #c7d2fe;border-radius:8px;
            padding:16px;margin-bottom:24px;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td style="padding:4px 0;">
      <span style="font-size:12px;color:#6366f1;display:block;">Your DID</span>
      <code style="font-size:11px;color:#312e81;word-break:break-all;">
        {registration.did or "N/A"}
      </code>
    </td></tr>
    <tr><td style="padding:8px 0 4px;">
      <span style="font-size:12px;color:#6366f1;display:block;">Result Hash (SHA-256)</span>
      <code style="font-size:11px;color:#312e81;word-break:break-all;">
        {result.result_hash}
      </code>
    </td></tr>
    <tr><td style="padding:8px 0 4px;">
      <span style="font-size:12px;color:#6366f1;display:block;">Blockchain TX</span>
      <code style="font-size:11px;color:#312e81;word-break:break-all;">
        {result.blockchain_tx}
      </code>
    </td></tr>
  </table>
</div>

<h3 style="font-size:14px;font-weight:600;color:#374151;margin:0 0 12px;
           text-transform:uppercase;letter-spacing:0.05em;">Public Verification</h3>
<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:16px;margin-bottom:24px;">
  <p style="margin:0 0 12px;font-size:13px;color:#166534;line-height:1.5;">
    Anyone can verify your result using your <strong>Certificate ID</strong> below.
    Public verification only reveals your name, exam, and pass/fail status —
    <strong>your marks and personal details remain private</strong>.
  </p>
  <div style="background:#dcfce7;border-radius:6px;padding:10px;text-align:center;">
    <code style="font-size:16px;font-weight:700;color:#14532d;letter-spacing:0.05em;">
      {result.certificate_id}
    </code>
  </div>
  <p style="margin:12px 0 0;font-size:12px;color:#166534;text-align:center;">
    Verify at: <a href="{verify_url}" style="color:#16a34a;">{verify_url}</a>
  </p>
</div>
"""

    text = (f"Result Published\n\nHello {registration.full_name},\n\n"
            f"Your result for {exam.title} is published.\n\n"
            f"Marks: {result.marks_obtained}/{result.total_marks} ({percentage}%)\n"
            f"Grade: {result.grade}\n"
            f"Status: {result.result_status.upper()}\n"
            f"Certificate ID: {result.certificate_id}\n"
            f"Result Hash: {result.result_hash}\n"
            f"Blockchain TX: {result.blockchain_tx}\n"
            f"Your DID: {registration.did}\n\n"
            f"Public verification link: {verify_url}\n"
            f"(Public verifiers only see name + pass/fail — your marks stay private)")

    _send(registration.email, subject, text, _base_html(subject, content))