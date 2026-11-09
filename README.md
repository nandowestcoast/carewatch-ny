# CareWatch NY v2

Independent AI for Health Equity Design Sprint prototype based on the CSSNY hospital financial-assistance challenge. Public hospital-policy data; no patient data. For demonstration only. Not medical advice, legal advice, or compliance certification.

The existing public site is https://dwt8kng927tzh.cloudfront.net/. A local release is not live until the release manifest says it has been deployed and verified.

## Run on a laptop

Use Node.js 20.19+ or 22.12+:

```sh
npm ci
npm run dev
```

Open http://127.0.0.1:5173. The React app and Lambda-shaped Node backend bind only to loopback. No cloud account is needed for the bundled dashboard, reviews, exports, or rubric draft. The thin local HTTP adapter uses Node's standard library rather than adding an Express dependency. Existing frontend files remain in src/ to avoid a disruptive move.

The browser calls only relative `/api/*` routes. Locally these reach backend/src/handler.js (API Gateway HTTP API payload-v2 shape). On the public static release, read-only API paths serve versioned public JSON; AI and shared writes are disabled. No AWS SDK, credentials, or secrets belong in frontend code.

## Data and findings

The 212 hospital records and letter grades are from the supplied CSSNY September 2025 manual review, not synthetic patient data. All historical grades remain unchanged. The source directory listed 218 facilities at original import; scope reconciliation is not complete. Map locations use 211 GeoNames ZIP-code centroids, not precise hospital coordinates or primary service areas. Service-area counties remain N/A when not recorded.

Monitoring health separates attempted source pages, successful retrievals, fetch errors, sources needing attention, and stale/unchecked evidence (26-hour threshold). Source pages and hospital records use different denominators. Changes do not establish legal noncompliance.

Evidence decisions record hospital/check, exact source quotation, URL/page, source hash, evidence timestamp, reviewer alias, decision, reasoning, and review date. They never update published grades. Review JSON can be exported/imported with strict validation. Browser data stays on the device; the local backend also stores a file under .local/reviews.json. These are portable evidence decisions, not a cloud multi-user approval system.

The Methodology page exports a rubric draft. Current grading is blocked until CSSNY or a qualified legal reviewer approves citations, effective dates, applicability, weights, thresholds, and automatic-fail rules. See docs/partner-review.md.

## Public-source monitoring

Cloud: four source pages per hour, up to two relevant same-host PDFs each. Local: install the existing Python dependency and run a small batch:

```sh
uv pip install --target monitor/package -r monitor/requirements.txt
PYTHONPATH=monitor/package npm run scan -- --limit 4
```

Use --refresh-live to import the public live monitoring results before a local scan. No AWS resources are required. Cache, source snapshots, raw extracted pages, and cursors stay in ignored .local/. External document hosts require an operator-reviewed local allowlist in .local/approved-hosts.json. Never add a host to evade an access restriction.

The monitor enforces HTTPS, public resolved IPs, explicit host validation, robots rules, PDF magic bytes, document/response limits, and bounded requests. Relevant financial-assistance PDFs are prioritized. Discovered but unfetched documents have explicit reasons. A failed fetch preserves the last successful evidence; newly observed changes preserve before/after passages. This cannot reconstruct evidence lost by an older monitor. Full page/document contents are never logged.

Reviewed source URL changes are in monitor/source-registry.json, with the original redirect recorded as verification. They affect future retrievals, not the historical baseline. Blocked websites, unresolved redirects, and absent documents remain manual-review work.

## Optional AI / OCR

AI is off by default. Configure the AWS CLI with SSO in your own terminal. Never put portal keys in files or chat. Export non-secret configuration in the terminal and restart the local app:

```sh
export AWS_PROFILE=aws-workshop
export AWS_REGION=us-east-1
export AI_ENABLED=true
export MODEL_ID=us.amazon.nova-lite-v1:0
npm run dev
```

