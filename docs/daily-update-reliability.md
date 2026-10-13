# Daily publication reliability

The scheduled news producer is `auto-daily-report-cloud-fallback.yml` (`src/auto_collect`). The 06:00 JST cron is an attempt time, not a 07:00 delivery guarantee. The two legacy `script/build_news.py` workflows are retained as manual deprecation notices; they no longer compete with this producer. Manual slide authoring remains independent and the last real slide date can differ from the news date.

## Publication contract

1. Collect public-source candidates. Failure diagnostics retain public candidates only; private-vault X bookmarks are not uploaded.
2. Use a production-authorized provider. Require valid Japanese summaries, nonempty source attribution, valid external article URLs, at least three news items and two sources. A heuristic English fallback is never a successful daily publication.
3. Generate report and timeline, capture individual items under `public-pages/news/daily/YYYY-MM-DD.json`, extend search, and regenerate the homepage. Historical search records are preserved; dated legacy aggregate bulletins are not mistaken for individual articles. New managed rows can receive same-day corrections. Snapshot provenance reports exclusions and duplicates.
4. Validate dates, counts, URLs, Japanese processing and rendered text. The strict publisher stages the explicit manifest and uses a non-force fast-forward push. A competing remote push requires a fresh generation; the strict path does not rebase generated content over someone else's update.
5. A successful cloud-primary completion explicitly starts Pages through `workflow_run`. Pages verifies its artifact and actual public content after deployment. General legacy structural deployments explicitly do not certify Japanese provider quality.

## Provider prerequisite and current hold

The former implicit `meta/llama-3.3-70b-instruct` endpoint is retired. No replacement model is selected automatically. NVIDIA requires `NVIDIA_MODEL` and `NVIDIA_PRODUCTION_USE_CONFIRMED=true`, in addition to the existing key, before API calls. The latter setting is an operator assertion that an applicable production entitlement has actually been verified; setting it does not purchase or grant one.

NVIDIA's current catalog trial terms restrict trial use and generated content to internal evaluation. Do not set production confirmation merely because a free endpoint is available. No new key, subscription, billing change or terms acceptance is performed by this repair. Local Ollama remains the existing local override route. Scheduled runs diagnose missing prerequisites before collection; unavailable or unverified providers fail visibly and retain the previous public edition.

- Trial terms: https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf
- Candidate for permitted evaluation only: https://build.nvidia.com/nvidia/nemotron-3-super-120b-a12b

## Diagnosis and recovery

After collection, failure artifacts contain `logs/auto_collect/daily_quality_YYYY-MM-DD.json` and public raw candidates. Configuration failures before collection retain `logs/auto_collect/provider_preflight.json` instead. Permanent configuration, authentication, retirement and invalid-content failures are not automatically retried. Retryable network/rate-limit/service failures use bounded request retries, then the existing watchdog can reserve at most two recovery dispatches per JST day with a cooldown and overlap check. An acknowledged dispatch is still pending, not proof of publication.

Use `python scripts/check_daily_publication.py --base-url https://visionhub.jp --date YYYY-MM-DD --require-quality` for an honest live daily-health check. Omit `--require-quality` only for an explicitly labeled legacy structural inspection. Use `--root .` as well to compare live content with the checked-out expected edition. The existing safety net and Pages self-heal use these checks; no additional scheduled notification automation is introduced.

The scheduled runner uses `requirements-daily.txt`; optional model-training/search dependencies remain in the general requirements file. Offline publication regressions run on relevant pushes and pull requests without provider credentials.

## Preflight and existing local recovery

Cloud Primary now diagnoses the existing NVIDIA configuration before collection.
Missing settings are reported together and the run fails without calling that
provider or touching published data. `provider_preflight.json` is retained in the
failure artifact. No model name, entitlement assertion, API key, subscription or
persistent access is supplied by the preflight.

Read-only diagnosis (no generation, dispatch, commit or push):

```powershell
python -m src.auto_collect.provider_preflight --provider nvidia
python -m src.auto_collect.provider_preflight --provider ollama --probe
```

Without `--probe`, `configured` only means required values exist. With `--probe`,
`ready` only means the existing provider answered a short health check. Neither
result certifies Japanese article quality or a public edition.

The provisioned Windows override remains the local recovery path. Its selector
uses Ollama when a NVIDIA key is confirmed but its model is missing, rather than
choosing a permanently blocked NVIDIA route. Both routes run preflight before
collection, and the existing publisher still requires quality verification.
No Ollama model is installed, selected from a guessed name, or forwarded into a
GitHub-hosted runner. The PC must be awake and its existing daemon available.

After approval to publish, an operator can run the already provisioned
`scripts/run_daily_override.ps1` in its independent runtime checkout. That runner
collects candidates, generates Japanese summaries and invokes the strict publisher
with `--require-quality --push`; it is not a harmless diagnostic command. Inspect
`logs/run_daily_override.log` and the quality report if it stops. Do not run it in
the authoring checkout, manually change publication dates, or bypass a failed gate.
PR127's date-filtered quality-count correction is separate and must be integrated
and tested before trusting that repaired path; this patch does not merge that PR.

For cloud resumption, the operator must verify the exact production-authorized
NVIDIA model and applicable entitlement, then configure the existing variables
and credential through the normal approval process. Repeating the failed workflow
without those prerequisites does not repair it. No new cloud provider is enabled.

Schedule delay is independent: compare a run's `event`, creation time and final
result with the expected JST time. A successful `workflow_dispatch` is not evidence
that `schedule` fired. GitHub cron is best effort; these changes do not guarantee
09:15/09:35 delivery or add another automatic retry/dispatch loop.

Observed on 2026-10-13: the existing 08:00 local task selected Ollama and ran
processing, then stopped with `quality.article_count does not match daily news
items`. This is distinct from Cloud Primary's missing NVIDIA model/entitlement
configuration. The local health probe succeeded, but full publication remains
blocked until the separately reviewed PR127 correction is integrated and the
strict quality check passes. A passed health probe must not override that error.
