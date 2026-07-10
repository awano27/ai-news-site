# GPT-5.6 Daily Slide Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign, publish, and push a 15-slide GPT-5.6 daily presentation for 2026-07-10 from the supplied TXT, PNG, and PDF.

**Architecture:** Keep generation-only artifacts under `workspace/0710-image2-brand-slides/`, with one Image2-generated PNG per slide and deterministic title-only stabilization for normal slides. Build an image-backed 16:9 PPTX from the stabilized PNGs, then use the repository publisher to create the dated HTML, JPEGs, index entries, and sitemap entry before a scoped commit and push.

**Tech Stack:** Built-in Image2 generation, Python 3 with Pillow, Node.js with PptxGenJS, repository `scripts/publish_image2_day_slide.py`, Git, and static HTML.

## Global Constraints

- The deck contains exactly 15 slides in 16:9 format.
- The content contract is `input/day/0710slide.txt`, `input/day/0710.png`, and `input/day/0710.pdf`.
- The visual direction is executive infographic: white to pale blue, navy, teal, and orange, with large Japanese headings and concise copy.
- The supplied content is authoritative; shorten and reorganize it without introducing or externally revising factual claims.
- Use no-logo mode and do not invent a logo.
- Slide 2 is `本日の流れ`.
- Do not show page numbers or sequence numbers in visible slide titles.
- The slide body must be Image2-generated; code may only stabilize normal-slide titles and package images into PPTX/JPEG/HTML.
- Preserve original Image2 outputs under `image2-original/`; final images come from `image2-fixed/`.
- Preserve unrelated tracked and untracked workspace files.
- Push to `main` only after local validation, then verify `origin/main` and the public URL.

---

### Task 1: Lock the 15-slide source coverage and visual system

**Files:**
- Create: `workspace/0710-image2-brand-slides/input_manifest.md`
- Create: `workspace/0710-image2-brand-slides/deck_structure.md`
- Create: `workspace/0710-image2-brand-slides/design_system.md`
- Create: `workspace/0710-image2-brand-slides/titles.json`
- Create: `workspace/0710-image2-brand-slides/prompts/01-title.md` through `15-conclusion.md`

**Interfaces:**
- Consumes: the three source files and the approved design spec.
- Produces: a complete coverage map, reusable design rules, 15 exact one-slide prompts, and `[{'file': string, 'title': string}]` title metadata.

- [ ] **Step 1: Create the input manifest**

Write that `0710slide.txt` supplies the narrative and labels, `0710.png` supplies illustration vocabulary, and `0710.pdf` supplies topic coverage and diagram references. Record no-logo mode and state that no unrelated template or prior workspace output is an input.

- [ ] **Step 2: Create the coverage-first deck structure**

Use this exact slide map:

| File | Visible title | Key message | Required visual |
|---|---|---|---|
| `01-title.png` | `GPT-5.6 導入・活用戦略ロードマップ` | 知能の高さではなく、実行価値でAIを選ぶ | central AI routing core with three colored paths |
| `02-agenda.png` | `本日の流れ` | 価値、実行基盤、運用の3章で理解する | three-section horizontal journey |
| `03-value-war.png` | `知能戦争から価値戦争へ` | 評価軸はIQから完遂力・コスト・統合へ移る | before/after evaluation bridge |
| `04-family.png` | `階層化されたモデルファミリー` | Sol・Terra・Lunaは役割分担で価値を最大化する | three-tier family architecture |
| `05-model-matrix.png` | `料金と用途の戦略マトリクス` | Terraを標準、Lunaを大量処理、Solを難題へ | three-column comparison with supplied prices |
| `06-pareto.png` | `価値で見るPareto Frontier` | 最高知能ではなく完了までの総コストで選ぶ | cost-versus-completion scatter curve |
| `07-competitive.png` | `SolとFable 5の使い分け` | 深い分析と実行効率は別の評価軸である | balanced two-column diagnostic comparison |
| `08-ptc.png` | `Programmatic Tool Calling` | 判断不要の連続ツール処理をコードで圧縮する | legacy loop versus sandboxed JS flow |
| `09-multi-agent.png` | `Multi-agent / Ultraモード` | 親エージェントが専門作業を並列統合する | parent and four specialist branches |
| `10-effort.png` | `Reasoning Effortを使い分ける` | タスクの重さに応じて推論コストを調整する | low/medium/high/max control rail |
| `11-ecosystem.png` | `Work・Codex・Sitesの統合` | コンテキスト取得から実装・共有までを接続する | three-layer operating system stack |
| `12-prompting.png` | `Brevity Paradoxを越える` | 簡潔さではなく優先順位と権限境界を指定する | bad/good prompt design comparison |
| `13-routing.png` | `価値最適化ルーティング` | LunaからTerra、Solへ段階的に振り分ける | decision tree with three endpoints |
| `14-governance.png` | `自律性を制御するガバナンス` | 承認ゲート、最小権限、ZDRで逸脱を抑える | shield with three control layers |
| `15-conclusion.png` | `実行価値を最大化する` | ルーティング、プロンプト、監督体制を今すぐ整える | three-action closing roadmap |

