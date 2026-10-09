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

NVIDIA's current catalog trial terms restrict trial use and generated content to internal evaluation. Do not set production confirmation merely because a free endpoint is available. No new key, subscription, billing change or terms acceptance is performed by this repair. Local Ollama remains the existing local override route. Until an appropriate production route is available, scheduled collection and health checks continue, publication fails visibly, and the previous public edition is retained.

- Trial terms: https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf
- Candidate for permitted evaluation only: https://build.nvidia.com/nvidia/nemotron-3-super-120b-a12b

## Diagnosis and recovery

Failure artifacts contain `logs/auto_collect/daily_quality_YYYY-MM-DD.json` and public raw candidates. Permanent configuration, authentication, retirement and invalid-content failures are not automatically retried. Retryable network/rate-limit/service failures use bounded request retries, then the existing watchdog can reserve at most two recovery dispatches per JST day with a cooldown and overlap check. An acknowledged dispatch is still pending, not proof of publication.

Use `python scripts/check_daily_publication.py --base-url https://visionhub.jp --date YYYY-MM-DD --require-quality` for an honest live daily-health check. Omit `--require-quality` only for an explicitly labeled legacy structural inspection. Use `--root .` as well to compare live content with the checked-out expected edition. The existing safety net and Pages self-heal use these checks; no additional scheduled notification automation is introduced.

The scheduled runner uses `requirements-daily.txt`; optional model-training/search dependencies remain in the general requirements file. Offline publication regressions run on relevant pushes and pull requests without provider credentials.
