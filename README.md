Here is a comprehensive system context prompt you can use. You can paste this into a **`.cursorrules`** file (if using Cursor), your **Custom Instructions** in ChatGPT, or simply paste it at the start of a new chat session to ground the LLM.

---

# Project Context: SmartMaps SaaS (Malaysian Edition)

**Project Description**
We are building a **B2B SaaS Digital Directory Platform** tailored for the Malaysian market (Malls, Universities, Exhibition Centers). It replaces physical directory boards with a mobile-first, QR-code-accessible web app.

**Business Goal**

* **Primary Revenue:** Monthly SaaS fees from Venue Owners (RM200/mo).
* **Expansion Revenue:** "Featured Merchant" fees (Ad slots) and Upsells.
* **User Value:** Fast, friendly mobile directory to find shops, check Halal status, and contact merchants via WhatsApp.

---

## Charging & Billing (MVP)

This repo includes a lightweight billing domain to support the SaaS model:

* `venues.Plan`: defines pricing (monthly fee, featured merchant fee, merchant limits).
* `venues.VenueSubscription`: tracks a venue’s plan + status (`TRIALING/ACTIVE/PAST_DUE/CANCELED`) and period dates.

**Recommended MVP flow**

1. Create Plans in Django Admin (e.g. Starter RM200/mo).
2. When a new Venue is created, create a `VenueSubscription` (trial by default).
3. Use `PAST_DUE` to gate premium features (e.g., featured sorting, more merchants, analytics).
4. In production, plug payments into a provider later (Stripe/FPX/DuitNow); keep `VenueSubscription` as the source of truth in-app.

---

### 1. Technology Stack

* **Backend:** Django 5.x (Python).
* **Frontend:** Django Templates (Server-Side Rendering).
* **Styling:** Tailwind CSS (via CDN for dev, build pipeline later).
* **Interactivity:** **HTMX** (for infinite scroll/pagination and search) and **Alpine.js** (for simple UI toggles like accordions).
* **Database:** PostgreSQL (Production) / SQLite (Dev).
* **Hosting:** Railway/Render.

**Constraints & Architecture Rules**

* **No SPA Frameworks:** Do not suggest React, Vue, or Next.js. We use the "Django Monolith + HTMX" approach to keep the stack simple and deployable by a single developer.
* **HTMX Pattern:** Use `hx-get`, `hx-target`, and `hx-swap` for list updates. Always split lists into `partials/` templates to allow re-rendering parts of the page.
* **Static/Media:** Use `Whitenoise` for static files. Media files (images) are served from AWS S3 (future) or local media root (current).

---

### 2. Database Schema (Core Domain: `venues` app)

* **Venue:** Represents the client (Mall/Campus).
* Fields: `name`, `slug`, `venue_type`, `cover_image`.


* **Floor:** Linked to Venue.
* Fields: `name` (e.g., "Level 1"), `level_order` (int).


* **MerchantCategory:** Lookup table (e.g., "Food", "Fashion").
* **Merchant:** The core entity.
* **Location:** `lot_number` (G-45), `nearest_entrance` (Near North Court).
* **Visuals:** `logo`, `storefront_image`.
* **Local Context:** `is_halal` (Boolean), `accepts_ewallet` (Boolean), `operating_hours`.
* **Contact:** `phone_number` (WhatsApp link logic), `instagram`, `facebook`.
* **Monetization:** `is_featured` (Boolean) - Featured merchants appear at the top with a special badge.
* **Search:** `keywords` (Hidden text field for better search results).



---

### 3. Design System ("Malaysian Tech")

* **Aesthetic:** Friendly, rounded, vibrant. Inspired by Grab/Touch 'n Go/Shopee.
* **Typography:**
* Headings: **Space Grotesk** (Tech/Futuristic).
* Body: **Plus Jakarta Sans** (Modern/Legible).


* **Color Palette:**
* `brand`: `#0058ff` (Vibrant Blue).
* `accent`: `#ff9500` (Shopee Orange).
* `halal`: `#10b981` (Islamic Green - Critical for food).


* **UI Components:**
* **Cards:** Rounded corners (`rounded-3xl`), soft shadows, white background on light gray pattern.
* **Buttons:** WhatsApp Green for calls, Gradient for Instagram.
* **Badges:** Pills for "Halal", "Open", "Level 1".


* **Tone of Voice:** Localized English/Malay mix. Use emojis.
* *Example:* "Jom jalan-jalan!", "Alamak! Tak jumpa.", "Pilihan Ramai".



---

### 4. Current Implementation Status

* **Directory View:** A list view with search and category filters.
* **Infinite Scroll:** Implemented using HTMX. The main page includes a `partials/merchant_list.html`. When the "Muat Lagi" button is clicked, it swaps itself with the next page of results.
* **Search:** Server-side filtering using `Q` objects (searching name, description, keywords, lot number).

### 5. Coding Conventions

* **Views:** Function-based views (FBVs) preferred over CBVs for clarity in this MVP.
* **Tailwind:** Use utility classes directly in HTML. Do not create external CSS files unless absolutely necessary.
* **Partials:** Any section of the page that updates dynamically (like the merchant list) must live in a separate file inside `templates/venues/partials/`.
