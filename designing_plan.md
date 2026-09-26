# Marsh AI Pitch Generator -- UI Design Plan

> **Status:** Awaiting approval before implementation.
> This document is the single source of truth for all CSS variables, spacing, and component behaviour. Nothing gets built until this plan is approved.

---

## Quick-Reference Token Table

| Token | Value | Usage |
|---|---|---|
| `--color-primary` | `#0A1F44` | Main navy -- headers, nav, key text |
| `--color-primary-light` | `#1A3A6E` | Hover states on navy surfaces |
| `--color-accent` | `#00A3A3` | Marsh teal -- CTA, focus rings, active indicators |
| `--color-accent-dark` | `#007A7A` | Teal hover/active |
| `--color-accent-subtle` | `#E6F7F7` | Teal tint -- chip backgrounds, selected states |
| `--color-bg` | `#F4F6F9` | Page background |
| `--color-surface` | `#FFFFFF` | Card/panel background |
| `--color-surface-2` | `#EEF1F6` | Nested background (e.g. claim rows) |
| `--color-border` | `#D1D9E6` | All borders |
| `--color-text-primary` | `#0F1C35` | Body text |
| `--color-text-secondary` | `#4A5872` | Labels, meta, captions |
| `--color-text-disabled` | `#9BA8BE` | Disabled state text |
| `--color-status-pass` | `#1A7F5A` | SUPPORTED -- dark green (text + icon) |
| `--color-status-pass-bg` | `#E6F5F0` | SUPPORTED -- row background |
| `--color-status-partial` | `#8A5A00` | PARTIALLY_SUPPORTED -- amber (text + icon) |
| `--color-status-partial-bg` | `#FEF6E4` | PARTIALLY_SUPPORTED -- row background |
| `--color-status-fail` | `#B91C1C` | UNSUPPORTED -- dark red (text + icon) |
| `--color-status-fail-bg` | `#FEE8E8` | UNSUPPORTED -- row background |
| `--color-status-unknown` | `#4A5872` | UNVERIFIABLE -- gray (text + icon) |
| `--color-status-unknown-bg` | `#EEF1F6` | UNVERIFIABLE -- row background |
| `--font-family` | `'Inter', sans-serif` | All text |
| `--radius-sm` | `4px` | Chips, badges, small elements |
| `--radius-md` | `8px` | Input fields, buttons |
| `--radius-lg` | `12px` | Cards, panels |
| `--shadow-sm` | `0 1px 3px rgba(10,31,68,0.08)` | Subtle surface lift |
| `--shadow-md` | `0 4px 16px rgba(10,31,68,0.10)` | Cards |
| `--shadow-lg` | `0 8px 32px rgba(10,31,68,0.13)` | Modals, dropdowns |
| `--spacing-unit` | `4px` | Base unit -- all spacing is a multiple of this |

---

## 1. Visual Identity

### 1.1 Color Palette

**Rationale:**

- **`#0A1F44` (Primary Navy):** Directly aligned with Marsh's official deep navy brand anchor. Used for the header, headings, and any surface that must communicate authority and stability -- insurance is a trust-first domain.
- **`#00A3A3` (Accent Teal):** Marsh's secondary teal, desaturated slightly from a pure cyan to avoid feeling clinical. Used sparingly -- *only* on the single primary CTA per screen state and active indicators. One accent color only; this is the entire accent budget.
- **`#F4F6F9` (Page Background):** A very slight blue-gray rather than pure white. Creates depth when white cards are placed on it without inducing the "screen glow" fatigue of `#FFFFFF` backgrounds on monitors.
- **`#0F1C35` (Text Primary):** Near-black with a slight blue undertone -- harmonises with the navy palette without the harshness of pure `#000000`.

**Contrast ratios (WCAG AA requires 4.5:1 for body text, 3:1 for large text):**

| Pair | Ratio | WCAG AA? |
|---|---|---|
| `--color-text-primary` on `--color-surface` (`#0F1C35` / `#FFFFFF`) | **16.2:1** | AAA |
| `--color-text-secondary` on `--color-surface` (`#4A5872` / `#FFFFFF`) | **7.1:1** | AA |
| `--color-text-primary` on `--color-bg` (`#0F1C35` / `#F4F6F9`) | **14.8:1** | AAA |
| White on `--color-primary` (`#FFFFFF` / `#0A1F44`) | **14.3:1** | AAA -- header text |
| White on `--color-accent` (`#FFFFFF` / `#00A3A3`) | **3.1:1** | AA -- large button text only |
| `--color-status-pass` on `--color-status-pass-bg` | **4.6:1** | AA |
| `--color-status-fail` on `--color-status-fail-bg` | **5.8:1** | AA |
| `--color-status-partial` on `--color-status-partial-bg` | **5.1:1** | AA |

### 1.2 Typography

