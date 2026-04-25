import os

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


def generate_output(events):
    """Generate comprehensive output with clear source documentation."""
    rows = []

    for e in events:
        # Format capital information
        old_capital_str = format_currency(e.old_capital)
        new_capital_str = format_currency(e.new_capital)
        
        # Get source documents with file paths
        source_docs = "; ".join(e.sources) if e.sources else "No sources"
        
        # Build detailed notes
        detail_notes = []
        
        # Add capital change details if available
        if e.old_shares and e.new_shares:
            detail_notes.append(
                f"Shares: {format_shares(e.old_shares, 10)} → {format_shares(e.new_shares, 10)}"
            )
        
        # Add validation notes
        if e.notes:
            detail_notes.extend(e.notes)
        
        # Add conflict information if present
        if e.conflicts:
            detail_notes.append(f"⚠ Conflicts: {', '.join(str(c) for c in e.conflicts)}")
        
        # Add missing fields info
        if e.missing_fields:
            detail_notes.append(f"Missing fields: {', '.join(e.missing_fields)}")
        
        final_notes = " | ".join(detail_notes) if detail_notes else "All fields verified from sources"
        
        rows.append({
            "Date": e.date or "N/A",
            "From (Previous)": old_capital_str,
            "To (Revised)": new_capital_str,
            "Source Documents": source_docs,
            "Confidence": e.confidence.upper(),
            "Details": final_notes
        })

    columns = ["Date", "From (Previous)", "To (Revised)", "Source Documents", "Confidence", "Details"]
    df = pd.DataFrame(rows, columns=columns)

    os.makedirs("data/outputs", exist_ok=True)
    df.to_csv("data/outputs/result.csv", index=False)

    return df
