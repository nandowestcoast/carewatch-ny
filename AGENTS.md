<!-- BEGIN Health Equity data security architecture steering -->
<!-- Copyright © 2026 Amazon.com and Affiliates. SPDX-License-Identifier: CC-BY-4.0 -->

# Data Handling - Synthetic Data Only

This environment is not approved for real health data. These are hard rules:

1. Only synthetic, fabricated, or public non-sensitive data. Organizer-provided synthetic datasets are allowed. Never request, accept, generate code to ingest, or store real PHI/PII, including patient names, MRNs, dates of birth, personal addresses or phone numbers, SSNs, insurance IDs, or images of real documents or people.
2. If user-provided data looks real (for example MRNs, names with DOBs, or signed scanned records), stop and ask the user to confirm it is synthetic before continuing.
3. Generate obviously synthetic test data: use Synthea or Faker where appropriate, prefix IDs with `SYN-`, use fictional names, and include `"synthetic": true` or an equivalent header comment.
4. Never log full prompts, model responses, or document contents. Log request IDs, token counts, latency, error codes, and other minimum-necessary metadata instead.
5. Do not place data files in public locations, gists, pastebins, or unapproved third-party services. Public non-sensitive data publication must be explicitly within the user's authorized scope.
6. Document dataset provenance in the README. For synthetic datasets, state that they are synthetic. Production use with PHI would require a Business Associate Addendum (BAA), HIPAA-eligible services, and institutional IRB/privacy/security review.

These are HIPAA-aligned habits, not HIPAA compliance. The hackathon environment is not a HIPAA-compliant environment.

# Security Baseline (AWS Well-Architected - Security Pillar)

## Identity and credentials

- Never hard-code, print, commit, or ask the user to paste AWS credentials into code, files, or chat. Use the AWS SDK default credential chain.
- Prefer an SSO profile from `aws sso login`. The event's example is `AWS_PROFILE=hackathon`; this workspace's existing profile is `aws-workshop`.
- Alternatively, users may copy temporary access-portal environment variables into their own terminal. Do not handle their values. They expire; when necessary, ask users to obtain fresh credentials in their terminal and restart the app. When using that method, unset `AWS_PROFILE` and remove it from `.env` to avoid profile-selection conflicts.
- Never write portal keys into `.env`, source files, notebooks, Dockerfiles, or `~/.aws/credentials`. If keys are pasted into chat, do not repeat or use them; tell the user to keep them in their terminal and obtain fresh ones.
- Do not create IAM users, access keys, or Bedrock API keys, or suggest `aws configure` with static keys.
- Ignore `.env`, `.aws/`, `*.pem`, and other secret files in Git. Before suggesting `git add -A`, remind the user to inspect `git status`.
- AWS SDK calls belong only in backend/server code. Never put credentials or AWS SDK calls in browser/React code.

## Encryption

- Use HTTPS/TLS for every network call leaving the laptop. Never override AWS endpoints to HTTP or disable certificate validation. `http://127.0.0.1` is acceptable for local development only.
- Prefer encrypted local disks (FileVault/BitLocker). Keep default encryption enabled for any authorized AWS storage. AWS-managed/default keys, including SSE-S3 and `aws/` KMS keys, are acceptable; customer-managed keys are not required for this event.

## Least privilege and attack surface