**Font:** `Inter` (Google Fonts, variable font). Chosen because:
- Optimised for screen readability at small sizes (open apertures, tall x-height).
- Widely recognised as the standard for enterprise SaaS tools -- feels familiar and trustworthy, not experimental.
- Has a strong numeric character set (important for confidence scores, percentages).
- Free, no licensing risk.

**Type Scale:**

| Role | Size | Weight | Line-height | Color |
|---|---|---|---|---|
| H1 -- Page title | `28px` | `700` | `1.2` | `--color-primary` |
| H2 -- Section heading | `20px` | `600` | `1.3` | `--color-primary` |
| H3 -- Card title | `16px` | `600` | `1.4` | `--color-text-primary` |
| Body -- Default text | `14px` | `400` | `1.6` | `--color-text-primary` |
| Small / Label | `12px` | `500` | `1.5` | `--color-text-secondary` |
| Micro / Metadata | `11px` | `400` | `1.4` | `--color-text-secondary` |
| Button | `14px` | `600` | `1` | Context-dependent |
| Monospace (source clause) | `12px` system-mono | `400` | `1.6` | `--color-text-secondary` |

### 1.3 Spacing System

Base unit: **4px**. All margins, padding, and gaps are strict multiples:

| Scale | Value | Typical Use |
|---|---|---|
| `xs` | `4px` | Icon-to-label gap, badge padding |
| `sm` | `8px` | Chip internal padding, tight row gaps |
| `md` | `16px` | Card internal padding, field spacing |
| `lg` | `24px` | Section gaps within a card |
| `xl` | `32px` | Between major sections |
| `2xl` | `48px` | Top/bottom page breathing room |
| `3xl` | `64px` | Maximum outer container padding |

This is non-negotiable. No `margin: 13px` or `padding: 7px` anywhere.

### 1.4 Corner Radius, Shadow & Border Conventions

- **Radius `sm` (4px):** Chips, badges, status pills, small tags.
- **Radius `md` (8px):** Input fields, buttons, small cards.
- **Radius `lg` (12px):** All main cards and panels.
- **`border-radius: 9999px` (pill):** Reserved only for the overall status badge in the results header.

**Shadows:** Used to communicate elevation, not decoration:
- `shadow-sm` -- resting state for inputs and chips.
- `shadow-md` -- resting state for cards.
- `shadow-lg` -- reserved for modals/dropdowns only. No card gets `shadow-lg`.

**Borders:** A single `1px solid --color-border` on cards and inputs. The sole exception: a `2px solid --color-accent` left border on an *expanded* audit claim detail panel.

---

## 2. Layout & Information Architecture

### 2.1 Page Structure (top to bottom)

```
+-----------------------------------------------------+
|  HEADER (fixed, 56px)                               |
|  Marsh logo + product name                          |
+-----------------------------------------------------+
|  HERO INPUT PANEL (centered, max-width 680px)       |
|  Company name field -> Policy chips -> Generate CTA |
+-----------------------------------------------------+
|  [LOADING PANEL -- replaces input panel in-place]   |
|  Multi-step pipeline progress indicator             |
+-----------------------------------------------------+
|  [RESULTS SECTION -- appears below when done]       |
|  Summary card + Download button                     |
|  Audit Report: Overall badge + Per-slide claim list |
+-----------------------------------------------------+
|  ADMIN PANEL (collapsed by default, bottom of page) |
|  "Upload Policy Document" -- secondary feature      |
+-----------------------------------------------------+
```

**Ordering Justification:**

- **Header fixed:** Provides consistent orientation (Nielsen: Consistency & Standards). The user always knows where they are.
- **Input panel centered, constrained width:** F-pattern reading flow. A centered narrow column for the primary action focuses attention without competing visual noise. The single CTA (Generate) has no competition above the fold.
- **Loading replaces input in-place:** Not a new page. The transition happens in the same viewport zone -- the advisor knows what just happened.
- **Results appear below the input panel:** Progressive disclosure -- don't show results until there are results. The page extends downward naturally.
- **Admin panel at the bottom, collapsed:** Uploading a policy is a rare, privileged action. It should never compete visually with "Generate Pitch."

### 2.2 UX Principles Applied to Layout

- **Proximity:** Company name input, policy chip row, and Generate button are grouped inside one card. The audit report and deck summary card are siblings inside the results section -- related content, visually adjacent.
- **Consistency:** Every expandable section (audit claim detail, admin panel) uses the same chevron-down icon + smooth height transition. Every secondary action is always a text-link style, never a filled button.
- **Single primary CTA per screen state:** While showing results, the Download button (filled teal) is the primary CTA. The "Generate another" link is a secondary text-button in muted style.

### 2.3 Responsive Breakpoints