Map all eight numbered sections of `0710slide.txt`, both supplied comparison matrices, the risk examples, and the three final action steps to one or more rows. State explicitly that no source section is omitted.

- [ ] **Step 3: Create the reusable no-logo design system**

Specify these exact roles:

```text
Background: #F6FAFC
Surface: #FFFFFF
Primary text: #102A43
Muted text: #52667A
Teal: #0C8A8A
Navy: #173B63
Orange: #F28C28
Line: #D9E4EA
Sol accent: #F2B544
Terra accent: #2D9B78
Luna accent: #D95B73
```

Use Noto Sans JP style, Regular headings, Light body, Medium emphasis, wide margins, two or three groups per slide, clean flat diagrams, and no decorative gradients, page numbers, logo, dense dashboards, or copied template chrome.

- [ ] **Step 4: Create 15 prompt files from one shared contract**

Every prompt must contain the exact global contract below, followed by its row's visible title, key message, required visual, and the assigned source copy:

```text
Use case: productivity-visual
Asset type: standalone presentation slide
Create a single 16:9 slide image. Do not create a contact sheet. Do not include multiple slides in one image.
The slide body/content must be Image2-generated. Do not use SVG, code-rendered layout, wireframe, or programmatic vector graphics.
No logo appears. Do not invent a logo. Do not show page numbers. Do not include sequence numbers in visible slide titles.
Use a simple executive-infographic consulting style with generous whitespace, wide margins, one clear key message, and at most three content groups.
Use a pale blue-white background, navy text, teal structure, and orange emphasis. Use Noto Sans JP style with Regular headings, Light body text, and Medium emphasis only.
Make all Japanese text accurate and readable. Use only the supplied slide copy. Do not imitate unrelated templates.
```

Normal-slide prompts also require a quiet title at the top-left and an empty top-right corner. The title-slide prompt requires a central hero composition and no normal-slide header.

- [ ] **Step 5: Create title metadata and verify structure**

`titles.json` contains all 15 file/title pairs from the table. Run:

```powershell
$root = 'workspace/0710-image2-brand-slides'
(Get-ChildItem "$root/prompts" -Filter '*.md').Count
(Get-Content "$root/titles.json" -Raw -Encoding UTF8 | ConvertFrom-Json).Count
rg -n "本日の流れ|no source section is omitted|No logo appears" $root
```

Expected: prompt count `15`, title count `15`, and matches in the structure/design/prompt files.

### Task 2: Generate and review the first five slides

**Files:**
- Create: `workspace/0710-image2-brand-slides/image2-original/01-title.png` through `05-model-matrix.png`
- Create: `workspace/0710-image2-brand-slides/image2-fixed/01-title.png` through `05-model-matrix.png`
- Create: `workspace/0710-image2-brand-slides/stabilize_no_logo_headers.py`

