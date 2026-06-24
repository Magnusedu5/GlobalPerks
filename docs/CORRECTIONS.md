# GlobalPerks — Design & Content Corrections

Read this entire file before making any changes. These are targeted corrections to the
already-built frontend and admin templates. Do not rebuild anything from scratch —
surgically update only what is specified here.

---

## CORRECTION 1 — Fonts (apply to ALL frontend HTML files)

### Replace the Google Fonts link in every HTML file

Find this (or any existing Google Fonts link tag) and replace with:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;1,300;1,400;1,500&family=Playfair+Display:ital,wght@0,400;0,700;1,400;1,700&family=Lato:wght@300;400;700&display=swap" rel="stylesheet">
```

### Replace every font reference in CSS across all frontend files

| Find | Replace with |
|---|---|
| `'DM Serif Display'` | `'Playfair Display'` |
| `'IBM Plex Mono'` | `'Lato'` |
| `'Courier New'` | `'Helvetica Neue'` |

### "GlobalPerks" navbar wordmark — update its CSS specifically

Find the `.nav-brand` or the anchor/span wrapping "GlobalPerks" in every nav and apply:

```css
font-family: 'Cormorant Garamond', Georgia, serif;
font-style: italic;
font-weight: 400;
font-size: 26px;
letter-spacing: 0.04em;
```

### Body text font-weight

Where body paragraphs use `font-weight: 400` with the old monospace, change to:
`font-weight: 300` and `line-height: 1.8` — Lato 300 reads better at body size.

Label/eyebrow text (uppercase, letter-spaced): `font-weight: 700`
Buttons: `font-weight: 700`
Nav links: `font-weight: 400`, `letter-spacing: 0.06em`

---

## CORRECTION 2 — Color Palette (apply to ALL frontend HTML files)

### Replace the full CSS variables block in every frontend file with this:

```css
:root {
  /* Brand palette — GlobalPerks by Perfecta */
  --burgundy:             #7A2E2E;
  --burgundy-light:       #9B3A3A;
  --burgundy-pale:        rgba(122, 46, 46, 0.08);
  --terracotta:           #C4753A;
  --terracotta-light:     #D4956A;
  --caramel:              #D4A574;
  --caramel-pale:         rgba(212, 165, 116, 0.15);

  --bg-dark:              #120A06;
  --bg-surface:           #1E0F08;
  --bg-card:              #2A1510;
  --bg-cream:             #FAF5EF;
  --bg-cream-deep:        #F2E8DA;

  --border-dark:          #3D1F14;
  --border-cream:         #E0D0BC;
  --border-accent:        rgba(212, 165, 116, 0.4);

  --text-dark:            #1A0A04;
  --text-light:           #FAF0E6;
  --text-secondary-dark:  #6B4A35;
  --text-secondary-light: #C4A882;
  --text-muted-dark:      #A0826A;
  --text-muted-light:     #7A5A44;

  --accent:               #7A2E2E;
  --accent-hover:         #9B3A3A;
  --accent-warm:          #C4753A;

  --font-display:  'Cormorant Garamond', Georgia, serif;
  --font-heading:  'Playfair Display', Georgia, serif;
  --font-body:     'Lato', 'Helvetica Neue', sans-serif;

  --text-xs:   0.75rem;
  --text-sm:   0.875rem;
  --text-base: 1rem;
  --text-lg:   1.25rem;
  --text-xl:   1.75rem;
  --text-2xl:  2.5rem;
  --text-3xl:  4rem;
  --text-4xl:  6rem;

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

  --max-width: 1200px;
  --nav-height: 72px;
}
```

### Specific color swap — find and replace these hardcoded hex values in frontend files

| Find | Replace with | Note |
|---|---|---|
| `#D9A640` | `#C4753A` | Old gold → terracotta |
| `#BF8C2C` | `#7A2E2E` | Old gold hover → burgundy |
| `#8C6520` | `#D4A574` | Old gold dim → caramel |
| `#0A0A0A` | `#120A06` | Cold black → warm espresso |
| `#141414` | `#1E0F08` | Cold dark → warm dark |
| `#1A1A1A` | `#2A1510` | Cold card → warm card |
| `#2A2A2A` | `#3D1F14` | Cold border → warm border |
| `#F5F5F0` | `#FAF0E6` | Cold white → warm white |
| `#A0A09A` | `#C4A882` | Cold secondary → warm tan |
| `#606058` | `#A0826A` | Cold muted → warm muted |

