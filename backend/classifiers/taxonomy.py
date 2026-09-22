"""Extensible social-engineering tactic taxonomy and phrase detector."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from backend.utils.text import normalize_text


# Direct safety advice often repeats the exact words an attacker would use
# (for example, "never share OTP"). In the absence of diarisation, a narrow
# local polarity guard is safer than treating every quoted request as active.
SAFETY_PREFIX = re.compile(
    r"(?:\bdo not\b|\bdon't\b|\bnever\b|\bavoid\b|\bmust not\b|\bshould not\b|\brefuse to\b|\bstop\b)\s+(?:(?:ever|please|directly)\s+)?$",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class TacticDefinition:
    name: str
    stage: str
    weight: int
    explanation: str
    attack_categories: tuple[str, ...]
    phrases: tuple[str, ...]


TACTICS: tuple[TacticDefinition, ...] = (
    TacticDefinition(
        "IDENTITY_CLAIM", "IDENTITY_CLAIM", 5,
        "Caller asserted an identity or official role.",
        ("IMPERSONATION",),
        ("this is inspector", "this is officer", "i am officer", "i am calling from", "main bol raha", "main bank", "मैं बोल रहा", "நான் பேசுகிறேன்"),
    ),
    TacticDefinition(
        "AUTHORITY_IMPERSONATION", "AUTHORITY_IMPERSONATION", 16,
        "Caller claimed authority associated with a government, police, regulator, bank, or courier.",
        ("DIGITAL_ARREST", "GOVERNMENT_IMPERSONATION", "BANK_IMPERSONATION", "COURIER_CUSTOMS"),
        (
            "cybercrime department", "cyber crime department", "cybercrime", "cyber crime", "cyber cell", "police department",
            "cbi", "rbi", "enforcement directorate", "ed officer", "income tax department",
            "customs department", "customs officer", "from customs", "telecom department", "bank security team", "bank security officer",
            "bank fraud department", "bank security", "kyc desk", "telecom security team", "courier department", "government officer", "customs",
            "साइबर क्राइम", "पुलिस विभाग", "आरबीआई", "सीबीआई", "कस्टम्स",
            "சைபர் கிரைம்", "காவல் துறை", "ரிசர்வ் வங்கி", "சுங்கத் துறை",
        ),
    ),
    TacticDefinition(
        "THREAT", "FEAR_ESCALATION", 15,
        "Caller used legal, account, service, or safety consequences to create fear.",
        ("DIGITAL_ARREST", "KYC", "BANK_IMPERSONATION", "SIM_SCAM"),
        (
            "arrest warrant", "you will be arrested", "criminal case", "legal action",
            "money laundering case", "account will be blocked", "account block hoga", "account is frozen",
            "sim will be blocked", "sim band ho jayega", "your number will be disconnected", "taken into custody", "account will be disabled", "account is disabled", "your money is at risk", "police case",
            "गिरफ्तार", "कानूनी कार्रवाई", "अकाउंट ब्लॉक", "मनी लॉन्ड्रिंग",
            "கைது", "வழக்கு பதிவு", "கணக்கு முடக்க", "போலீஸ் வழக்கு",
        ),
    ),
    TacticDefinition(
        "URGENCY", "URGENCY", 10,
        "Caller imposed an immediate deadline to reduce time for independent verification.",
        ("DIGITAL_ARREST", "OTP", "UPI_PAYMENT", "KYC"),
        (
            "immediately", "right now", "within 10 minutes", "within ten minutes",
            "urgent", "final warning", "act now", "before it is too late", "next ten minutes", "in the next ten minutes",
            "तुरंत", "अभी", "जल्दी", "अंतिम चेतावनी",
            "உடனே", "இப்போதே", "அவசரம்", "கடைசி எச்சரிக்கை",
        ),
    ),
    TacticDefinition(
        "ISOLATION", "ISOLATION", 14,
        "Caller attempted to isolate the person from help or independent verification.",
        ("DIGITAL_ARREST", "FAMILY_EMERGENCY"),
        (
            "do not disconnect", "don't disconnect", "stay on the call", "stay connected", "do not tell anyone",
            "don't tell anyone", "keep this confidential", "do not contact your family",
            "do not call the bank", "do not ring your bank", "keep the call private", "keep this private", "keep the matter private", "keep this line open", "do not speak to anyone", "do not call anyone", "do not tell your family", "do not call her", "do not call them", "line pe raho", "call mat kaatna", "किसी को मत बताना", "कॉल मत काटना",
            "फोन मत काटना", "यहीं रहो", "யாரிடமும் சொல்லாதீர்கள்", "அழைப்பை துண்டிக்காதீர்கள்",
            "குடும்பத்தினரை தொடர்பு கொள்ளாதீர்கள்",
        ),
    ),
    TacticDefinition(
        "CREDENTIAL_REQUEST", "CREDENTIAL_EXTRACTION", 17,
        "Caller requested a secret authentication factor or sensitive identity information.",
        ("OTP", "KYC", "BANK_IMPERSONATION"),
        (
            "share your otp", "tell me the otp", "verification code", "share your pin",
            "tell me your cvv", "share your password", "aadhaar number", "pan number",
            "one time password", "share otp", "give otp", "read the code", "tell me the code",
            "six digit code", "six digit security code", "authentication code", "otp batao", "ओटीपी बताइए", "पिन बताइए",
            "ஆதார் எண்", "ஓடிபி சொல்லுங்கள்", "பின் எண்ணை சொல்லுங்கள்",
        ),
    ),
    TacticDefinition(
        "FINANCIAL_ACTION", "FINANCIAL_EXTRACTION", 20,
        "Caller asked for a payment, transfer, or movement of funds.",
        ("UPI_PAYMENT", "DIGITAL_ARREST", "INVESTMENT", "BANK_IMPERSONATION"),
        (
            "transfer money", "send money", "send payment", "upi payment", "transfer using upi", "scan this qr",
            "security deposit", "verification amount", "safe account", "protected account", "processing charge", "clearance fee", "pay using upi", "pay the charge", "release charge", "pay the release",
            "pay now", "unless you pay", "bank transfer", "transfer the amount", "पैसे ट्रांसफर",
            "move your balance", "add beneficiary", "pay to release", "पेमेंट भेजो", "upi से भेजो", "पैसा भेजो", "பணம் அனுப்புங்கள்",
            "யுபிஐ மூலம்", "பாதுகாப்பான கணக்கு", "தொகையை மாற்றுங்கள்",
        ),
    ),
    TacticDefinition(
        "REMOTE_ACCESS", "CREDENTIAL_EXTRACTION", 19,
        "Caller requested remote access or screen sharing, which can expose accounts and credentials.",
        ("REMOTE_ACCESS", "BANK_IMPERSONATION"),
        (
            "install anydesk", "download anydesk", "anydesk install", "install teamviewer", "screen sharing", "share your screen", "view the screen",
            "download this application", "install this app", "remote access", "give me control",
            "ऐप इंस्टॉल", "स्क्रीन शेयर", "ऐनीडेस्क", "ஆப்ஸை நிறுவுங்கள்",
            "திரையை பகிருங்கள்", "எனிடெஸ்க்",
        ),
    ),
    TacticDefinition(
        "TAMPER_EVASION", "ISOLATION", 13,
        "Caller attempted to disable a safety control or conceal the interaction from protective help.",
        ("TAMPER_EVASION", "IMPERSONATION"),
        (
            "disable this app", "disable the app", "turn off this app", "turn off scam detection",
            "disable security warning", "security app is malware", "this app is malware", "mute your phone",
            "mute the phone", "close the security app",
        ),
    ),
    TacticDefinition(
        "TRUST_BUILDING", "IDENTITY_CLAIM", 4,
        "Caller attempted to establish legitimacy using verification language.",
        ("IMPERSONATION",),
        (
            "official verification", "official procedure", "case id", "badge number",
            "recorded line", "for your safety", "trust me", "सरकारी प्रक्रिया",
            "அதிகாரப்பூர்வ நடைமுறை",
        ),
    ),
    TacticDefinition(
        "FAMILY_EMERGENCY", "FEAR_ESCALATION", 15,
        "Caller used a family emergency narrative to create immediate emotional pressure.",
        ("FAMILY_EMERGENCY",),
        (
            "your son had an accident", "your daughter is in trouble", "your son", "your daughter", "family emergency",
            "do not call them", "hospital emergency", "accident case", "accident", "आपका बेटा",
            "आपकी बेटी", "குடும்ப அவசரம்", "விபத்து ஏற்பட்டுள்ளது",
        ),
    ),
)


def detect_tactics(text: str) -> list[dict[str, Any]]:
    """Detect direct behavioral indicators, preserving explainable phrase evidence."""
    normalized = normalize_text(text)
    findings: list[dict[str, Any]] = []
    for definition in TACTICS:
        hits = []
        for phrase in definition.phrases:
            phrase_normalized = normalize_text(phrase)
            match = re.search(re.escape(phrase_normalized), normalized)
            if match and not _safety_advice_context(normalized, match.start()):
                hits.append({
                    "phrase": phrase,
                    "start_char": match.start(),
                    "end_char": match.end(),
                })
        if hits:
            confidence = min(0.98, 0.58 + 0.12 * len(hits))
            findings.append({
                "tactic": definition.name,
                "stage": definition.stage,
                "weight": definition.weight,
                "confidence": round(confidence, 2),
                "evidence": hits,
                "explanation": definition.explanation,
                "attack_categories": list(definition.attack_categories),
            })
    return findings


def _safety_advice_context(text: str, start: int) -> bool:
    """Suppress a quoted request only when it follows a narrow safety negation."""
    prefix = text[max(0, start - 56):start]
    return bool(SAFETY_PREFIX.search(prefix))


def aggregate_tactics(segment_findings: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    aggregate: dict[str, dict[str, Any]] = {}
    for findings in segment_findings:
        for item in findings:
            key = item["tactic"]
            if key not in aggregate:
                aggregate[key] = {**item, "occurrences": 0, "evidence": []}
            aggregate[key]["occurrences"] += 1
            aggregate[key]["evidence"].extend(item["evidence"])
            aggregate[key]["confidence"] = max(aggregate[key]["confidence"], item["confidence"])
    return sorted(aggregate.values(), key=lambda item: (-item["weight"], item["tactic"]))


def attack_categories(tactics: list[dict[str, Any]]) -> list[str]:
    values = defaultdict(int)
    for tactic in tactics:
        for category in tactic["attack_categories"]:
            values[category] += tactic["weight"]
    return [name for name, _ in sorted(values.items(), key=lambda item: (-item[1], item[0]))]
