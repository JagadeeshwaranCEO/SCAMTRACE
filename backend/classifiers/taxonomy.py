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

# Hindi and Tamil safety advice commonly places the negation *after* the
# protected item ("OTP साझा न करें", "OTP-ஐ பகிர வேண்டாம்").  Checking a
# short suffix prevents those warnings from being mistaken for attacker
# requests without suppressing an earlier isolation phrase in the sentence.
SAFETY_SUFFIX = re.compile(
    r"(?:साझा\s+(?:न|मत)\s+कर(?:ें|ना)|(?:न|मत)\s+बत(?:ाएं|ाना|ाइए)|(?:न|मत)\s+दें|"
    r"பகிர\s+வேண்டாம்|சொல்ல\s+வேண்டாம்|கூற\s+வேண்டாம்|கொடுக்க\s+வேண்டாம்|"
    r"பகிராதீர்கள்|சொல்லாதீர்கள்|கூறாதீர்கள்)",
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
        (
            "this is inspector", "this is officer", "i am officer", "i am calling from",
            "main bol raha", "main bank", "मैं बोल रहा", "मैं बोल रही", "से बोल रहा हूं",
            "से बोल रही हूं", "நான் பேசுகிறேன்", "பேசுகிறேன்",
        ),
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
            "साइबर क्राइम", "साइबर अपराध", "साइबर सेल", "पुलिस विभाग", "पुलिस अधिकारी",
            "मुंबई पुलिस", "दिल्ली पुलिस", "आरबीआई", "भारतीय रिजर्व बैंक", "सीबीआई",
            "कस्टम्स", "कस्टम विभाग", "कस्टम अधिकारी", "सीमा शुल्क", "बैंक सुरक्षा विभाग", "दूरसंचार विभाग",
            "टेलीकॉम विभाग", "சைபர் கிரைம்", "சைபர் குற்றப்பிரிவு", "காவல் துறை",
            "காவல்துறையிலிருந்து", "காவல் அதிகாரி", "ரிசர்வ் வங்கி", "இந்திய ரிசர்வ் வங்கி",
            "சுங்கத் துறை", "சுங்க அதிகாரி", "வங்கி பாதுகாப்பு பிரிவு", "தொலைத்தொடர்பு துறை",
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
            "गिरफ्तार", "गिरफ्तारी वारंट", "कानूनी कार्रवाई", "अकाउंट ब्लॉक", "खाता बंद",
            "खाता फ्रीज", "सिम बंद", "नंबर बंद", "मामला दर्ज", "मनी लॉन्ड्रिंग",
            "கைது", "கைது வாரண்ட்", "வழக்கு பதிவு", "கணக்கு முடக்க", "கணக்கு முடக்கப்படும்",
            "சிம் துண்டிக்கப்படும்", "எண் துண்டிக்கப்படும்", "குற்ற வழக்கு", "போலீஸ் வழக்கு",
        ),
    ),
    TacticDefinition(
        "URGENCY", "URGENCY", 10,
        "Caller imposed an immediate deadline to reduce time for independent verification.",
        ("DIGITAL_ARREST", "OTP", "UPI_PAYMENT", "KYC"),
        (
            "immediately", "right now", "within 10 minutes", "within ten minutes",
            "urgent", "final warning", "act now", "before it is too late", "next ten minutes", "in the next ten minutes",
            "तुरंत", "तुरन्त", "अभी", "इसी वक्त", "दस मिनट", "आज ही", "जल्दी", "अंतिम चेतावनी",
            "உடனே", "இப்போதே", "இப்பொழுதே", "பத்து நிமிடங்களில்", "இன்றே", "தாமதிக்காமல்",
            "அவசரம்", "கடைசி எச்சரிக்கை",
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
            "फोन मत काटना", "फोन मत रखिए", "लाइन पर रहिए", "किसी से मत कहना",
            "परिवार को मत बताना", "बैंक को फोन मत करना", "यहीं रहो", "யாரிடமும் சொல்லாதீர்கள்",
            "யாரிடமும் கூறாதீர்கள்", "குடும்பத்திடம் சொல்லாதீர்கள்", "அழைப்பை துண்டிக்காதீர்கள்",
            "அழைப்பை நிறுத்தாதீர்கள்", "லைனில் இருங்கள்", "வங்கியை அழைக்காதீர்கள்",
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
            "six digit code", "six digit security code", "authentication code", "otp batao", "ओटीपी बताइए",
            "ओटीपी बताओ", "ओटीपी साझा करें", "पिन बताइए", "पिन नंबर बताइए", "सीवीवी बताइए",
            "पासवर्ड बताइए", "वेरिफिकेशन कोड", "ஆதார் எண்", "ஓடிபி சொல்லுங்கள்", "ஓடிபி சொல்லவும்",
            "ஓடிபியை பகிருங்கள்", "பின் எண்ணை சொல்லுங்கள்", "பின் எண்ணை கூறுங்கள்", "சிவிவி",
            "கடவுச்சொல்", "சரிபார்ப்பு குறியீடு",
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
            "move your balance", "add beneficiary", "pay to release", "पेमेंट भेजो", "upi से भेजो", "पैसा भेजो",
            "पैसे भेजिए", "राशि ट्रांसफर", "यूपीआई से भेजिए", "भुगतान करें", "सुरक्षित खाते",
            "जुर्माना भरें", "शुल्क भेजिए", "फीस भेजिए", "பணம் அனுப்புங்கள்", "பணம் செலுத்துங்கள்", "தொகை அனுப்புங்கள்",
            "பணத்தை மாற்றுங்கள்", "யுபிஐ மூலம் அனுப்புங்கள்", "பாதுகாப்பான கணக்கு",
            "பாதுகாப்பு கணக்கு", "தொகையை மாற்றுங்கள்", "கட்டணம் செலுத்துங்கள்", "அபராதத்தை",
        ),
    ),
    TacticDefinition(
        "REMOTE_ACCESS", "CREDENTIAL_EXTRACTION", 19,
        "Caller requested remote access or screen sharing, which can expose accounts and credentials.",
        ("REMOTE_ACCESS", "BANK_IMPERSONATION"),
        (
            "install anydesk", "download anydesk", "anydesk install", "install teamviewer", "screen sharing", "share your screen", "view the screen",
            "download this application", "install this app", "remote access", "give me control",
            "ऐप इंस्टॉल", "स्क्रीन शेयर", "स्क्रीन साझा", "ऐनीडेस्क", "एनीडेस्क", "टीमव्यूअर",
            "फोन का नियंत्रण", "ஆப்ஸை நிறுவுங்கள்", "ஆப்ஸை பதிவிறக்கம்", "திரையை பகிருங்கள்",
            "திரையைப் பகிருங்கள்", "ஸ்கிரீன் ஷேர்", "எனிடெஸ்க்", "டீம்வியூவர்", "கட்டுப்பாட்டை கொடுங்கள்",
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


# Native-script requests often place the requested value before the action
# verb, with several credentials separated by punctuation. These bounded
# patterns complement the exact phrase inventory while remaining auditable.
TACTIC_REGEXES: dict[str, tuple[str, ...]] = {
    "CREDENTIAL_REQUEST": (
        r"(?:ओटीपी|पिन(?:\s+(?:नंबर|कोड))?|सीवीवी|पासवर्ड).{0,48}(?:बताइए|बताओ|बताकर|दीजिए|दें|साझा\s+करें)",
        r"(?:ஓடிபி|பின்\s+எண்|சிவிவி|கடவுச்சொல்).{0,52}(?:சொல்லுங்கள்|கூறுங்கள்|பகிருங்கள்|சொல்லவும்|கூறவும்)",
    ),
    "FINANCIAL_ACTION": (
        r"(?:भुगतान|रकम|राशि|पैसे|शुल्क|जुर्माना).{0,40}(?:भेजिए|भेजो|ट्रांसफर|जमा\s+करें|भुगतान\s+करें)",
        r"(?:பணம்|தொகை|கட்டணம்|அபராதம்).{0,44}(?:அனுப்புங்கள்|செலுத்துங்கள்|மாற்றுங்கள்)",
    ),
    "REMOTE_ACCESS": (
        r"(?:ऐनीडेस्क|एनीडेस्क|टीमव्यूअर).{0,44}(?:इंस्टॉल|डाउनलोड|स्क्रीन\s+(?:शेयर|साझा))",
        r"(?:எனிடெஸ்க்|டீம்வியூவர்).{0,48}(?:நிறுவ|பதிவிறக்கம்|திரை(?:யை|யைப்)?\s+பகிர)",
    ),
}


def detect_tactics(text: str) -> list[dict[str, Any]]:
    """Detect direct behavioral indicators, preserving explainable phrase evidence."""
    normalized = normalize_text(text)
    findings: list[dict[str, Any]] = []
    for definition in TACTICS:
        hits = []
        for phrase in definition.phrases:
            phrase_normalized = normalize_text(phrase)
            match = re.search(re.escape(phrase_normalized), normalized)
            if (
                match
                and not _safety_advice_context(normalized, match.start(), match.end())
                and not _trusted_routine_context(definition.name, normalized)
            ):
                hits.append({
                    "phrase": phrase,
                    "start_char": match.start(),
                    "end_char": match.end(),
                })
        for pattern in TACTIC_REGEXES.get(definition.name, ()):
            for match in re.finditer(pattern, normalized, flags=re.IGNORECASE):
                if (
                    _safety_advice_context(normalized, match.start(), match.end())
                    or _trusted_routine_context(definition.name, normalized)
                ):
                    continue
                if any(item["start_char"] == match.start() and item["end_char"] == match.end() for item in hits):
                    continue
                hits.append({
                    "phrase": match.group(0),
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


def _safety_advice_context(text: str, start: int, end: int) -> bool:
    """Suppress a quoted request only when it follows a narrow safety negation."""
    prefix = text[max(0, start - 56):start]
    suffix = text[end:min(len(text), end + 64)]
    return bool(SAFETY_PREFIX.search(prefix) or SAFETY_SUFFIX.search(suffix))


def _trusted_routine_context(tactic: str, text: str) -> bool:
    """Suppress a narrow, explicitly consented workplace remote-access context."""
    if tactic != "REMOTE_ACCESS":
        return False
    trusted_actor = any(marker in text for marker in ("it team", "आईटी टीम", "ஐடி குழு"))
    explicit_context = any(marker in text for marker in (
        "scheduled", "with my permission", "my permission",
        "नियोजित", "तय किया", "मेरी अनुमति",
        "திட்டமிட்ட", "என் அனுமதி", "அனுமதியுடன்",
    ))
    return trusted_actor and explicit_context


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