---

## CORRECTION 3 — Section Backgrounds

The site should now alternate warm dark and warm cream sections instead of being all-dark.

### index.html section backgrounds

| Section | Background | Text color to use |
|---|---|---|
| Nav | `rgba(18, 10, 6, 0.96)` | light variants |
| Hero | `#120A06` (dark) | light variants |
| Featured Work | `var(--bg-cream)` `#FAF5EF` | dark variants |
| About Teaser | `var(--bg-cream-deep)` `#F2E8DA` | dark variants |
| Services Overview | `var(--bg-surface)` `#1E0F08` | light variants |
| Testimonials | `var(--bg-cream)` `#FAF5EF` | dark variants |
| CTA Band | `var(--bg-surface)` `#1E0F08` | light variants |
| Footer | `var(--bg-dark)` `#120A06` | light variants |

On **cream background sections**, update:
- All headings → `color: var(--text-dark)` `#1A0A04`
- All body text → `color: var(--text-secondary-dark)` `#6B4A35`
- All eyebrow/label text → `color: var(--burgundy)` `#7A2E2E`
- All borders → `var(--border-cream)` `#E0D0BC`
- Card backgrounds → `#FFFFFF` with `border: 1px solid var(--border-cream)`

On **dark background sections**, update:
- All headings → `color: var(--text-light)` `#FAF0E6`
- All body text → `color: var(--text-secondary-light)` `#C4A882`
- All eyebrow/label text → `color: var(--caramel)` `#D4A574`
- All borders → `var(--border-dark)` `#3D1F14`

### services.html — alternate sections dark/cream/dark/cream/dark

Service 1 (Portraits): cream bg
Service 2 (Headshots): dark bg
Service 3 (Maternity): cream bg
Service 4 (Events): dark bg
Service 5 (Brand): cream bg

### about.html — cream background throughout, dark footer

### contact.html — cream background for contact split section

---

## CORRECTION 4 — Buttons

Replace button styles across all frontend files:

```css
.btn {
  font-family: 'Lato', sans-serif;
  font-weight: 700;
  font-size: 0.8rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  padding: 0.875rem 2.5rem;
  border-radius: 0;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-block;
  text-decoration: none;
}
.btn-primary {
  background: var(--burgundy);
  color: #FAF0E6;
  border: 1px solid var(--burgundy);
}
.btn-primary:hover {
  background: var(--burgundy-light);
  border-color: var(--burgundy-light);
}
.btn-ghost {
  background: transparent;
  color: var(--text-light);
  border: 1px solid rgba(250, 240, 230, 0.35);
}
.btn-ghost:hover {
  border-color: var(--caramel);
  color: var(--caramel);
}
```

Nav "Book a Session" button specifically:
```css
border-color: var(--caramel);
color: var(--caramel);
/* on hover: */
background: var(--burgundy);
color: #FAF0E6;
border-color: var(--burgundy);
```

---

## CORRECTION 5 — Real Content Updates

### index.html

**Hero eyebrow text** — find and replace:
- Old: `PREMIUM PHOTOGRAPHY` or `PREMIUM PHOTOGRAPHY · LAGOS`
- New: `PORTRAIT · FASHION · FAMILY · CALABAR`

**Hero headline** — wrap the second line in italic:
- Old: `Moments That Live Forever` (or similar)
- New: `Moments That <em>Live Forever</em>` — the `<em>` tag should render in italic Playfair Display

**About teaser — replace all three copy elements:**

Label:
- Old: `ABOUT THE PHOTOGRAPHER`
- New: `ABOUT PERFECTA`

Headline:
- Old: `Eye for Detail, Heart for People`
- New: `People Saw Beauty in What I Captured`

