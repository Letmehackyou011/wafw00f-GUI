from __future__ import annotations

from datetime import datetime

from wafw00f_gui.runner import ScanResult


def generate_smart_report(result: ScanResult, developer_name: str) -> str:
    timestamp = datetime.utcnow().isoformat() + "Z"
    detected = ", ".join(result.detected_wafs) if result.detected_wafs else "No WAF detected"

    lines: list[str] = [
        "=== Smart Security Report (Heuristic) ===",
        f"Generated: {timestamp}",
        f"Target: {result.target_url or 'N/A'}",
        f"Maintainer (GUI): {developer_name}",
        f"Exit code: {result.exit_code if result.exit_code is not None else 'error'}",
        f"Detected protection: {detected}",
        f"Request count: {result.request_count if result.request_count is not None else 'unknown'}",
        "",
        "Assessment:",
    ]

    if result.exit_code is None:
        lines.append("- Scan did not finish successfully; network issues or command errors are likely.")
    elif result.detected_wafs:
        lines.append("- A WAF/security layer is present and likely filtering malicious payload patterns.")
        lines.append("- Detection confidence is moderate; verify manually with controlled testing.")
    else:
        lines.append("- No WAF signature was detected by wafw00f in this run.")
        lines.append("- Absence of detection does not guarantee absence of protection.")

    lines.extend([
        "",
        "Possible attack types to prioritize in authorized security testing:",
        "- SQL injection attempts against input parameters",
        "- Cross-site scripting (reflected and stored)",
        "- Path traversal and local file inclusion patterns",
        "- Command injection and unsafe deserialization vectors",
        "- HTTP request smuggling and header manipulation",
        "- Layer 7 denial-of-service behavior",
        "",
        "Important:",
        "- This is a heuristic assistant report, not proof of exploitability.",
        "- Only test targets you are legally authorized to assess.",
        "=== End Smart Security Report ===",
    ])

    return "\n".join(lines)