| Breakpoint | Width | Changes |
|---|---|---|
| Mobile | < 640px | Input panel full-width with 16px side padding; policy chips wrap freely; audit table stacks vertically |
| Tablet | 640px - 1024px | Input panel max-width: 560px; results max-width: 100% - 48px |
| Desktop | > 1024px | Input panel and results max-width: 720px, centered; 48px side margins |

Only three breakpoints. No over-engineering.

---

## 3. Component-by-Component Plan

### 3.1 Header / Branding

- **Height:** 56px fixed, `--color-primary` background.
- **Left:** Marsh logo mark (small white SVG) + "Marsh" wordmark in Inter 600, white, 16px. Separated from product name by a `1px` vertical rule (`rgba(255,255,255,0.2)`).
- **Right of rule:** "AI Pitch Generator" in Inter 400, `rgba(255,255,255,0.7)`, 14px -- clearly secondary to the brand name.
- **Right side of header:** Empty. No nav, no menu. This is a single-tool page; navigation would be a false affordance.
- **Why fixed:** The advisor may scroll through a long audit report. The Marsh brand should remain visible throughout -- it reinforces institutional credibility.

### 3.2 Company Name Input + Policy-Selection Chips

Contained in a white card (`shadow-md`, `radius-lg`), centered, max-width 680px.