Bio paragraph:
- Old: any placeholder bio
- New: `GlobalPerks started with one simple thing — a camera and an eye for what others walked past. Today, Perfecta shoots portraits, headshots, maternity, family, and brand sessions from her Calabar studio, travelling wherever the story takes her.`

Stats strip:
- Old: `150+ Sessions · 8 Years · 12 Countries`
- New: `295+ Sessions · 5+ Years · Travel-Ready`

**Services overview cards — replace service names and descriptions:**

| Old service | New service | Description |
|---|---|---|
| Portraits | Portraits | Personal portrait sessions that celebrate who you are — confident, natural, and beautifully lit |
| Weddings | Headshots | Professional headshots for corporate teams, doctors, lawyers, and personal brands |
| Commercial | Maternity & Family | Tender, warm sessions capturing new life and the people you love most |
| Events | Events | From inductions to launches — every milestone documented with intention |
| Travel | Brand & Commercial | Branded content and campaign shoots for fashion, lifestyle, and product brands |

**Footer tagline:**
- Old: any generic tagline
- New: `Capturing beauty in moments.`

**Footer location line:**
- Old: `Lagos, Nigeria · Shooting Worldwide`
- New: `Calabar, Nigeria · Travel-Ready`

---

### services.html

**Replace the 5 service detail sections with correct GlobalPerks services:**

Service 1 — **Portraits** (cream bg, image right)
- Heading: `Portraits`
- Description: `Every person carries a story worth telling. Perfecta's portrait sessions are relaxed, directed, and focused on one thing — showing you at your most confident and authentic.`
- Includes: `Full edited gallery · Digital files in high resolution · 1–2 hour session · Wardrobe consultation`
- Price: `From ₦50,000`

Service 2 — **Headshots / Corporate** (dark bg, image left)
- Heading: `Headshots & Corporate`
- Description: `First impressions live online now. Whether you're a doctor, lawyer, executive, or entrepreneur — a sharp, professional headshot tells people you take your work seriously.`
- Includes: `Individual or team sessions · LinkedIn and press-ready files · Same-week delivery · Studio or on-location`
- Price: `From ₦35,000`

Service 3 — **Maternity & Family** (cream bg, image right)
- Heading: `Maternity & Family`
- Description: `These are the moments you'll want to remember exactly as they felt. Warm, unhurried sessions that document new life, growing families, and the people who matter most.`
- Includes: `Bump and newborn sessions available · Full edited gallery · Print-ready files · Studio or outdoor`
- Price: `From ₦60,000`

Service 4 — **Events** (dark bg, image left)
- Heading: `Events`
- Description: `Nursing inductions, graduation ceremonies, brand launches, award nights — Perfecta captures the energy and emotion of every milestone with speed and precision.`
- Includes: `Full event coverage · Fast turnaround · Crowd and detail shots · Candid and directed moments`
- Price: `From ₦80,000`

Service 5 — **Brand & Commercial** (cream bg, image right)
- Heading: `Brand & Commercial`
- Description: `Your brand deserves imagery that matches its quality. From fashion lookbooks to product campaigns, Perfecta creates content that stops the scroll and sells the vision.`
- Includes: `Creative direction · Full licensed files · Multiple looks · Collaboration with brands and stylists`
- Price: `From ₦150,000`

---

### about.html

**Replace bio section copy entirely:**

Pull quote (large italic, burgundy left border):
`"GlobalPerks started with one simple thing... people saw beauty in what I captured."`

Bio paragraphs (3 paragraphs):

Paragraph 1:
`Before GlobalPerks had a name, it had a feeling. Perfecta picked up a camera not because she planned a career, but because people kept stopping to ask about the photos she was taking. What started as curiosity became a calling.`

Paragraph 2:
`Based in Calabar and available to travel anywhere the story leads, Perfecta has spent five years building a body of work that spans personal portraits, corporate headshots, maternity sessions, brand campaigns, and live events. Her clients range from fresh graduates marking a milestone to established brands building their visual identity.`

Paragraph 3:
`Her approach is simple: make people feel comfortable, then capture them when they forget she's there. The result is images that feel both polished and real — because they are.`

