# GlobalPerks Frontend — Design Specification

## Brand Identity

**GlobalPerks** is a premium photography brand. The visual identity communicates:
- **Craft** — every image is intentional, not accidental
- **Luxury** — this is not budget photography; it's an investment
- **Warmth** — the gold palette feels human, not corporate cold

---

## Design Tokens

```css
:root {
  /* Color palette */
  --gold-light:    #D9A640;
  --gold:          #BF8C2C;
  --gold-dim:      #8C6520;
  --gold-glow:     rgba(217, 166, 64, 0.08);
  --bg-dark:       #0A0A0A;
  --bg-surface:    #141414;
  --bg-card:       #1A1A1A;
  --border:        #2A2A2A;
  --border-gold:   rgba(217, 166, 64, 0.3);
  --text-primary:  #F5F5F0;
  --text-secondary:#A0A09A;
  --text-muted:    #606058;

  /* Typography */
  --font-display: 'DM Serif Display', Georgia, serif;
  --font-body:    'IBM Plex Mono', 'Courier New', monospace;

  /* Type scale */
  --text-xs:   0.75rem;   /* 12px — captions, labels */
  --text-sm:   0.875rem;  /* 14px — body small */
  --text-base: 1rem;      /* 16px — body */
  --text-lg:   1.25rem;   /* 20px — lead text */
  --text-xl:   1.75rem;   /* 28px — section headings */
  --text-2xl:  2.5rem;    /* 40px — page headings */
  --text-3xl:  4rem;      /* 64px — hero headings */
  --text-4xl:  6rem;      /* 96px — display hero */

  /* Spacing */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-12: 3rem;
  --space-16: 4rem;
  --space-24: 6rem;
  --space-32: 8rem;

  /* Layout */
  --max-width: 1200px;
  --nav-height: 72px;
}
```

---

## Typography

