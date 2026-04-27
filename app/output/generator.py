import os
from datetime import datetime

import pandas as pd


def format_currency(value):
    """Format integer value as Indian currency string."""
    if value is None:
        return "N/A"
    
    # Convert to string and handle already formatted values
    val_str = str(value).replace(",", "")
    
    try:
        val_int = int(val_str)
    except ValueError:
        return str(value)
    
    # Indian numbering: crore, lakh, thousand
    if val_int >= 10000000:  # Crore
        crore = val_int // 10000000
        remainder = (val_int % 10000000) // 100000
        if remainder > 0:
            return f"₹ {crore},{remainder:02d},00,000"
        return f"₹ {crore},00,00,000"
    elif val_int >= 100000:  # Lakh
        lakh = val_int // 100000
        remainder = (val_int % 100000) // 1000
        if remainder > 0:
            return f"₹ {lakh},{remainder:02d},000"
        return f"₹ {lakh},00,000"
    else:  # Regular thousands
        return f"₹ {val_int:,}"


def format_shares(count, face_value=None):
    """Format shares count with optional face value."""
    if count is None:
        return "N/A"
    
    try:
        count_int = int(str(count).replace(",", ""))
        if face_value:
            return f"{count_int:,} shares @ ₹ {face_value} each"
        return f"{count_int:,} shares"
    except ValueError:
        return str(count)


def _parse_date(date_str):
    """Parse date string in DD/MM/YYYY format."""
    try:
        return datetime.strptime(date_str, "%d/%m/%Y")
    except (ValueError, TypeError):
        return datetime.min  # Sort unknown dates to the beginning


def generate_output(events):
    """Generate comprehensive output with clear source documentation and markdown summary."""
    # Sort events chronologically
    events = sorted(events, key=lambda e: _parse_date(e.date or ""))
    
    rows = []
    """Generate comprehensive output with clear source documentation and markdown summary."""
    rows = []

    markdown_lines = [
        "# DRHP Capital Structure Table - Apex Corporation Private Limited",
        "",
        "## Summary of Authorised Share Capital Changes",
        "",
        "| Date | From (Previous) | To (Revised) | Particulars of Change | Source Documents | Confidence | Remarks |",
        "|------|-----------------|--------------|----------------------|------------------|------------|---------|",
    ]

    for e in events:
        old_capital_str = format_currency(e.old_capital)
        new_capital_str = format_currency(e.new_capital)
        particulars = []

        if e.old_shares is not None or e.new_shares is not None:
            particulars.append(
                f"{format_shares(e.old_shares, e.face_value_per_share)} → {format_shares(e.new_shares, e.face_value_per_share)}"
            )
        if e.event_type:
            particulars.append(e.event_type.replace("_", " ").title())
        if e.face_value_per_share:
            particulars.append(f"Face value ₹ {e.face_value_per_share} per share")

        source_docs = "; ".join(e.sources) if e.sources else "No sources"
        remarks = []
        if e.conflicts:
            remarks.append("Conflicting values detected")
        if e.missing_fields:
            remarks.append(f"Missing fields: {', '.join(e.missing_fields)}")
        if e.notes:
            remarks.extend(e.notes)

        particulars_text = " | ".join(particulars) if particulars else "n/a"
        remarks_text = " | ".join(remarks) if remarks else "Verified from sources"

        rows.append({
            "Date": e.date or "N/A",
            "From (Previous)": old_capital_str,
            "To (Revised)": new_capital_str,
            "Particulars of Change": particulars_text,
            "Source Documents": source_docs,
            "Confidence": e.confidence.upper(),
            "Remarks": remarks_text,
        })

        markdown_lines.append(
            f"| **{e.date or 'Unknown'}** | {old_capital_str} | {new_capital_str} | {particulars_text} | {source_docs} | **{e.confidence.upper()}** | {remarks_text} |"
        )

    markdown_lines.extend(["", "---", "", "## Detailed Capital Structure Evolution", ""])

    for index, e in enumerate(events, start=1):
        markdown_lines.extend([
            f"### Event {index}: {e.date or 'Unknown'}",
            "",
            f"**Old Authorised Capital:** {format_currency(e.old_capital)}",
            f"**New Authorised Capital:** {format_currency(e.new_capital)}",
            f"**Particulars:** {format_shares(e.old_shares, e.face_value_per_share)} → {format_shares(e.new_shares, e.face_value_per_share)}",
            "",
            "**Source Documents with Evidence:**",
        ])
        for source in e.sources:
            markdown_lines.append(f"- {source}")

        markdown_lines.extend([
            "",
            f"**Confidence Level:** {e.confidence.upper()}",
            f"**Remarks:** {remarks_text}",
            "",
        ])

    os.makedirs("data/outputs", exist_ok=True)
    df = pd.DataFrame(rows, columns=["Date", "From (Previous)", "To (Revised)", "Particulars of Change", "Source Documents", "Confidence", "Remarks"])
    # Sort by date chronologically using flexible parsing
    df['Date_parsed'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
    df = df.sort_values(by='Date_parsed').drop(columns=['Date_parsed'])
    df.to_csv("data/outputs/result.csv", index=False)

    with open("data/outputs/CAPITAL_STRUCTURE.md", "w", encoding="utf-8") as md_file:
        md_file.write("\n".join(markdown_lines))

    return df
