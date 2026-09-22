# Limitations

1. SCAMTRACE detects potential social-engineering indicators; it cannot establish criminal intent, caller identity, or truth.
2. The bundled language model is a small curated baseline. It is useful as an independent signal but is not probability-calibrated or field-trained.
3. Tactic rules are most complete for the demonstrated Indian scam patterns and target languages. The internal adversarial suite strengthens paraphrase/noise coverage but was used in development, so novel paraphrases and underrepresented regional dialects can still be missed.
4. Voice output is an acoustic anomaly fallback, not a validated anti-spoofing classifier. It intentionally reports uncertainty on live audio.
5. Local Whisper base ASR can make recognition errors, particularly with short clips, noisy calls, mixed languages, and code-switching.
6. The evaluation dataset is intentionally small and curated. Its metrics must not be represented as deployment accuracy.
7. This prototype does not capture normal phone-call audio or auto-report incidents. Those platform and legal workflows require separate work.
8. The Threat Narrative Graph is a bounded, auditable policy layer—not a semantic truth engine. It can miss unseen playbooks, unclear speaker roles, indirect requests, regional phrasing, or ASR mistakes. Its alignment score is not a probability.
9. The graph and report are local interoperability primitives, not a live bank, RBI, I4C, 1930, or cybercrime.gov.in integration. SCAMTRACE never auto-submits a complaint or triggers a fund freeze.
10. Drift and feedback are deliberately aggregate-only and memory-only. They flag a need for reviewed data collection; they do not provide continuous learning or real-world model adaptation.
