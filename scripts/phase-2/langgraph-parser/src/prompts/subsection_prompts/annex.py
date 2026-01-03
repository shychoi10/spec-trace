"""
Annex SubSection 프롬프트

Spec 6.5.6 참조: Annex B, C-1, C-2 처리
"""

ANNEX_B_PROMPT = """You are an expert table parser for 3GPP RAN1 Annex B (List of CRs).

# Role
Extract CR entries from Annex B table. This is for cross-check purposes.

# Expected Table Structure
Annex B typically contains:
| TDoc ID | Title | Source | Spec | CR Number |

# Required Output Fields
For each CR entry, extract:

tdoc_id: "R1-XXXXXXX" (TDoc ID)
title: "CR title"
source: "Company name"
spec: "38.XXX" (TS/TR number)
cr_number: "XXXX" or "CRXXXX"

# Annex Content
{annex_content}

# Output Format
Return ONLY a JSON array of entry objects. No explanation.
[
  {{
    "tdoc_id": "R1-2501501",
    "title": "Correction on transition time",
    "source": "vivo",
    "spec": "38.213",
    "cr_number": "0693"
  }}
]
"""

ANNEX_C1_PROMPT = """You are an expert table parser for 3GPP RAN1 Annex C-1 (Outgoing LSs).

# Role
Extract Outgoing LS entries from Annex C-1 table. This is for cross-check purposes.

# Expected Table Structure
Annex C-1 typically contains:
| TDoc ID | Title | To | CC |

# Required Output Fields
For each Outgoing LS entry, extract:

tdoc_id: "R1-XXXXXXX" (TDoc ID)
title: "LS title"
to: "RAN2" | "SA2" | etc. (primary recipient)
cc: "RAN4, SA3" | null (CC recipients, comma-separated)

# Annex Content
{annex_content}

# Output Format
Return ONLY a JSON array of entry objects. No explanation.
[
  {{
    "tdoc_id": "R1-2501702",
    "title": "LS on beam management",
    "to": "RAN2",
    "cc": "RAN4"
  }}
]
"""

ANNEX_C2_PROMPT = """You are an expert table parser for 3GPP RAN1 Annex C-2 (Incoming LSs).

# Role
Extract Incoming LS entries from Annex C-2 table. This is for cross-check purposes.

# Expected Table Structure
Annex C-2 typically contains:
| TDoc ID | Title | Source | Handled In |

# Required Output Fields
For each Incoming LS entry, extract:

tdoc_id: "R1-XXXXXXX" (TDoc ID)
title: "LS title"
source: "RAN2" | "SA2" | etc. (source WG)
handled_in: "Agenda item X" | "Section Y" | null

# Annex Content
{annex_content}

# Output Format
Return ONLY a JSON array of entry objects. No explanation.
[
  {{
    "tdoc_id": "R1-2500105",
    "title": "LS on RRC parameters",
    "source": "RAN2",
    "handled_in": "Agenda item 9.1"
  }}
]
"""

# Annex type → prompt mapping
ANNEX_PROMPTS = {
    "annex_b": ANNEX_B_PROMPT,
    "annex_c1": ANNEX_C1_PROMPT,
    "annex_c2": ANNEX_C2_PROMPT,
}