Use an inference profile enabled by the organizer. The AI lab sends one public source at a time through backend-only Bedrock Converse calls. It uses up to 12 bounded passages from a matching local source snapshot when available, or from the stored candidate passages otherwise. Therefore the model does not necessarily see an entire document. Output is capped at 1,200 tokens, retries are bounded, and identical results are cached locally. No autonomous tools, grading, or eligibility decisions. Strict schema validation rejects any quotation that is not an exact substring of its cited passage. Unknown fields have no fabricated citation. Optional existing Guardrail IDs can be configured via environment variables. AccessDenied is reported; the app does not attempt permission workarounds.

For public single-page PDFs/PNG/JPEG under 5 MB:

```sh
node scripts/ocr.mjs public-document.pdf --public-document
```

This uses Textract DetectDocumentText and saves OCR output locally without logging contents. The flag is an explicit operator confirmation of public non-sensitive data. Never use patient documents. Live AI/OCR evaluation requires valid SSO/API access; see docs/ai-evaluation.md. Schema tests do not establish model accuracy.

## Testing and demo

```sh
npm test
PYTHONPATH=monitor:monitor/package python -m unittest discover -s tests -p 'test_*.py'
npm run build
npm audit
```

Browser integration checks use Playwright Python and Chromium at /usr/bin/chromium, with npm run dev active: `python tests/v2_browser.py`. See docs/showcase.md for a laptop demonstration. Dependency versions are pinned and package-lock.json is committed. Avoid adding dependencies without approval.

## Backup

Verified project repository: https://github.com/nandowestcoast/https-github.com-nandowestcoast-carewatch-ny

After checking `git status`, commit changes and push to the agreed GitHub repository. `npm run backup` creates a source ZIP and a Git history bundle from committed, tracked files. Ignored .local/ data, credentials, dependencies, generated downloads, and secrets are excluded. Export your review records separately. A teammate can clone the history bundle with `git clone carewatch-history.bundle carewatch-ny`.

The temporary AWS sandbox will be wiped at lease end. GitHub publication requires a valid connection and agreed repository; a local Git commit alone is not a remote backup.

## Existing AWS deployment and release process

Hosting stack: carewatch-ny (private encrypted/versioned S3 plus CloudFront OAC). Monitor stack: carewatch-ny-scans (scheduled Lambda, DynamoDB lease, encrypted SQS failure queue, logs, alarm). Region us-east-1. Stateful resources have Retain policies. Snapshot retention is 90 days; logs 14 days. Costs are usage-based; no new hosting service is needed for v2. The free local equivalent is npm run dev plus the bounded Python scanner.

Infrastructure is in infra/hosting.json and infra/monitoring.json. The v2 hosting template adds a noncached read-only api/* path and no-referrer headers; it creates no extra service. The monitor's scoped IAM policy adds only its site/api/monitor write path. Build output includes public read-only API objects. The Lambda ZIP must include handler.py, scanner.py, state.py, source-registry.json, and pypdf. Deploy under a new immutable artifact key through the existing stack's CodeKey parameter.

On first deployment only, initialize private/state.json and site/data/monitor.json. Do not overwrite live scan state during updates. Exclude BOTH data/monitor.json and api/monitor when uploading an updated frontend. After the monitor update, a bounded scan writes both monitoring paths. Verify stack status, deployed assets, headers, API data, and scanner output before claiming a release is live.

Any AWS resource change requires the user's authorization. Deployment may need renewed SSO. Prior access failures must not be treated as proof that deployment succeeded. The old carewatch-ny-monitor rollback stack remains untouched.

## Data handling and attribution

Public hospital names, institutional contacts, and published policies are non-sensitive source material. Synthetic patient demonstrations, if ever added, must be clearly labeled synthetic with SYN- IDs. No real PHI/PII ingestion. Production PHI would require a BAA, HIPAA-eligible services, and institutional IRB/privacy/security review. These habits do not make this event environment HIPAA-compliant.

CSSNY review: https://docs.google.com/spreadsheets/d/17S2EheUVVr1g911fPpBQJqRpy18pkUlaEEnvGM0LB1o/edit

NYS directory: https://profiles.health.ny.gov/directory/hospitals

Legal reference: https://newyork.public.law/laws/n.y._public_health_law_section_2807-k

GeoNames ZIP locations (CC BY 4.0): https://download.geonames.org/export/zip/

State outline: https://github.com/PublicaMundi/MappingAPI/blob/master/data/geojson/us-states.json