**Interfaces:**
- Consumes: prompt files 01-05 and the design system.
- Produces: five preview-ready final PNGs with separate preserved originals.

- [ ] **Step 1: Generate slides 1-5 as separate built-in Image2 calls**

Issue one image-generation call per prompt. Copy each selected output from `$CODEX_HOME/generated_images/` into `image2-original/` with the exact stable name. Do not combine slides.

- [ ] **Step 2: Write the title-only stabilization helper**

The helper must copy `01-title.png` unchanged, then for slides 2-15 cover only the top 13% header band with `#F6FAFC`, redraw the exact title at top-left in `#102A43`, and draw a short teal rule beneath it. It must not draw a logo, page number, or body content.

- [ ] **Step 3: Stabilize slides 2-5**

Run:

```powershell
python workspace/0710-image2-brand-slides/stabilize_no_logo_headers.py `
  --input-dir workspace/0710-image2-brand-slides/image2-original `
  --output-dir workspace/0710-image2-brand-slides/image2-fixed `
  --titles workspace/0710-image2-brand-slides/titles.json
```

Expected: five PNGs in `image2-fixed/`; slide 1 remains pixel-identical to its original.

- [ ] **Step 4: Inspect every preview slide at original size**

Check Japanese text, missing copy, clipping, overlap, contrast, title position, accidental logos, page numbers, and style consistency. Regenerate any slide with text or composition defects, rerun stabilization, and complete at least one fix-and-verify cycle.

- [ ] **Step 5: Present the five preview slides for approval**

Show the five stabilized files individually and wait for explicit approval before generating slides 6-15.

### Task 3: Generate and stabilize slides 6-15

**Files:**
- Create: `workspace/0710-image2-brand-slides/image2-original/06-pareto.png` through `15-conclusion.png`
- Create: `workspace/0710-image2-brand-slides/image2-fixed/06-pareto.png` through `15-conclusion.png`

**Interfaces:**
- Consumes: approved preview, prompts 06-15, stable design system, and title helper.
- Produces: all 15 final PNGs.

- [ ] **Step 1: Generate slides 6-15 through authorized independent workers**

Assign each worker one slide or a small independent batch with the exact prompt content, no-logo rule, stable filename, and one-slide-only requirement. Each worker uses the built-in image tool and saves its output under `image2-original/`.

- [ ] **Step 2: Run deterministic title stabilization for all normal slides**

Run the same helper across the full original directory. Expected: exactly 15 PNGs in both `image2-original/` and `image2-fixed/`.

- [ ] **Step 3: Perform full-deck visual QA**

Inspect all 15 final PNGs at original size. Record issues, regenerate affected originals with one targeted prompt change, rerun title stabilization, and verify the affected slide again. Continue until a full pass finds no new clipping, overlap, unreadable text, accidental logo, or page-number issue.

### Task 4: Package the final PNGs into a valid PowerPoint deck

**Files:**
- Create: `workspace/0710-image2-brand-slides/build_image_deck_pptx.mjs`
- Create: `workspace/0710-image2-brand-slides/0710_image2_rebuilt.pptx`

**Interfaces:**
- Consumes: 15 final PNGs in filename order.
- Produces: a 15-slide 16:9 image-backed PPTX compatible with the repository publisher.

- [ ] **Step 1: Implement the minimal PptxGenJS packager**

The script creates a fresh `pptxgenjs` presentation with `LAYOUT_16x9`, adds one full-bleed image per slide at `{x:0,y:0,w:10,h:5.625}`, sets title and subject metadata, and writes `0710_image2_rebuilt.pptx`. It adds no code-rendered text or shapes.

- [ ] **Step 2: Build and structurally validate the deck**

Run:

```powershell
$env:NODE_PATH='C:/Users/awano/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules'
& 'C:/Users/awano/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe' `
  workspace/0710-image2-brand-slides/build_image_deck_pptx.mjs
python -c "import zipfile,re; p='workspace/0710-image2-brand-slides/0710_image2_rebuilt.pptx'; z=zipfile.ZipFile(p); print(len([n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',n)]))"
```

