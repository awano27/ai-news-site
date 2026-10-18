# TOP quality improvement
Base: origin/main 283dc619; isolated worktree. Original dirty checkout remains untouched.

## Scope
- Put latest slide title, date, summary and reading link in first screen; preserve generated IDs and unique personal tools entry.
- Consolidate major news to one editorial selection (up to three), with source dates, evidence attribution, interpretation and limits. No invented outcomes.
- Preserve archives and tools. Keep existing portfolio evidence and roles.
- Match calm existing navy/yellow styling; consistent spacing, readable typography, responsive keyboard-accessible layout.

## Dependencies and ownership
Root: index.html, assets/home-editorial.css, editorial data, visual checks, final integration.
Bounded delegated audit: generator/update map and regression risks (read-only initially).
Generator changes depend on verified source data; visual work is independent.

## Risks
Existing latest/LATEST and exclusion fixes must survive generation and browser fetches. Keep their IDs and regression tests. Curated picks must expire by report date; no old picks relabeled new. Keep full historical data. No commit/push/deploy.

## Acceptance
First screen communicates purpose/latest theme/personal tools entry. One major news section. Source and interpretation labels and actual dates. Before/after PC and 390px captures; overflow, keyboard/menu and links checked. Focused generator tests plus fixture freshness and exclusion tests. Record unverified live automation, real-device and usability evidence separately.