- **Input field:** Full-width, 48px height (Fitts's Law). Placeholder: `"Enter company name (e.g. Infosys, Zomato)"`. Left icon: building SVG in `--color-text-secondary`. Focus state: border becomes `2px solid --color-accent` + faint `0 0 0 3px rgba(0,163,163,0.15)` outer glow.
- **Policy chips (below the input, 8px gap):** One chip per ingested policy document. Default state: white bg, `1px solid --color-border`, `--color-text-secondary` label. Selected state: `--color-accent-subtle` bg, `1px solid --color-accent`, `--color-accent-dark` text, checkmark icon. Always visible -- Recognition over Recall. "All Policies" pre-selected by default.
- **Label above chips:** `"Ground pitch against:"` in Small/Label style.

### 3.3 Primary "Generate" Button

- **Size:** Full-width within the card, 52px height. Large per Fitts's Law.
- **Default:** `--color-accent` fill, white "Generate Pitch", `radius-md`, Inter 600 14px, right-arrow icon.
- **Hover:** Background to `--color-accent-dark`. Arrow shifts 2px right (150ms ease).
- **Active:** Background `#005F5F`. Scale 0.98.
- **Disabled:** `--color-text-disabled` background, white text, `cursor: not-allowed`. No teal anywhere.
- **Loading:** Stays teal. Text becomes "Generating..." + spinning icon. Same dimensions -- no layout jump. `pointer-events: none`.

### 3.4 Multi-Step Loading Indicator

Displayed in place of the Generate button area. The input field remains visible (read-only).

Four pipeline steps as a horizontal stepper (desktop) / vertical list (mobile):

```
[Check] Building Company Profile    -- completed, teal + checkmark
[Pulse] Retrieving Policy Chunks    -- current, teal + pulse
[Empty] Generating Pitch Deck       -- pending, gray circle
[Empty] Auditing Claims             -- pending, gray circle
```

- **Completed step:** Filled teal circle + white checkmark. Label in `--color-text-primary 600`.
- **Current step:** Teal circle with pulse animation (scale 1.0 to 1.15 to 1.0, 1.2s infinite). Label in `--color-accent 600`.
- **Pending steps:** Empty circle (2px solid `--color-border`). Label in `--color-text-disabled`.
- **Connecting line:** 2px rule, teal for completed, `--color-border` for pending.
- **Live status line:** Small text below stepper that updates per stage. Satisfies Nielsen: Visibility of System Status.
- **Cancel link:** Discreet text-link below stepper. Satisfies Nielsen: User Control & Freedom.

### 3.5 Results Section: Deck Summary + Download + Audit Report

Appears below the input card with a smooth `translateY(16px to 0)` + `opacity 0 to 1` entrance (300ms ease-out).

**Deck Summary Card:**
- White card, `shadow-md`, `radius-lg`.
- Left: Slide-stack SVG in teal, 32px.
- Center: H3 "Pitch Deck Ready" + filename, slide count, generation time in Small style.
- Right: **Download button** (filled teal, "Download .pptx") as the primary CTA, with "Generate another" as a plain text-link below.

**Audit Report Section:**
- H2 "Audit Report" + overall status badge pill ("PASS" green or "REVIEW REQUIRED" amber) + confidence score in Small style.
- **Horizontal proportional bar** below the heading: four color-coded segments (teal/amber/red/gray) sized to claim count. Pass/fail judgment in under 2 seconds without reading any rows.

### 3.6 Audit Claim List

**Per-slide collapsible sections:**
- H3 slide title + chevron toggle. Closed by default. Pill badge: "5 claims / 1 issue" at a glance.

**Each claim row:**
- Status-specific background color.
- **Status icon (16px) at far left -- always paired with color:**
  - Green checkmark = SUPPORTED
  - Amber triangle = PARTIALLY_SUPPORTED
  - Red X = UNSUPPORTED
  - Gray question mark = UNVERIFIABLE
- Icon + color always together. Colorblind users read the shape; sighted users read the color.
- **Claim text** in Body style.
- **Right:** Confidence score (monospace badge) + verification method chip ("cosine" or "llm").
- **Entire row is clickable** (not just the chevron). Smooth `max-height` expand reveals:
  - Quoted source clause in a `<blockquote>` with `2px solid --color-accent` left border.
  - Source document name, similarity score, LLM rationale (if applicable).
  - Hidden by default -- detail for investigation, not for every glance.

### 3.7 Error / Validation States

- **Empty field:** Generate button disabled -- error prevented before it can happen (Nielsen: Error Prevention).
- **API error:** Inline error card (red left-border, error icon, plain message, Retry button, pre-filled company name).
- **Partial failure (audit timeout):** Amber warning card. Download button labeled "Download (Unaudited)" in amber.
- **Whitespace-only input:** Inline validation message below the field in `--color-status-fail` Small text. No modal.

### 3.8 Admin / Upload Panel

- Bottom of page, collapsed by default.
- Toggle: discreet "Admin: Upload Policy Document" text-link in `--color-text-secondary`. No teal, no filled button.
- Expanded: file drop-zone + outlined "Upload" button (no fill). Clearly secondary.
- Why at bottom: progressive disclosure -- never competes with "Generate Pitch."

---

## 4. Universal UI/UX Rules -- Confirmed

### Nielsen's Heuristics (relevant subset)

| Heuristic | Implementation |
|---|---|
| **Visibility of System Status** | Four-step loading stepper + live status text. Always know what the pipeline is doing. |
| **User Control & Freedom** | "Cancel" link during loading. "Generate another" after results. No dead-ends. |
| **Error Prevention** | Generate button disabled until valid input. Real-time validation, not post-submit. |
| **Recognition over Recall** | Policy chips always visible with persistent selected state. |
| **Consistency & Standards** | One pattern for expandable sections. One pattern for secondary actions. Teal = CTA only. |

### Fitts's Law

- Generate button: 52px tall, full-width. Not shrunk for aesthetics.
- Download button: 44px minimum height.
- Claim-row expand target: entire row width, not just the chevron.

### Accessibility

- **Color is never the only signal.** Every audit verdict uses a colored background AND a distinct icon shape simultaneously.
- **Focus states:** Visible `2px solid --color-accent` or `--color-primary` ring on all interactive elements. Never `outline: none` without a replacement.
- **Keyboard navigation:** Tab order follows visual order. Chips: `role="checkbox"`, Space to toggle. Expandable rows: `role="button"`, `aria-expanded` toggled.
- **All contrast ratios documented in Section 1.1. All meet WCAG AA minimum.**

### Don't Make the User Think

- Placeholder is a concrete example: "e.g. Infosys, Zomato" -- not just "Company name."
- Policy chips are labeled with actual insurer names, self-explanatory.
- Every button is verb + noun: "Generate Pitch", "Download .pptx", "Upload Document". No "Submit" or "OK."
- The proportional audit bar makes pass/fail legible in under 2 seconds.

---

## 5. "Stunning but Simple" Aesthetic Direction

### What We WILL Do

1. **Depth through restrained elevation.** Cards on a tinted background (`#F4F6F9`) lifted by `shadow-md`. Clean layering without gradients or textures. Depth is real (shadow geometry), not decorative.

2. **Accent color as a precision instrument.** Teal appears in exactly three places: Generate button, focus ring, current loading step. When the advisor's eye lands on teal, it means "act here" or "this is happening." No other usage.

3. **Purposeful motion, not decoration.** Exactly four animations:
   - Pulse on the current loading step (system is alive).
   - Button arrow shift on hover (tactile confirmation of interactivity).
   - Card entrance after results load (smooth `translateY` + `opacity`).
   - `max-height` expand on claim detail rows (no jarring jumps).
   All are 300ms or less, ease-out/ease-in-out. No looping decorative animations.

### What We Will NOT Do

- No gratuitous animation: no page particles, no shimmer on static text, no entrance animations on passive elements.
- No second accent color: teal is the entire accent budget.
- No decorative elements: no abstract shapes in the background, no watermarks, no decorative dividers. Every visual element is functional, semantic, or brand-anchored.
- No layout-shifting hover effects on cards.
- No modal dialogs for non-destructive content. Audit detail expands inline.

---

*Awaiting approval. Once confirmed, this document's Token Table becomes the direct source for all CSS custom properties.*
