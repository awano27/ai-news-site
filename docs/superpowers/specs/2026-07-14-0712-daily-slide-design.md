# 2026-07-12 Daily Slide Design

## Objective

Create a complete 2026-07-12 daily slide deck from the supplied narrative and visual sources while matching the established 2026-07-11 presentation family.

The deck must explain the shift from prompt engineering to loop engineering for developers, engineering leaders, and AI-adoption decision makers. It should translate the long-form article into a concise, visual, decision-oriented story.

## Source mapping

- Primary narrative: `input/day/0712slide.txt`
- Overview visual and topic inventory: `input/day/0712.png`
- Detailed visual reference: `input/day/0712.pdf`
- Visual system and structural reference: `workspace/0711-image2-brand-slides/`
- Published viewer reference: `presentations/day_slides/day_slide_2026_07_11.html`

`input/day/0712.txt` is daily-news material and is not a slide-content source. No 2026-07-12 source PPTX exists, so the deck will be built from the text, PNG, and PDF rather than treating the 2026-07-11 PPTX as editable 2026-07-12 content.

## Visual direction

Reuse the 2026-07-11 “Agent Signal Room” design language:

- 16:9 canvas at 1672 x 941 pixels.
- Graphite and teal-black backgrounds.
- Warm-white primary text and cool-gray secondary text.
- Electric cyan for verified flow and signal paths.
- Signal orange for outcomes, decisions, and warnings.
- Wide margins, strong negative space, and one dominant visual per slide.
- Thin Japanese sans-serif typography with short, conclusion-first titles.
- No visible page numbers, logos, NotebookLM marks, or invented branding.

The supplied 2026-07-12 PNG and PDF are content references. Their light-background infographic styling and NotebookLM watermark will not be copied into the final deck.

## Narrative structure

The deck will contain 14 slides:

| No. | Working title | Purpose |
|---:|---|---|
| 1 | 開発者は「コードを書く人」から「ループを設計する人」へ | Establish the paradigm shift. |
| 2 | 本日の流れ | Preview the five-part narrative. |
| 3 | 30秒でわかるループエンジニアリング | Summarize the operating-model change. |
| 4 | 「点」の指示から「円」の設計へ | Contrast prompts with agentic loops. |
| 5 | ループを閉じるのは成功条件 | Show why deterministic acceptance criteria matter. |
| 6 | Planner・Builder・Judgeが自律反復する | Explain the multi-agent control loop. |
| 7 | /goal・/loop・/batchが開発時間を解放する | Map asynchronous and parallel commands to outcomes. |
| 8 | AIで熟練者が19%遅くなる理由 | Introduce verification load and its limits. |
| 9 | AIを投入すべき仕事、任せない仕事 | Separate high-verifiability from low-verifiability work. |
| 10 | 長時間ループは文脈を捨てて強くなる | Explain context disposal and the Ralph Loop. |
| 11 | 企業事例が示すのは「8倍」より運用設計 | Present supplied Rakuten and Spotify outcomes with context. |
| 12 | CLAUDE.mdとMCPがチーム知を永続化する | Show external memory and tool connectivity. |
| 13 | 自律化にはコスト・権限・停止条件が要る | Define operational guardrails and safety controls. |
| 14 | 明日、自動化する1つのループを決める | End with a measurable first action. |

## Content rules

- Each slide communicates one primary conclusion.
- Paragraphs from the source will be converted into flows, comparisons, gates, and sparse diagrams.
- Supplied benchmark, market-share, productivity, and adoption figures will be labeled as supplied-source values rather than independently verified facts.
- Quotes will be paraphrased or kept very short; no new attributed quotation will be invented.
- The deck will not introduce product features, commands, dates, or performance claims that are absent from the supplied materials.
- Code-like configuration examples will be simplified into an operating-control diagram rather than reproduced as a dense code block.

## Artifact design

Work will be isolated under `workspace/0712-image2-brand-slides/`. Final local artifacts will be:

- Rendered source images under the workspace.
- A rebuilt 14-slide PowerPoint deck.
- Real JPEG slide images under `presentations/day_slides/images/0712/`.
- `presentations/day_slides/day_slide_2026_07_12.html` using the 2026-07-11 viewer structure.
- A downloadable PPTX under `presentations/day_slides/downloads/`.

The public day-slide index/list and sitemap will be updated only if required to make the locally completed 2026-07-12 slide discoverable. No remote publication or push is included.

## Error handling and scope controls

- If visual generation produces clipped, unreadable, or branded output, regenerate only the affected slide and keep rejected versions in a workspace-only folder.
- If the PDF and narrative conflict, the narrative controls wording and the PDF is treated only as a visual reference.
- Existing unrelated dirty-tree changes must remain untouched.
- Only 2026-07-12 workspace and publication paths may be created or edited, aside from `PLAN.md` and this design record.
- No commit or push of generated slide artifacts is included unless separately requested.

## Verification

- Inspect a full contact sheet and representative full-resolution slides for hierarchy, consistency, clipping, and accidental branding.
- Confirm all published images open as JPEG files and have the expected dimensions.
- Confirm the HTML figure count equals 14 and every local `src`/`href` resolves.
- Confirm the PPTX is a valid ZIP package with exactly 14 slide XML files.
- Render the PPTX for a visual parity check against the published JPEG deck.
- Run `git diff --check` and review the scoped diff for unrelated changes.

## Acceptance criteria

- The deck reads as a coherent continuation of the 2026-07-11 design family.
- All 14 slides are legible and free of overlap, clipping, watermarks, and logos.
- The story covers the article’s core ideas without copying its long paragraphs.
- Supplied figures are presented with appropriate provenance language.
- Viewer, JPEG set, and PPTX agree on slide order and slide count.
- No unrelated existing file is modified and no remote action is performed.