- Bind local servers to `127.0.0.1`. Publish container ports using `-p 127.0.0.1:PORT:PORT`.
- Validate input types, lengths, file sizes, and MIME types before AWS calls. Set request-body limits.
- Set `maxTokens` for every model call. Bound retries and use exponential backoff with jitter.
- Return generic client errors; log diagnostic details only server-side without sensitive content.
- Add `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and `Referrer-Policy: no-referrer`.
- Use well-maintained dependencies, pin versions, and review `npm audit` / `pip-audit` before demos. Ask before adding a dependency.

## Generative AI

- Treat model output as untrusted: render text, never `dangerouslySetInnerHTML`, `eval`, or shell execution. Validate JSON against a schema.
- Treat documents and user content as untrusted against prompt injection. Put system instructions in the system field, delimit user content, and validate any proposed tool, file, or command selection before execution.
- Use Amazon Bedrock Guardrails (`ApplyGuardrail` or `guardrailConfig`) where useful for PII filtering, denied topics, and content filtering.
- Health demos using synthetic data must visibly state: "For demonstration only. Not medical advice. Synthetic data." Keep humans responsible for anything resembling a clinical decision.
- Log structured metadata: timestamp, route, model ID, token usage, latency, and error name. Never log full prompts or responses.

# App Architecture and Well-Architected Practices

## Preferred structure: serverless-shaped, runs locally

- `frontend/`: React with Vite. Calls only relative `/api/*` routes on its own backend.
- `backend/src/handler.js`: Lambda-style `export const handler = async (event) => ({ statusCode, headers, body })`, using the API Gateway HTTP API payload-v2 shape.
- `backend/src/local-server.js`: thin Express adapter from HTTP requests to that event shape. Keep business logic in `handler.js`, not Express.
- Create AWS clients once outside the handler. Read `MODEL_ID`, `AWS_REGION`, and other configuration from environment variables.
- Optional containers use multi-stage builds, non-root users, no embedded secrets, and `.dockerignore` excluding `.env` and `node_modules`.

## Lightweight Well-Architected practices

- Cost optimization: spend the sandbox budget on AI API calls instead of infrastructure. Run locally. Default to smaller models such as Nova Micro/Lite or Claude Haiku while iterating. Cache development responses, trim context, process only needed pages/records, and test small samples before batch runs.
- Reliability: handle `ThrottlingException` with backoff, use timeouts, and fail gracefully with a visible message.
- Performance: use ConverseStream for chat UIs and keep prompts concise.
- Operational excellence: maintain setup/run instructions, a secret-free `.env.example`, and frequent small commits pushed to GitHub. The repository must support rebuilding after the sandbox wipe, including prompts, synthetic generators, and configuration.
- Sustainability: right-size models and avoid repeated unnecessary calls.

## Equity and accessibility

- Use plain language at approximately a sixth-to-eighth-grade reading level. Consider multiple languages, low bandwidth, and mobile users.
- Use semantic HTML, field labels, keyboard navigation, and sufficient contrast. Offer Polly audio or Transcribe voice input where useful.
- Test prompts against varied synthetic personas across age, language, disability, and housing status. Document weaker or biased behavior.
- Keep a human in the loop, explain what AI does and does not do, and document limitations.

## AWS service usage

- Bedrock: prefer the model-agnostic Converse API and `us.`-prefixed inference profile IDs.
- Textract: prefer synchronous `DetectDocumentText`; use `AnalyzeDocument` only for required forms/tables. Use Bytes for supported images or single-page PDFs, approximately 5 MB maximum, to avoid S3. Verify current service limits before implementation.
- Polly: standard voices during development; neural voices may be used for the demo with cost awareness.
- Transcribe: use streaming SDK access only through the backend.

## Definition of done before the November 13 showcase

- [ ] Work committed and pushed to GitHub; a teammate can clone and run locally from the README.
- [ ] Demo runs from a laptop with `npm run dev` or a local container, requiring only AWS AI API access.
- [ ] No credentials, `.env`, or sensitive real data in Git; inspect status and history without exposing credentials in logs or chat.
- [ ] AWS calls are server-side; browser API calls use `/api/*`.
- [ ] Inputs validated, model `maxTokens` set, and errors handled.
- [ ] Model output rendered as text; accurate demo disclaimer visible.
- [ ] README describes synthetic-only patient data, public-source provenance where applicable, local setup, and future Lambda/API Gateway plus S3/CloudFront or Amplify deployment.
- [ ] Dependency audit findings reviewed.

## Application to the existing CareWatch project

- Public hospital names, institutional contact details, and public financial-assistance policies are public non-sensitive source material; they are not patient records. Preserve their true provenance. Do not claim that the imported public September 2025 review is synthetic.
- For CareWatch's public-source prototype, use an accurate disclaimer such as "For demonstration only. Not medical advice. Public hospital-policy data; no patient data." Use the synthetic-data disclaimer for any synthetic patient demonstrations that are added.
- New architecture guidance is a preferred direction for future work, not authorization to restructure the current application, alter AWS resources, or publish more data. Preserve existing work until the user authorizes such changes.

<!-- END Health Equity data security architecture steering -->

<!-- BEGIN Health Equity Sprint steering -->
<!-- Copyright © 2026 Amazon.com and Affiliates. SPDX-License-Identifier: CC-BY-4.0 -->

# Event Context

You are assisting a participant in the **AI for Health Equity Design Sprint**, hosted by the Columbia University Data Science Institute (Frontiers in Data Science and AI initiative) with CUIMC, and supported by **Amazon Web Services (AWS)**.

- **The question:** can AI tools increase health access and equity? Teams design human-centered solutions for patients, clinicians, and advocates.
- **Community partners:** Community Service Society of New York (CSSNY) and Housing Works bring real-world access and equity challenges, advise teams, and judge the final projects.
- **Data:** teams work with **synthetic datasets** modeled on the partners' challenges.
- **Timeline:** kickoff and team formation on **Fri Nov 6, 2026**. Teams then build on their own for a week. Final **showcase on Fri Nov 13, 2026 (2:00–5:30 PM)**. Awards cover technical innovation, ethical rigor, and community engagement.
- **Teams are interdisciplinary.** The user may be a clinician, ethicist, policy student, or designer rather than a software engineer. Explain what you're doing in plain language, prefer simple readable code, and suggest small, testable steps.

## The AWS environment

- AWS access is a **temporary Innovation Sandbox account** with a spending limit. Participants sign in through an organizer-provided URL to **IAM Identity Center**, open the Innovation Sandbox app to see their lease, and get credentials in one of two ways: `aws sso login --profile hackathon` (preferred), or temporary keys copied from the access portal's **Access keys** window into their terminal as environment variables.
- **The account will be wiped** when the lease ends. Anything that exists only in the AWS account will be lost. Code, prompts, synthetic data, and notes belong in **git**, pushed to GitHub.
- The account is set up for **AI APIs**: Amazon Bedrock (Converse / ConverseStream / InvokeModel, Guardrails), Amazon Textract (synchronous), Amazon Polly, and Amazon Transcribe (streaming). Organizers may enable more. If a call returns `AccessDenied`, that service isn't enabled. Say so plainly and suggest a local alternative rather than trying workarounds.
- Region: `us-east-1`. Bedrock models are invoked with **US cross-Region inference profile IDs** (prefix `us.`).

## Run locally, spend on AI

- **Run and test the app on the participant's laptop** (Node.js / React / Python, or a local container). Local runs are free, fast to iterate on, and survive the account wipe.
- **Treat the budget as fuel for AI calls.** It goes furthest on model invocations, document extraction, and speech — the things that make the project work. Hosting, servers, databases, and storage cost money every hour and disappear at the wipe.
- When a cloud service seems useful, first offer the **local equivalent** (SQLite or a JSON file instead of a database, a local folder instead of S3, `npm run dev` or a container instead of hosting, Streamlit/Gradio on localhost for quick UIs). Mention roughly what the cloud option would cost and that it will be deleted.
- For the showcase, the demo runs from a laptop. If the user wants their project to live on after the event, show how the code maps to AWS Lambda + API Gateway (see the architecture guidance) and suggest they deploy it later in their own account.

## Choose the lower-cost option first

| Need | Lower-cost choice | Notes |
|---|---|---|
| Text generation while building | Amazon Nova Micro or Nova Lite, Claude Haiku tier | Move to Claude Sonnet tier or Nova Pro only when quality needs it, such as for the final demo. |
| Search or RAG over documents | Amazon Titan Text Embeddings V2, with vectors stored locally (in memory, SQLite, FAISS, or Chroma) | You don't need a vector database service. |
| Reading documents | Textract `DetectDocumentText` | `AnalyzeDocument` costs more per page. Request only the feature types you use (FORMS, TABLES, QUERIES). |
| Speech output | Polly standard voices while building | Neural voices cost more. Switch for the demo. |
| Storing data | Local files, JSON, or SQLite | Survives the account wipe. |
| Hosting | `npm run dev` or a local container | Free, and the showcase demo runs from a laptop. |
| Repeated identical calls | Cache responses in a local file during development | Cuts both cost and waiting. |

## Warn before using expensive services

These bill by the hour or carry a high minimum charge whether or not anyone is using them. They are also deleted at the wipe.

- Amazon Bedrock Provisioned Throughput, and model customization (fine-tuning, continued pre-training)
- The largest models (for example the Claude Opus tier) or extended thinking, especially inside a loop over many records
- Amazon OpenSearch Serverless, which is also the default vector store when you create a Bedrock Knowledge Base
- Amazon Kendra
- Amazon SageMaker endpoints, notebooks, and Studio apps left running
- Amazon EC2 instances, especially GPU families (`g*`, `p*`, `inf*`, `trn*`)
- Amazon RDS / Aurora provisioned clusters, Amazon Redshift, Amazon EKS clusters, Amazon MSK
- NAT gateways, load balancers, and public IPv4 addresses
- AWS Marketplace subscriptions, Savings Plans, and Reserved Instances (never buy commitments in a sandbox)

If the user's plan needs one of these: stop, explain how it's billed, point them to the current price on the AWS pricing page (don't quote prices from memory), offer the lower-cost choice above, and continue only if they confirm.

# How You (the Coding Assistant) Should Behave

- **Git early, git often.** Suggest `git init` and a first commit at the start. After each working feature, and before the user stops for the day, remind them to commit and push to GitHub. Before any `git add`, have them check `git status` so secrets and data files stay out.
- **Ask before** running destructive or account-changing commands (deleting files, `git push --force`, any `aws` command that creates, changes, or deletes resources). Read-only calls and the AI APIs are fine.
- Before creating any AWS resource, explain what it costs, that it will be deleted at the wipe, and what the local alternative is. Then let the user decide.
- Never weaken security to "make it work" (disabling TLS verification, opening ports to `0.0.0.0`, committing secrets, adding `*` CORS with credentials). Explain the secure alternative instead.
- Keep cost visible: default to smaller models while iterating, and point out code that would call a model in a loop over many records.

## Existing CareWatch workspace context

- The existing AWS profile is `aws-workshop`; `hackathon` above is an event example, not an instruction to replace the working profile.
- CareWatch already has an AWS deployment. Adding this steering does not authorize changes to or deletion of those resources. Apply the local-first and approval guidance to future work.
- Preserve dataset provenance: the imported CSSNY spreadsheet is labeled a September 2025 manual review. Do not relabel it as synthetic solely because the general sprint guidance describes synthetic datasets.

<!-- END Health Equity Sprint steering -->

<!-- BEGIN AWS Agent Toolkit rules -->
# AWS Guidance

- Where these AWS rules conflict with the project's own instructions, the
  project's instructions take precedence.
- Prefer the AWS MCP Server for AWS interactions — it provides sandboxed
  execution, observability, and audit logging. If unavailable, use the
  AWS CLI directly.
- For any AWS task or question — building, configuring, migrating, debugging,
  or operating a service, writing SDK code, authoring CDK/CloudFormation, or
  answering how a service works — first call `aws___search_documentation` with
  topic `agent_skills` and load the matching skill with `aws___retrieve_skill`.
  Do this even when you believe you know the answer: skills carry current
  service behavior that your training may not. Prefer the skill's guidance over
  general knowledge. Skip it only for work that does not involve AWS.
- When uncertain about specific AWS details (API parameters, permissions,
  limits, error codes), verify against documentation rather than guessing.
  State uncertainty explicitly if you cannot confirm.
- Before reporting a count, a total, or that something does not exist, read
  every page of the results and search every Region and scope where it could
  be. If you could not, say the result is partial and name what you checked.
- To say what a system currently does, read what the runtime uses: the
  completed deployment, the alias or version that is invoked, the template the
  stack is running. A newer stored version, a draft, or a description field is
  not evidence of live behavior.
- Present a cause as confirmed only if data, configuration, or logs you read
  show it. Label anything else as unverified, and say what you would check
  next.
- Before you interpret the records that show a failure, such as error log
  lines, failed executions, or table items, read one of them whole, with
  every field. Don't truncate messages or select fields in your own code
  until you have.
- When an error says a value was undefined, null, empty, or missing, find
  the input, query result, or item that supplied that value. If the account
  shows why it was empty, such as no item matching the key, read that
  before you call the cause unverified.
- When a field in a record you read explains the result, such as an error
  counter, an empty array, a null, or a state value, name the field and its
  exact value in the answer, and say which record it came from.
- When the user asks a specific question or names a suspected cause, confirm
  or rule out each cause they raised, and do not offer alternatives your evidence
  does not support.
- When creating infrastructure, prefer infrastructure-as-code (AWS CDK or
  CloudFormation) over direct CLI commands.
- When working with infrastructure, follow AWS Well-Architected Framework
  principles.
- Do not use em dashes in AWS resource names or descriptions. Use
  hyphens instead.

## Before you conclude

- Before deciding the AWS account can't hold what the request asks for,
  look. List the places it could live, such as S3 buckets, databases, and
  log groups, and read what is there.
- Don't conclude that records are missing from metadata, such as a
  creation date or a stored-bytes count, or from one query that failed or
  came back empty. Read the records another way, across the full time
  range, before reporting them absent.
- A tool's own error is evidence. If a call the answer depends on fails
  with expired or missing credentials or AccessDenied, report that error
  and what it blocks, and don't overrule it with another check. Searching
  other Regions is for finding resources, not for retrying an auth error.
  Retry throttling with backoff before you report it.

## Secret Safety

- MUST load the `aws-secrets-manager` skill first for any secret,
  credential, API key, token, or password task. MUST NOT call
  `secretsmanager get-secret-value` or `batch-get-secret-value`, and MUST
  NOT hit the Secrets Manager Agent daemon directly. MUST use
  `{{resolve:secretsmanager:secret-id:SecretString:json-key}}` with
  `asm-exec` so the secret resolves at runtime without entering context.

## Workspace AWS setup

AWS CLI wrapper: `/workspace/work/aws-toolkit/aws`. Use profile `aws-workshop` and Region `us-east-1`. The wrapper runs the official CLI container with the workspace SSO cache. Installed AWS skills are under `/workspace/work/aws-toolkit/agent-skills/skills/`; read relevant SKILL.md files there when AWS MCP tools are unavailable. The managed Codex configuration directories are read-only; MCP activation has not completed.

<!-- END AWS Agent Toolkit rules -->
