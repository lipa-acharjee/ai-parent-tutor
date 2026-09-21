# Security and child-privacy baseline

## Identity
- Use an established OIDC provider in production.
- Store only password hashes if local credentials are necessary.
- Use short-lived access tokens, refresh-token rotation and revocation.
- Require MFA for administrators.

## Authorization
Every request must be checked against the authenticated user's family/tenant. Never trust `family_id`, `child_id`, `chapter_id`, or `lesson_id` from the client without ownership checks.

## Files
- Restrict MIME type and file size.
- Validate file signatures, not just extensions.
- Quarantine and malware-scan uploads before parsing.
- Keep object storage private.
- Use short-lived signed URLs.
- Encrypt at rest.

## AI safety
- Treat uploaded documents as untrusted data.
- Never allow document text to override system/developer instructions.
- Separate retrieved context from instructions.
- Validate structured model output.
- Add moderation and abuse controls.
- Log model metadata, not raw child content by default.

## Privacy
- Collect the minimum child data required.
- Provide deletion/export workflows.
- Define retention periods.
- Obtain required parental consent and age/child-safety controls for each launch market.
- Execute DPAs with cloud/AI vendors where required.
- Keep production backups encrypted and subject to the same retention policy.

## Threat model to complete before launch
1. Account takeover
2. Cross-tenant data access
3. Malicious PDF/OCR payloads
4. Prompt injection in textbooks
5. AI-generated unsafe content
6. Video URL leakage
7. Queue abuse/cost attacks
8. Denial of service
9. Insider/admin misuse
10. Data deletion and backup recovery failures