**Google Fonts to load:**
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=IBM+Plex+Mono:wght@300;400;500&display=swap" rel="stylesheet">
```

**Usage rules:**
- `DM Serif Display` — hero headlines, section titles, pull quotes. Never used for body copy.
- `IBM Plex Mono` — all body text, navigation, labels, buttons, captions. The monospace creates a distinctive editorial texture.

**Type hierarchy:**
```
Hero headline:    DM Serif Display, 6rem/1.0, normal
Page headline:    DM Serif Display, 4rem/1.1, normal
Section title:    DM Serif Display, 2.5rem/1.2, normal
Lead text:        IBM Plex Mono, 1.25rem/1.6, 300
Body:             IBM Plex Mono, 1rem/1.7, 400
Label/caption:    IBM Plex Mono, 0.75rem/1.4, 500, letter-spacing: 0.1em, uppercase
Navigation:       IBM Plex Mono, 0.875rem/1, 400
Button:           IBM Plex Mono, 0.875rem/1, 500, letter-spacing: 0.05em
```

---

## Navigation

**Structure:** Fixed top nav, 72px height, dark background with subtle bottom border.

**Left:** GlobalPerks wordmark in `DM Serif Display` + thin gold rule underneath
**Center:** Nav links — Home · Portfolio · Services · About · Contact
**Right:** "Book a Session" CTA button — gold border, transparent bg, hover fills gold

**Mobile:** Hamburger menu at ≤768px. Full-screen overlay nav, links stacked vertically.

**Active state:** Current page link has `color: var(--gold-light)` + 1px gold underline.

---

## Page Specifications

### index.html — Homepage

**Sections (in order):**

1. **Hero**
   - Full viewport height (100vh)
   - Background: full-bleed dark image (use a CSS placeholder gradient if no real image: `linear-gradient(135deg, #0A0A0A 0%, #1A1A1A 50%, #141414 100%)`)
   - Overlay: `rgba(10, 10, 10, 0.55)`
   - Content centered, text-align left (max-width 700px)
   - Eyebrow: `PREMIUM PHOTOGRAPHY` — monospace, tiny, gold, letter-spaced
   - Headline: `Moments That` (line break) `Live Forever` — DM Serif Display, large
   - Subtext: One sentence brand statement — monospace, muted
   - Two CTAs: Primary `View Portfolio` (gold filled) + Secondary `Book a Session` (ghost/outline)
   - Bottom-left: Scroll indicator — thin vertical line + "scroll" text

2. **Featured Work** (3-column asymmetric grid)
   - Section label: `SELECTED WORK` — monospace, gold, letter-spaced
   - Heading: `Stories Worth Telling` — DM Serif Display
   - 6-image masonry-style grid (2 columns left, 1 column right — unequal heights)
   - Each image card: on hover, overlay appears with category label + year
   - Use CSS `aspect-ratio` for placeholder boxes with subtle gradient fills
   - Link: `View full portfolio →`

3. **About Teaser** (two-column: text left, image right)
   - Label: `ABOUT THE PHOTOGRAPHER`
   - Headline: `Eye for Detail, Heart for People` — DM Serif Display
   - 2–3 sentence bio paragraph
   - Stat strip: 3 numbers — `150+ Sessions` · `8 Years` · `12 Countries`
   - CTA: `Read My Story →`

4. **Services Overview** (card grid)
   - Label: `WHAT I OFFER`
   - Headline: `Every Occasion, Captured`
   - 5 cards (one per service): Portraits · Weddings · Commercial · Events · Travel
   - Each card: service icon (SVG or Unicode symbol), name, one-line description, `from ₦X` price placeholder
   - Cards have gold border on hover

5. **Testimonials** (carousel)
   - Label: `KIND WORDS`
   - Headline: `What Clients Say`
   - 3 testimonial slides, auto-rotate every 5s
   - Each: large quote mark (gold), quote text, client name + type of shoot
   - Dot indicators below

6. **CTA Band**
   - Full-width dark surface band with gold accent line top
   - Headline: `Let's Create Something Beautiful`
   - Subtext: one line
   - Button: `Book a Session`

7. **Footer**
   - Logo + tagline left
   - Quick links: Home · Portfolio · Services · About · Contact
   - Social icons: Instagram · Pinterest · LinkedIn (SVG icons)
   - Copyright line

---

### portfolio.html — Portfolio

**Sections:**

1. **Page Hero** (shorter — 50vh)
   - Headline: `The Work`
   - Subtext: `A collection of moments, moods, and milestones`

2. **Filter Bar**
   - Pills: All · Portraits · Weddings · Commercial · Events · Travel
   - Active pill: gold background
   - JS filter: show/hide cards based on `data-category` attribute

3. **Gallery Grid**
   - Masonry grid: 3 columns desktop, 2 tablet, 1 mobile
   - Each item: image/placeholder + `data-category` attribute
   - Click opens lightbox (custom CSS/JS lightbox — no library needed)
   - Lightbox: dark overlay, image centered, prev/next arrows, close button, category + year label

---

### services.html — Services

**Sections:**

1. **Page Hero** (50vh)
   - Headline: `Services & Investment`

2. **Services Detail** (one section per service — alternating layout)
   - Each service: image side + text side
   - Text: service name, description (2–3 sentences), what's included (bullet list), price range, CTA `Enquire about this`
   - Alternate: image left/text right, then image right/text left

3. **Process Section**
   - Headline: `How It Works`
   - 4 steps: Enquiry → Consultation → The Shoot → Delivery
   - Step number in gold, title, one-line description

4. **FAQ Accordion**
   - 5–6 common questions, JS accordion expand/collapse
   - Gold chevron rotates on open

5. **CTA Band** (same as homepage)

---

### about.html — About

**Sections:**

1. **Page Hero** (50vh) — `Behind the Lens`

2. **Bio Section** (large image + text, generous whitespace)
   - Full photographer story — 3–4 paragraphs
   - Pull quote in DM Serif Display italic, gold left border

3. **Values Strip** — 3 columns: `Light · Emotion · Story`

4. **Equipment / Approach** (optional small section)

5. **CTA Band**

---

### contact.html — Contact

**Sections:**

1. **Page Hero** (40vh) — `Get in Touch`

2. **Contact Split** (two columns)
   - Left: Contact information
     - Email, Instagram, response time note
     - "Based in Lagos, shooting worldwide"
   - Right: **Booking Form** (the most important element)

---

## Booking Form Specification

The contact page booking form is the most critical frontend component.

```html
<form id="booking-form" novalidate>
  <!-- Row 1: Name + Email -->
  <div class="form-row">
    <div class="form-group">
      <label for="name">Full name</label>
      <input type="text" id="name" name="name" required maxlength="100" placeholder="Amara Okafor">
    </div>
    <div class="form-group">
      <label for="email">Email address</label>
      <input type="email" id="email" name="email" required placeholder="amara@example.com">
    </div>
  </div>

  <!-- Row 2: Phone + Service -->
  <div class="form-row">
    <div class="form-group">
      <label for="phone">Phone number</label>
      <input type="tel" id="phone" name="phone" required maxlength="20" placeholder="+234 801 234 5678">
    </div>
    <div class="form-group">
      <label for="service">Type of shoot</label>
      <select id="service" name="service" required>
        <option value="">Select a service</option>
        <option value="portraits">Portraits</option>
        <option value="wedding">Wedding</option>
        <option value="commercial">Commercial</option>
        <option value="events">Events</option>
        <option value="travel">Travel</option>
      </select>
    </div>
  </div>

  <!-- Row 3: Preferred date -->
  <div class="form-group">
    <label for="preferred_date">Preferred date</label>
    <input type="date" id="preferred_date" name="preferred_date" required>
  </div>

  <!-- Message -->
  <div class="form-group">
    <label for="message">Tell me about your vision</label>
    <textarea id="message" name="message" rows="5" maxlength="1000"
      placeholder="Share details about your shoot — location ideas, mood, special requirements..."></textarea>
  </div>

  <!-- Submit -->
  <button type="submit" class="btn btn-primary" id="submit-btn">
    Send Booking Request
  </button>

  <!-- States -->
  <div id="form-error" class="form-message error" hidden></div>
  <div id="form-success" class="form-message success" hidden>
    Your request has been received. We'll be in touch within 24 hours.
  </div>
</form>
```

**Form JS behaviour:**
- Client-side validation before submit (required fields, email format)
- On submit: disable button, show loading state `Sending...`
- `fetch('https://globalperks-backend.onrender.com/api/bookings/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(formData) })`
- On 201: hide form, show success message
- On 400: show field errors inline
- On 500: show generic error message
- On network error: show "Connection error. Please try again."

---

## Component Patterns

### Buttons
```css
.btn {
  font-family: var(--font-body);
  font-size: var(--text-sm);
  font-weight: 500;
  letter-spacing: 0.05em;
  padding: 0.875rem 2rem;
  border-radius: 2px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.btn-primary {
  background: var(--gold-light);
  color: var(--bg-dark);
  border: 1px solid var(--gold-light);
}
.btn-primary:hover {
  background: var(--gold);
  border-color: var(--gold);
}
.btn-ghost {
  background: transparent;
  color: var(--text-primary);
  border: 1px solid var(--border);
}
.btn-ghost:hover {
  border-color: var(--gold-light);
  color: var(--gold-light);
}
```

### Form inputs
```css
.form-group label {
  font-family: var(--font-body);
  font-size: var(--text-xs);
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-secondary);
  display: block;
  margin-bottom: var(--space-2);
}
input, select, textarea {
  width: 100%;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  color: var(--text-primary);
  font-family: var(--font-body);
  font-size: var(--text-base);
  padding: 0.875rem 1rem;
  border-radius: 2px;
  transition: border-color 0.2s;
}
input:focus, select:focus, textarea:focus {
  outline: none;
  border-color: var(--gold-dim);
}
input.error, select.error, textarea.error {
  border-color: #E24B4A;
}
```

### Status badges (admin)
```css
.badge { padding: 0.25rem 0.75rem; border-radius: 2px; font-size: 0.75rem; font-weight: 500; letter-spacing: 0.05em; text-transform: uppercase; }
.badge-pending   { background: rgba(186, 117, 23, 0.15); color: #EF9F27; border: 1px solid rgba(186, 117, 23, 0.3); }
.badge-confirmed { background: rgba(29, 158, 117, 0.15); color: #5DCAA5; border: 1px solid rgba(29, 158, 117, 0.3); }
.badge-declined  { background: rgba(226, 75, 74, 0.15);  color: #F09595; border: 1px solid rgba(226, 75, 74, 0.3); }
.badge-completed { background: rgba(55, 138, 221, 0.15); color: #85B7EB; border: 1px solid rgba(55, 138, 221, 0.3); }
.badge-archived  { background: rgba(136, 135, 128, 0.15);color: #B4B2A9; border: 1px solid rgba(136, 135, 128, 0.3); }
```

---

## Responsive Breakpoints

```css
/* Mobile first */
/* Base: 0–599px (mobile) */
@media (min-width: 600px)  { /* tablet portrait */ }
@media (min-width: 900px)  { /* tablet landscape / small desktop */ }
@media (min-width: 1200px) { /* desktop */ }
@media (min-width: 1600px) { /* wide desktop */ }
```

**Key responsive rules:**
- Nav collapses to hamburger at < 768px
- Hero headline: 6rem → 3.5rem → 2.5rem
- Grid columns: 3 → 2 → 1
- Form rows: 2-col → 1-col at < 600px
- Stats strip: horizontal → vertical stack

---

## Image Strategy

Since no real photos exist yet, use these placeholder approaches:

**Hero:** `background: linear-gradient(160deg, #1A1411 0%, #0A0A0A 40%, #141414 100%)`

**Portfolio grid placeholders:**
```css
.photo-placeholder {
  background: var(--bg-card);
  border: 1px solid var(--border);
  position: relative;
  overflow: hidden;
}
.photo-placeholder::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, var(--bg-surface) 0%, var(--bg-card) 100%);
  opacity: 0.5;
}
```

Use `<img src="https://picsum.photos/seed/{unique}/800/600" alt="...">` as placeholder images — these are consistent (same seed = same image) and appropriate for a photography site mockup.
