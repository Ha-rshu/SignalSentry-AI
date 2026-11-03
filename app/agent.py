from app.config import META_API_KEY, META_API_BASE_URL, META_MODEL_NAME

def meta_api_status() -> tuple[bool, str]:
    if not META_API_KEY:
        return False, "Meta API credentials are not configured yet. The app is running in local demo mode."
    if not META_API_BASE_URL or not META_MODEL_NAME:
        return False, "API key is present, but the official endpoint URL and model name still need to be configured from your hackathon instructions."
    return True, "Credentials are configured. Add the verified Meta API request format before enabling live calls."

def build_investigation_brief(row: dict) -> str:
    evidence = row.get("evidence", [])
    labels = row.get("risk_labels", [])
    evidence_text = ", ".join(evidence) if evidence else "No configured keyword rule matched."
    label_text = ", ".join(labels) if labels else "No label"
    return f"""
### Investigation brief

**Item:** {row.get('post_id', 'Unknown')}  
**Platform field:** {row.get('platform', 'Unknown')}  
**Rule-based indicator score:** {row.get('risk_score', 0)}/100  
**Matched categories:** {label_text}  

**Observed text:**  
> {row.get('text', '')}

**Evidence terms:** {evidence_text}

**Analyst interpretation:** The configured local rules identified the indicators above. This is a triage signal only, not proof of malicious activity or attribution to an individual.

**Recommended next steps:**
1. Verify the original source and context using authorized data.
2. Preserve the item and timestamp for audit.
3. Seek independent corroboration before escalating.
4. Record analyst decisions and uncertainty.
"""
