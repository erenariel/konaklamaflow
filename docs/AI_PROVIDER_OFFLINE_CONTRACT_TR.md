# AI provider showcase — offline reference contract

**Implemented in this branch:** `konaklamaflow/ai_providers.py` is an offline-only, deterministic demonstration contract. It is **not a connected OpenAI / Claude / Gemini / Azure / local model adapter**, and it does not make an AI model call.

## Public demo catalog
- OpenAI API — NOT_INTEGRATED
- Anthropic API — NOT_INTEGRATED
- Google Gemini API — NOT_INTEGRATED
- Azure OpenAI — NOT_INTEGRATED
- Self-hosted model — NOT_INTEGRATED
- KonaklamaFlow offline illustration — MOCK_DEMO

Card labels are text only, not official logos or evidence of endorsement. ChatGPT Business/Plus subscriptions do not automatically provision OpenAI API access. Real integrations require their own consent, credentials, usage budget and authorized server environment.

## Offline preview
The trusted caller provides opaque task ID, full trusted report digest, blocker codes from the Python engine and state. The function verifies types and shapes and returns message keys for the presentation layer. It cannot translate sensitive guest notes, assign rooms, check in guests, take payments, contact OTA/PMS/KBS, or send messages. All policy flags prohibit writes and calls.

This simple mock does **not authenticate the caller or independently verify the report**. Only `explainability.build_explanations` (separate Issue #5 branch) ties explanation data to a re-evaluated trusted snapshot; do not combine these contracts without an explicit source-boundary review. Hashes are integrity hints, never authentication.

## Subsequent integration, not yet built
1. Offline explanation key catalog for international UI.
2. Versioned provider port + strict schema, credential-free fixture tests.
3. Optional dedicated backend and allowlisted egress, secrets vault, budget/timeout/circuit breaker and abuse testing.
4. Authorized pilot only after legal/privacy/security approval. No real keys in browser/CI or Git.

Issue #8, #7, #19. No production claim until independent validation.
