# Bounded AI evaluation plan

Live Bedrock/Textract evaluation requires a valid AWS SSO session and enabled APIs. Until then, only validation tests have passed; no model accuracy score is claimed.

Start with five public policy documents, including an image-only page, an older policy, a multilingual document, and a document with missing eligibility information. Have a human mark exact expected quotes, page numbers, and unknown fields. Run one small-model request per source and reuse the cache for identical inputs. Default: US Nova Lite inference profile, 1,200 output tokens, no tool use. Respect prompt/response limits, retry at most twice with jitter, and use an existing Guardrail when available.

Measure exact citation support, correct abstention on missing facts, policy-version confusion, and reviewer time. Unsupported quotes are rejected by the server before display. A schema-passing result is not proof of factual completeness or legal correctness.

Use obviously synthetic, nonclinical advocate personas: SYN-English-mobile, SYN-Spanish-low-bandwidth, SYN-Keyboard-screen-reader, and SYN-Large-text. Do not generate patient eligibility cases or add PHI. Ask each persona to find a source, recognize a historical grade, identify a failed fetch, and export a review decision. Record misunderstandings and language/accessibility gaps. Only the safety notice is translated so far; the full application remains English.
