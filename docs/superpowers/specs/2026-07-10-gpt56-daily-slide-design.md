# 2026-07-10 GPT-5.6 Daily Slide Design

## Goal

Create and publish a redesigned 15-page daily slide for 2026-07-10 using these inputs as the content contract:

- `input/day/0710slide.txt`
- `input/day/0710.png`
- `input/day/0710.pdf`
- `presentations/day_slides/day_slide_2026_07_09.html` as the public-page reference

The work includes pushing the finished daily-slide files to `main` and verifying the remote commit and public page.

## Content Boundary

The supplied TXT, PNG, and PDF are authoritative. The redesign may shorten and reorganize wording for slide readability, but it must not introduce or externally revise factual claims. Each page presents one primary message.

## Visual Direction

Use an executive-infographic style that continues the readable public presentation pattern from 2026-07-09 while replacing the supplied PDF design:

- 16:9 layout
- white to pale-blue background
- navy, teal, and orange as the primary palette
- large Japanese headings and concise body copy
- diagrams, matrices, process flows, and comparison cards instead of dense paragraphs
- consistent page number, spacing, and visual hierarchy
- no added logo asset

## Page Structure

1. GPT-5.6 introduction and adoption roadmap
2. Shift from the intelligence war to the value war
3. Sol, Terra, and Luna model family
4. Model pricing and use-case matrix
5. Value and the Pareto frontier
6. Sol and Fable 5 comparison
7. Programmatic Tool Calling
8. Multi-agent and Ultra mode
9. Reasoning Effort selection
10. ChatGPT Work, Codex, and Sites integration
11. Brevity Paradox and prompt design
12. Value-optimized model routing
13. Autonomy risks and approval gates
14. Day-one adoption checklist
15. Conclusion: maximize execution value

## Output Architecture

Generate a 15-slide deck and rendered slide images, then publish them through the existing daily-slide page structure:

- `presentations/day_slides/day_slide_2026_07_10.html`
- `presentations/day_slides/downloads/day_slide_2026_07_10_<slug>.pptx`
- `presentations/day_slides/images/0710/cover.jpg`
- `presentations/day_slides/images/0710/p01.jpg` through `p14.jpg`
- latest-entry updates in `presentations/day_slides_index.html`
- latest-entry updates in `presentations/day_slides_list.html`
- URL entry in `sitemap.xml`

The HTML viewer keeps the existing wide `1696px` presentation shell and public metadata pattern.

## Data Flow

1. Extract the narrative and labels from `0710slide.txt`.
2. Use `0710.png` for illustration vocabulary and `0710.pdf` for topic coverage and diagram references.
3. Rebuild all 15 pages in the selected visual system.
4. Export real JPEG slide images and the downloadable PPTX.
5. Generate the dated HTML viewer and update the three discovery files.
6. Validate local references, image formats, deck/page counts, and Git diff hygiene.
7. Commit only the dated slide outputs and required index files, push to `main`, and verify the remote commit and public URL.

## Failure Handling

- Stop if the generated deck does not contain exactly 15 slides.
- Stop if any HTML image or download reference is missing.
- Stop if any published `.jpg` is not a real JPEG.
- Preserve unrelated tracked and untracked workspace files.
- If `main` diverges before publishing, use an isolated worktree from the current remote state rather than rebasing the dirty workspace.
- Do not claim publication until the pushed commit is visible on `origin/main`; public-page verification follows after deployment propagation.

## Verification

- Visually inspect a contact sheet and selected full-resolution pages for clipping, overlap, and unreadable text.
- Confirm 15 HTML figures, 15 JPEG files, and 15 PPTX slide XML entries.
- Resolve every local `src` and `href` in the dated HTML.
- Confirm `day_slides_index.html`, `day_slides_list.html`, and `sitemap.xml` contain the 2026-07-10 URL.
- Run `git diff --check` on the staged daily-slide files.
- Verify the pushed commit with `git ls-remote` or the updated `origin/main` log.
- Request the public 2026-07-10 URL and confirm the dated title marker when deployment is available.
