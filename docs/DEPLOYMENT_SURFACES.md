# Deployment surfaces and integration posture

SCAMTRACE is a local conversational decision layer. Its present product
boundary is a typed transcript, an approved local-ASR client, an uploaded
recording, or browser microphone capture. It is **not** a covert capture tool.

## Strategic priority

Generic dialer scam alerts are becoming an operating-system capability. Our
defensible position is the reviewable intervention layer and regional-language
coverage, not a claim to replace an OS dialer. Government reporting has also
identified Skype IDs and WhatsApp accounts used for digital-arrest fraud, so a
future integration needs to prioritise legitimate, consented video-call and
app-call surfaces as well as ordinary telephony.

| Surface | Current prototype | Production research direction | Boundary |
| --- | --- | --- | --- |
| Typed transcript | Working | Accessibility and recovery flow | User supplies text. |
| Local ASR client | Working REST contract | Android / desktop client | Audio remains on-device. |
| Browser microphone | Working where permission is granted | Accessibility fallback | Browser permission, visible recording only. |
| Telecom dialer | Not implemented | Evaluate only if platform policy and user consent permit | Do not compete on privileged interception. |
| WhatsApp / Skype / video calls | Not implemented | Consent-led capture or app-provided transcript only | No bypass of app, OS, encryption, or recording protections. |

## Why no silent capture

Silently collecting conversation audio would overturn SCAMTRACE's privacy
claim, create legal risk, and make the tool dangerous in abusive situations.
Any native client must make the active source visible, obtain an explicit
permission, retain audio only ephemerally, and allow an immediate stop.

## Official response handoff

When a user says money, credentials, or device control may already have been
lost, SCAMTRACE produces a local, redacted case summary and points to the
India cybercrime helpline **1930** and
[cybercrime.gov.in](https://cybercrime.gov.in). It never files the case,
contacts a bank, or initiates payment recovery. The user reviews and chooses
what to submit.