Expected: `15`.

- [ ] **Step 3: Render the PPTX and complete the required fix-and-verify loop**

Convert the PPTX to PDF and JPEGs with the bundled office helpers. Compare the rendered pages with the final PNGs, list any aspect-ratio, cropping, or packaging issue, fix the packager if needed, and rerender. Expected: 15 uncropped 16:9 pages.

### Task 5: Generate the dated public slide page

**Files:**
- Create: `presentations/day_slides/day_slide_2026_07_10.html`
- Create: `presentations/day_slides/downloads/day_slide_2026_07_10_gpt56_value_roadmap.pptx`
- Create: `presentations/day_slides/images/0710/cover.jpg`
- Create: `presentations/day_slides/images/0710/p01.jpg` through `p14.jpg`
- Modify: `presentations/day_slides_index.html`
- Modify: `presentations/day_slides_list.html`
- Modify: `sitemap.xml`

**Interfaces:**
- Consumes: full final image directory, image-backed PPTX, title metadata, and public title/summary.
- Produces: the complete static public artifact set.

- [ ] **Step 1: Dry-run the publisher**

Run:

```powershell
python scripts/publish_image2_day_slide.py 0710 `
  --workspace workspace/0710-image2-brand-slides `
  --input-text input/day/0710slide.txt `
  --title 'GPT-5.6 導入・活用戦略ロードマップ' `
  --summary 'GPT-5.6のSol・Terra・Luna、エージェント実行基盤、価値最適化ルーティング、プロンプト戦略、ガバナンスを15枚で整理する。' `
  --slug gpt56_value_roadmap `
  --dry-run
```

Expected: only the dated HTML, PPTX, 15 JPEGs, index, list, and sitemap are listed.

- [ ] **Step 2: Generate without Git mutation**

Run the same command without `--dry-run`. Expected: `[publish] validation passed` and `[publish] done`.

- [ ] **Step 3: Independently validate the public artifacts**

Confirm 15 HTML figures, 15 real JPEG files, 15 PPTX slide XML files, all local `src`/`href` targets, a `max-width: 1696px` viewer, and the dated URL in index, list, and sitemap.

### Task 6: Commit, push, and verify publication

**Files:**
- Stage only the files produced by Task 5 plus the approved design documentation already committed.

**Interfaces:**
- Consumes: validated public artifacts and current remote state.
- Produces: a scoped commit on `main`, matching `origin/main`, and verified public page markers.

- [ ] **Step 1: Fetch and confirm safe push state**

Run `git fetch origin main` and confirm the current branch contains `origin/main` with no remote-only commit. If it does not, stop and use an isolated worktree from `origin/main` rather than rebasing the dirty workspace.

- [ ] **Step 2: Stage only the daily slide files**

Use the publisher's explicit file list or `git add -f` with the exact dated HTML, PPTX, 15 JPEGs, index, list, and sitemap. Run `git diff --cached --name-only` and confirm no daily news, report, public-pages JSON, input, or workspace file is staged.

- [ ] **Step 3: Validate the staged diff and commit**

Run `git diff --cached --check`, repeat the static validations against the staged filenames, then commit with:

```powershell
git commit -m "feat: publish 2026-07-10 daily slide"
```

- [ ] **Step 4: Push and verify the remote commit**

Run `git push origin HEAD:main`, then compare `git rev-parse HEAD` with `git ls-remote origin refs/heads/main`. Expected: identical hashes.

- [ ] **Step 5: Verify the public URL after deployment propagation**

Request `https://visionhub.jp/presentations/day_slides/day_slide_2026_07_10.html` until it returns success or a reasonable deployment window expires. Confirm the title `GPT-5.6 導入・活用戦略ロードマップ`, 15 slide figures, and the `images/0710/cover.jpg` marker. Report remote push success separately from deployment status if the page has not propagated yet.
