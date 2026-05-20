import csv
import io
from datetime import datetime

from django.http import HttpResponse
from django.utils.dateparse import parse_date
from django.views import View

from blockchain_layer.models import BlockchainRecord
from examination.models import Registration, Result
from monitoring.models import AIAlert


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _parse_date_range(request):
    from_date = request.GET.get("from")
    to_date = request.GET.get("to")

    return (
        parse_date(from_date) if from_date else None,
        parse_date(to_date) if to_date else None,
    )


def _apply_date_filter(qs, field, from_date, to_date):
    if from_date:
        qs = qs.filter(**{f"{field}__date__gte": from_date})

    if to_date:
        qs = qs.filter(**{f"{field}__date__lte": to_date})

    return qs


def _csv_response(filename, headers, rows):
    response = HttpResponse(content_type="text/csv")

    response["Content-Disposition"] = (
        f'attachment; filename="{filename}"'
    )

    response["Access-Control-Expose-Headers"] = (
        "Content-Disposition"
    )

    writer = csv.writer(response)

    writer.writerow(headers)

    for row in rows:
        writer.writerow(row)

    return response


def _pdf_response(filename, title, headers, rows):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=20,
        leftMargin=20,
        topMargin=30,
        bottomMargin=20,
    )

    styles = getSampleStyleSheet()

    elements = []

    # Title
    elements.append(Paragraph(title, styles["Title"]))

    elements.append(
        Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            styles["Normal"],
        )
    )

    elements.append(Spacer(1, 16))

    # Table
    data = [headers] + rows

    col_count = len(headers)

    col_width = (landscape(A4)[0] - 40) / col_count

    table = Table(
        data,
        colWidths=[col_width] * col_count,
        repeatRows=1,
    )

    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4F46E5")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.HexColor("#F9FAFB"),
                ],
            ),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E5E7EB")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )

    elements.append(table)

    doc.build(elements)

    buffer.seek(0)

    response = HttpResponse(
        buffer,
        content_type="application/pdf",
    )

    response["Content-Disposition"] = (
        f'attachment; filename="{filename}"'
    )

    response["Access-Control-Expose-Headers"] = (
        "Content-Disposition"
    )

    return response


def _make_response(fmt, filename_base, title, headers, rows):
    today = datetime.now().strftime("%Y-%m-%d")

    if fmt == "pdf":
        return _pdf_response(
            f"{filename_base}-{today}.pdf",
            title,
            headers,
            rows,
        )

    return _csv_response(
        f"{filename_base}-{today}.csv",
        headers,
        rows,
    )


# ─────────────────────────────────────────────────────────────
# Export Views
# ─────────────────────────────────────────────────────────────

class ExportBlockchainView(View):

    def get(self, request):
        print(">>> ExportBlockchainView.get() called")
        print(">>> Query params:", request.GET)

        fmt = request.GET.get("format", "csv")

        from_date, to_date = _parse_date_range(request)

        qs = BlockchainRecord.objects.all()

        qs = _apply_date_filter(
            qs,
            "timestamp",
            from_date,
            to_date,
        )

        headers = [
            "ID",
            "Record Type",
            "Student",
            "Exam",
            "Transaction Hash",
            "Block Number",
            "Verification Status",
            "Timestamp",
        ]

        rows = [
            [
                r.id,
                r.record_type.replace("_", " ").title(),
                r.related_student or "—",
                r.related_exam or "—",
                r.transaction_hash,
                r.block_number,
                r.verification_status,
                r.timestamp.strftime("%Y-%m-%d %H:%M"),
            ]
            for r in qs
        ]

        return _make_response(
            fmt,
            "blockchain-records",
            "Blockchain Verification Logs",
            headers,
            rows,
        )


class ExportRegistrationsView(View):

    def get(self, request):
        fmt = request.GET.get("format", "csv")

        from_date, to_date = _parse_date_range(request)

        qs = Registration.objects.select_related(
            "exam"
        ).all()

        qs = _apply_date_filter(
            qs,
            "submitted_at",
            from_date,
            to_date,
        )

        headers = [
            "ID",
            "Reference No",
            "Full Name",
            "Father Name",
            "CNIC",
            "Email",
            "Phone",
            "Education Level",
            "Exam",
            "Status",
            "DID",
            "Submitted At",
        ]

        rows = [
            [
                r.id,
                r.reference_number,
                r.full_name,
                r.father_name,
                r.cnic,
                r.email,
                r.phone,
                r.education_level,
                r.exam.title if r.exam else "—",
                r.status,
                r.did or "—",
                r.submitted_at.strftime("%Y-%m-%d %H:%M"),
            ]
            for r in qs
        ]

        return _make_response(
            fmt,
            "registrations",
            "Student Registrations",
            headers,
            rows,
        )


class ExportResultsView(View):

    def get(self, request):
        fmt = request.GET.get("format", "csv")

        from_date, to_date = _parse_date_range(request)

        qs = Result.objects.select_related(
            "registration",
            "exam",
        ).filter(
            is_published=True
        )

        qs = _apply_date_filter(
            qs,
            "published_at",
            from_date,
            to_date,
        )

        headers = [
            "ID",
            "Student Name",
            "Reference No",
            "Exam",
            "Marks",
            "Total",
            "Grade",
            "Status",
            "Certificate ID",
            "Result Hash",
            "Blockchain TX",
            "Published At",
        ]

        rows = [
            [
                r.id,
                r.registration.full_name,
                r.registration.reference_number,
                r.exam.title if r.exam else "—",
                r.marks_obtained,
                r.total_marks,
                r.grade,
                r.result_status,
                r.certificate_id or "—",
                r.result_hash or "—",
                r.blockchain_tx or "—",
                (
                    r.published_at.strftime("%Y-%m-%d %H:%M")
                    if r.published_at
                    else "—"
                ),
            ]
            for r in qs
        ]

        return _make_response(
            fmt,
            "results",
            "Published Exam Results",
            headers,
            rows,
        )


class ExportAlertsView(View):

    def get(self, request):
        fmt = request.GET.get("format", "csv")

        from_date, to_date = _parse_date_range(request)

        qs = AIAlert.objects.all()

        qs = _apply_date_filter(
            qs,
            "triggered_at",
            from_date,
            to_date,
        )

        headers = [
            "ID",
            "Alert Type",
            "Severity",
            "Description",
            "Resolved",
            "Triggered At",
            "Resolved At",
        ]

        rows = [
            [
                a.id,
                a.alert_type,
                a.severity,
                a.description,
                "Yes" if a.is_resolved else "No",
                a.triggered_at.strftime("%Y-%m-%d %H:%M"),
                (
                    a.resolved_at.strftime("%Y-%m-%d %H:%M")
                    if a.resolved_at
                    else "—"
                ),
            ]
            for a in qs
        ]

        return _make_response(
            fmt,
            "ai-alerts",
            "AI Monitoring Alerts",
            headers,
            rows,
        )