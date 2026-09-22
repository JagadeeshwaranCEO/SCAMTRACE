# Demo Guide

## Before judges arrive

1. Run ./scripts/setup_models.py and confirm ready.
2. Start ./run.sh, then open http://127.0.0.1:8765.
3. Run ./.venv/bin/python scripts/run_demo.py in a second terminal as a quick preflight.
4. Optional proof of privacy: turn off Wi-Fi after the local model is already installed.

## Five-minute sequence

| Time | Action | Judge should observe |
| --- | --- | --- |
| 0:00–0:25 | Open SCAMTRACE and read the Privacy Status panel. | LOCAL processing, NONE cloud calls, raw audio not retained. |
| 0:25–0:55 | Click **Normal human call**. | LOW; no manipulation evidence. |
| 0:55–1:25 | Click **AI voice — safe**. | Declared synthetic demo fixture, but LOW risk because conversation is benign. |
| 1:25–2:20 | Click **Human scam — digital arrest**. | Human fixture, yet CRITICAL; timeline shows authority → threat → isolation → money and the Threat Narrative Graph identifies digital-arrest coercion. |
| 2:20–3:00 | Click **AI scam — bank / OTP**. | CRITICAL with credential and UPI evidence; Counter-Pressure Protocol says exactly how to exit and verify safely. |
| 3:00–3:35 | Click **Tamil scam**, then **Hinglish scam**. | Meaningful multilingual tactic evidence and simple intervention. |
| 3:35–4:20 | Upload a local recorded clip if available, or type a new line into the transcript box. | Live local pipeline and explanation. |
| 4:20–5:00 | Export Incident Report. State limitations clearly. | Transparent, technically defensible handoff. |

## Lines worth saying

- “A scammer does not need a fake voice to fool you. SCAMTRACE detects the attack itself.”
- “The score is evidence momentum, not a claim that someone is certainly a criminal.”
- “A synthetic voice alone cannot make the outcome critical.”
- “The system identifies the attack path, then gives a counter-pressure response—not just a red warning.”
- “Notice what would lower concern: independent verification through an official channel we find ourselves, never a number supplied by the caller.”
- “The model download happens once; inference and data handling remain local.”