**Values strip — replace three values:**
- `LIGHT` → description: `Every session is built around beautiful, flattering light`
- `PEOPLE` → description: `She photographs people, not poses — the real moments land hardest`
- `STORY` → description: `Each image is a frame in something larger — your story`

**Stats:**
- `295+` → Sessions Completed
- `5+` → Years Shooting
- `Calabar` → Home Base

---

### contact.html

**Replace contact info column text:**

Heading: `Let's Work Together`

Email line: `hello@globalperks.com`

Instagram line: `@globalperks_` (link to https://instagram.com/globalperks_)

Also add: `@globalperks_lovestories` with label `For weddings` (link to https://instagram.com/globalperks_lovestories)

Response time: `All enquiries answered within 24 hours`

Location: `Based in Calabar · Available for travel nationwide & beyond`

**Replace booking form service dropdown options:**

```html
<select id="service" name="service" required>
  <option value="">Select a service</option>
  <option value="portraits">Portraits</option>
  <option value="headshots">Headshots / Corporate</option>
  <option value="maternity">Maternity & Family</option>
  <option value="events">Events</option>
  <option value="brand">Brand & Commercial</option>
</select>
```

**Update form placeholder text:**
- Name placeholder: `Your full name`
- Email placeholder: `your@email.com`
- Phone placeholder: `+234 800 000 0000`
- Message placeholder: `Tell Perfecta about your shoot — the occasion, mood, location ideas, or anything that will help her prepare`

---

## CORRECTION 6 — Admin Templates (backend only)

In all three admin HTML templates (`login.html`, `bookings_list.html`, `booking_detail.html`):

**Add this Google Fonts link to each `<head>`:**
```html
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital@1&display=swap" rel="stylesheet">
```

**Update CSS variables:**
```css
--bg:         #100806;
--surface:    #1C0E08;
--border:     #3D1F14;
--text:       #FAF0E6;
--muted:      #C4A882;
--gold:       #C4753A;
--gold-dim:   #8B3A3A;
```

**Update the "GlobalPerks Admin" brand text in the nav of `base.html` (or whichever template has the nav):**
```css
font-family: 'Cormorant Garamond', Georgia, serif;
font-style: italic;
font-size: 20px;
color: #C4753A;
font-weight: 400;
letter-spacing: 0.04em;
```

**Update `login.html` brand heading:**
Same font styles as above. Change subtitle from "ADMIN PANEL" to "ADMIN" — keep it minimal.

---

## CORRECTION 7 — Update backend serializer service choices

In `backend/apps/bookings/serializers.py`, update the VALID_SERVICES list:

```python
VALID_SERVICES = ['portraits', 'headshots', 'maternity', 'events', 'brand']
```

In `backend/apps/core/email_service.py`, the service name already uses `.title()` so
`headshots` → `Headshots`, `brand` → `Brand` etc. No change needed there.

---

## Verification

After all corrections are applied:

1. Open `frontend/index.html` in browser
   - Navbar "GlobalPerks" should be in italic Cormorant Garamond
   - Hero eyebrow reads `PORTRAIT · FASHION · FAMILY · CALABAR`
   - Featured Work and About sections have cream backgrounds
   - Hero and Services sections have dark warm backgrounds
   - About teaser reads "People Saw Beauty in What I Captured"
   - Stats show `295+ Sessions · 5+ Years · Travel-Ready`

2. Open `frontend/contact.html`
   - Service dropdown shows 5 correct options (Portraits, Headshots, Maternity, Events, Brand)
   - Location reads "Calabar"
   - Instagram shows both @globalperks_ and @globalperks_lovestories

3. Open `frontend/services.html`
   - 5 correct services with correct copy
   - Sections alternate cream/dark correctly

4. Open `frontend/about.html`
   - Pull quote reads "GlobalPerks started with one simple thing..."
   - Three bio paragraphs about Perfecta present
   - Values show LIGHT · PEOPLE · STORY

5. Visit `http://localhost:8000/admin-panel/login/`
   - "GlobalPerks Admin" in italic terracotta Cormorant Garamond

6. `python manage.py runserver` starts with no errors after serializer change
