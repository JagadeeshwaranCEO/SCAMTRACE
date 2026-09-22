#!/usr/bin/env python3
"""Generate reproducible, authored contrast data for STDM-1 development.

This is deliberately labelled synthetic model-development data. It is useful
for exercising state decisions and hard negatives, not for claiming field
accuracy. Human-reviewed recordings must remain separate for any benchmark.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "data" / "processed" / "stdm_synthetic_contrasts.jsonl"

TEMPLATES = {
    "NORMAL": [
        ("safety_advice", "en", "Never share an OTP, PIN, or password with anyone. Use the official {bank} app if you need help."),
        ("payment_receipt", "en", "Your payment of ₹{amount} was received through the official college portal. No action is required."),
        ("police_awareness", "en", "Police have warned residents about digital-arrest scams. End the call and verify independently if anyone threatens arrest."),
        ("tamil_safety", "ta", "அறிமுகமில்லாத அழைப்பாளரிடம் ஓடிபி சொல்லாதீர்கள். வங்கியின் அதிகாரப்பூர்வ எண்ணை நீங்களே அழையுங்கள்."),
        ("hindi_safety", "hi", "किसी अनजान कॉलर को ओटीपी या पिन न बताएं। जानकारी के लिए बैंक की आधिकारिक वेबसाइट देखें।"),
        ("hinglish_safety", "hinglish", "Kisi unknown caller ko OTP mat batao. Help chahiye toh official bank app kholo."),
    ],
    "SUSPICIOUS": [
        ("routine_bank", "en", "This is a routine reminder from {bank}. Please visit the branch or use the official app at a convenient time."),
        ("courier_notice", "en", "Your courier may arrive tomorrow. Track it only through the order page you already use."),
        ("support_boundary", "en", "A support agent says a device check is available, but asks you to contact support through the official website."),
        ("tamil_routine", "ta", "வங்கியின் வழக்கமான நினைவூட்டல் இது. உங்களுக்கு வசதியான நேரத்தில் அதிகாரப்பூர்வ செயலியில் பார்க்கலாம்."),
        ("hindi_routine", "hi", "यह एक सामान्य सेवा सूचना है। अपनी सुविधा के अनुसार आधिकारिक ऐप में विवरण देख लें।"),
        ("hinglish_routine", "hinglish", "Yeh routine service reminder hai. Details official app mein apne time par check kar lena."),
    ],
    "IMPERSONATION": [
        ("bank_identity", "en", "I am calling from the {bank} security department about your account."),
        ("authority_identity", "en", "This is an officer from the cybercrime department speaking about a complaint."),
        ("customs_identity", "en", "I am a customs officer calling about a parcel under your name."),
        ("tamil_identity", "ta", "நான் சைபர் கிரைம் காவல் துறையிலிருந்து பேசுகிறேன். உங்கள் பெயரில் ஒரு புகார் உள்ளது."),
        ("hindi_identity", "hi", "मैं साइबर क्राइम विभाग से बोल रहा हूं। आपके नाम पर एक शिकायत है।"),
        ("hinglish_identity", "hinglish", "Main bank fraud team se bol raha hoon. Aapke account ke baare mein baat karni hai."),
    ],
    "MANIPULATION": [
        ("legal_pressure", "en", "Your account is linked to a criminal case. Do not disconnect; this is urgent and confidential."),
        ("service_pressure", "en", "Your SIM will be blocked today. Stay on the call and do not discuss this with anyone."),
        ("parcel_pressure", "en", "Prohibited documents were found in your parcel. Resolve this immediately or legal action will follow."),
        ("tamil_pressure", "ta", "உங்கள் கணக்கில் வழக்கு பதிவு செய்யப்பட்டுள்ளது. அழைப்பை துண்டிக்காதீர்கள், யாரிடமும் சொல்லாதீர்கள்."),
        ("hindi_pressure", "hi", "आपके खाते पर कानूनी कार्रवाई होगी। कॉल मत काटना और किसी को मत बताना।"),
        ("hinglish_pressure", "hinglish", "Aapka account block hoga. Call mat kaatna aur kisi ko mat batana."),
    ],
    "CREDENTIAL_EXTRACTION": [
        ("otp_demand", "en", "Tell me the OTP you just received so I can verify your {bank} account."),
        ("pin_demand", "en", "Share your PIN and CVV immediately to prevent your card from being blocked."),
        ("kyc_demand", "en", "Complete KYC now by giving your Aadhaar number and password."),
        ("tamil_otp", "ta", "உங்கள் ஓடிபியை உடனே சொல்லுங்கள், இல்லையெனில் கணக்கு முடக்கப்படும்."),
        ("hindi_otp", "hi", "अभी ओटीपी और पिन बताइए, नहीं तो आपका खाता ब्लॉक हो जाएगा।"),
        ("hinglish_otp", "hinglish", "Abhi OTP batao aur PIN share karo, warna account block hoga."),
    ],
    "FINANCIAL_EXTRACTION": [
        ("safe_account", "en", "Transfer ₹{amount} to the safe account immediately for verification."),
        ("upi_charge", "en", "Pay the ₹{amount} processing charge through UPI now to avoid legal action."),
        ("qr_payment", "en", "Scan this QR code and send ₹{amount} to release the parcel today."),
        ("tamil_payment", "ta", "உடனே பாதுகாப்பான கணக்குக்கு ₹{amount} பணம் அனுப்புங்கள்."),
        ("hindi_payment", "hi", "तुरंत यूपीआई से ₹{amount} ट्रांसफर करो, नहीं तो कार्रवाई होगी।"),
        ("hinglish_payment", "hinglish", "Abhi UPI se ₹{amount} safe account mein transfer karo."),
    ],
}

BANKS = ("SBI", "HDFC Bank", "ICICI Bank", "Axis Bank")
AMOUNTS = ("500", "2,000", "10,000", "25,000")


def main() -> None:
    rows = []
    for state, templates in TEMPLATES.items():
        for family, language, template in templates:
            for variant, (bank, amount) in enumerate(zip(BANKS, AMOUNTS), start=1):
                rows.append({
                    "id": f"{state.lower()}-{family}-{variant}",
                    "state": state,
                    "text": template.format(bank=bank, amount=amount),
                    "language": language,
                    "family": f"{state}:{family}",
                    "provenance": "synthetic_hard_negative_or_attack_template_v1",
                    "review_status": "authored model-development template; not independent benchmark data",
                })
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} synthetic, authored STDM contrast rows to {TARGET}")


if __name__ == "__main__":
    main()
