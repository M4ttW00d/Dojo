# Dojo - Project Context

This file exists to carry full project context between AI sessions. If you are a new Claude session, read this entire file before doing anything.

---

## What is Dojo?

Dojo is an open source, multi-tenant club and class management platform. It was conceived by the sole developer, who runs a judo club and wanted to replace a collection of Excel spreadsheets and a Wix website with a single, properly built system.

The name Dojo comes from the Japanese word 道場 (dōjō), meaning a martial arts training space. It was chosen because it fits the judo roots of the project, is broadly understood as a place of practice, is not locked to any one sport, and works naturally as a platform name.

The goal is for Dojo to be sport and activity agnostic. It should work equally well for a judo club, a dance school, a boxing gym, a music centre, or any organisation that runs classes with members, coaches, attendance, and billing.

---

## Licence

Dojo is licenced under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

This was a deliberate decision. AGPL means:
- Anyone can self-host and modify Dojo freely
- Anyone who runs a modified version as a network service (SaaS) must release their modifications under the same licence
- The original developer, as copyright holder, is not bound by the AGPL in the same way and can run a commercial hosted version (Dojo Cloud) and sell commercial licences to organisations who want to deploy privately without AGPL obligations

This is a dual licensing model, similar to GitLab, MongoDB, and Grafana.

---

## Deployment Model

Dojo is designed to support both:

1. **Self-hosted** - a club or centre deploys their own instance on their own infrastructure. They own their data entirely.
2. **SaaS (Dojo Cloud)** - the developer runs a hosted version that organisations can sign up to. This is a future commercial offering. No domain has been decided yet. Anyone interested in contributing or following the project should contact the developer via GitHub.

---

## Tech Stack

Every decision here was deliberate. Do not suggest changing the stack without good reason.

| Layer | Choice | Reason |
|---|---|---|
| **Framework** | Django (Python) | Developer has prior Django experience. Batteries included - auth, ORM, admin, migrations, file handling all built in. Fast to build with. |
| **Database** | MySQL | Developer preference. Django's ORM abstracts most of the difference from PostgreSQL. |
| **ORM** | Django's built-in ORM | Comes with Django, no separate choice needed. |
| **Frontend** | Django Templates + HTMX | Keeps things simple. No separate JS frontend, no npm build pipeline. HTMX adds interactivity where needed without a full SPA. |
| **Auth** | Django's built-in auth | Handles coach/admin login. Extended with custom permission logic for class-level access control. |
| **Payments** | Stripe + Stripe Connect | Stripe Connect allows each organisation to connect their own Stripe account. The platform can optionally take a fee in SaaS mode. PayPal was considered and rejected - Stripe has a better API, better webhooks, better UK support, and Stripe Connect is far superior to PayPal's equivalent. |
| **File storage** | AWS S3 or Cloudflare R2 | For storing signed health and safety documents per member. Not yet implemented. |
| **E-signatures** | DocuSeal (open source) | For sending, signing, and storing health and safety documents. Not yet implemented. |
| **Containerisation** | Docker + Docker Compose | Project runs in containers from day one. MySQL runs in a container, Django app runs in a container. This ensures self-hosting instructions in the README reflect the actual development environment. |
| **Hosting** | Not yet decided | Railway and Render are candidates. |

---

## Architecture Decisions

### Multi-tenancy

Everything in the database is scoped to an **Organisation**. A coach or admin at one organisation can never see or touch another organisation's data. This is enforced at the model level and must be enforced at the view level on every relevant endpoint.

Each organisation gets its own slug-based URL (e.g. `/org/bath-judo-club/`). In self-hosted mode, the single instance is effectively one organisation. In SaaS mode, multiple organisations share one instance.

### Roles and Permissions

There are four roles in the system:

1. **Super Admin** - platform level, only relevant in SaaS mode. This is the developer/operator.
2. **Org Admin** - full access within their organisation. Equivalent to a head coach or club secretary.
3. **Class Coach** - access only to the specific classes they are assigned to. Cannot view or modify members, attendance, or data for classes they are not assigned to. This was an explicit requirement - a gym might run multiple classes (e.g. judo and boxing) with different coaches, and coaches must be siloed to their own classes.
4. **Member/Parent** - no login. Access via tokenised links only (see below).

### Tokenised Parent/Member Portal

There is **no login system for parents or members**. This was a deliberate decision to keep things simple for a small club context (70 members was the original scale). A full login system for parents adds overhead (password resets, forgotten accounts, support burden) for something they might use a handful of times a year.

Instead, the system generates a **secure unique token per member**. A link containing this token is emailed to the parent or member. The link gives them access to:
- Their attendance history
- Their invoices
- A Stripe-powered payment page to pay outstanding invoices
- Their signed/unsigned health and safety documents

Stripe already supports this model natively with hosted payment links. The token-based route sits at something like `/p/<token>/`.

### Custom Fields

Member profiles are not hardcoded to any sport. An Org Admin can define **custom fields** for their organisation. For example:
- A judo club adds a "Belt Grade" field (select, with options White, Yellow, Orange, Green, Blue, Brown, Black)
- A dance school adds an "Exam Level" field
- A football club adds a "Position" field

Custom fields are stored as a `CustomField` model per organisation and values are stored as JSON on the member record or in a related `MemberFieldValue` table.

### Custom Progression System

Grading and progression is fully configurable per organisation. An Org Admin defines the stages of their progression system (e.g. White Belt, Yellow Belt, Orange Belt - or Grade 1, Grade 2, Grade 3). Each stage has a name and an order. Member progression is tracked as a separate record linking a member to a stage with a date achieved.

### Billing Model

The original use case was a UK school termly billing model (teaching only during term time, not during holidays). The developer's club is moving to a **monthly billing model** and Dojo should support this. Invoices are generated per member per billing period, tracked in the database, and payments are handled via Stripe. Stripe webhooks automatically update invoice status in the database when a payment is made.

In SaaS mode, each organisation connects their own Stripe account via Stripe Connect. The platform operator can optionally take a percentage fee.

---

## Database Schema

These are the core models. They have not been written in code yet - this is the planned schema.

```
Organisation
- id
- name
- slug
- settings (JSON)
- subscription_tier
- created_at

User (Django's built-in auth user)
- extended with a profile linking to OrganisationMember

OrganisationMember
- user (FK to User)
- organisation (FK to Organisation)
- role (choices: org_admin, coach)

Class
- id
- organisation (FK to Organisation)
- name
- description
- schedule

ClassCoach
- class (FK to Class)
- user (FK to User)
- Links coaches to specific classes they are permitted to manage

ClassMember
- class (FK to Class)
- member (FK to Member)
- Links members to the classes they are enrolled in

Member
- id
- organisation (FK to Organisation)
- name
- date_of_birth
- email
- phone
- emergency_contact_name
- emergency_contact_phone
- is_active
- token (unique, used for tokenised parent portal links)
- joined_date
- custom_field_values (JSON or related table)

Guardian
- id
- member (FK to Member)
- name
- email
- phone
- relationship

CustomField
- id
- organisation (FK to Organisation)
- name
- field_type (text, date, select, boolean)
- options (JSON, for select fields)
- order

ProgressionStage
- id
- organisation (FK to Organisation)
- name
- order

MemberProgression
- id
- member (FK to Member)
- stage (FK to ProgressionStage)
- achieved_date
- notes

Session
- id
- class (FK to Class)
- date
- notes

Attendance
- id
- session (FK to Session)
- member (FK to Member)
- present (boolean)

Invoice
- id
- organisation (FK to Organisation)
- member (FK to Member)
- amount
- period (e.g. "January 2026")
- due_date
- status (choices: unpaid, paid, overdue)
- created_at

Payment
- id
- invoice (FK to Invoice)
- stripe_payment_id
- amount
- paid_at

Document
- id
- organisation (FK to Organisation)
- member (FK to Member)
- type (e.g. health_and_safety, medical)
- signed (boolean)
- signed_at
- file_url (points to S3/R2)

Coach (handled via OrganisationMember and ClassCoach, not a separate model)
```

---

## Project Structure (Current State)

The project is in very early setup. Here is what exists so far:

- GitHub repo created, public, AGPL-3.0 licenced
- `README.md` - written and committed, includes logo, description, features, tech stack, roadmap, contributing guide, and licence section
- `Dockerfile` - written, uses `python:3.12-slim`, installs `gcc`, `default-libmysqlclient-dev`, `pkg-config`, copies `requirements.txt` and installs dependencies, copies project
- `docker-compose.yml` - written, defines two services: `db` (MySQL 8.0) and `web` (Django app). MySQL data is persisted via a named volume. Environment variables are read from `.env`.
- `.env` - created locally, not committed to git (in `.gitignore`)
- `.env.example` - committed, shows required variables without values
- `.gitignore` - includes `.env`, `__pycache__/`, `*.pyc`, `.DS_Store`, `venv/`
- `requirements.txt` - currently contains `django`, `mysqlclient`, `python-dotenv`
- Django project has been created via `django-admin startproject dojo .`
- `docker-compose up --build` has been run successfully. Both containers start. Django dev server is running on port 8000.
- `ALLOWED_HOSTS` needs to be updated in `dojo/settings.py` - currently `[]`, needs to be `['*']` for development

### What Has NOT Been Done Yet

- Django apps have not been created (e.g. `organisations`, `members`, `classes`, `billing`, `documents`)
- No models have been written
- No migrations have been run beyond Django's default ones
- `settings.py` has not been fully configured (database, static files, media files, environment variable loading)
- No views, URLs, or templates exist yet
- No admin configuration
- HTMX not yet installed or integrated
- Stripe not yet integrated
- DocuSeal not yet integrated
- S3/R2 not yet configured

---

## Suggested Next Steps (In Order)

1. Fix `ALLOWED_HOSTS` in `settings.py`
2. Configure `settings.py` to read from environment variables using `python-dotenv`
3. Configure the database in `settings.py` to use MySQL via environment variables
4. Run `python manage.py migrate` inside the Docker container to apply Django's default migrations
5. Create Django apps: start with `organisations` and `members`
6. Write models for `Organisation`, `OrganisationMember`, `Member`, `Guardian`, `CustomField`
7. Run migrations
8. Register models in Django admin
9. Create a superuser and verify admin works
10. Continue with `classes`, `billing`, `documents` apps

---

## Developer Notes

- The developer is working solo on this as a spare time project
- They are using PyCharm (JetBrains, licensed) on Linux
- They are comfortable with Django from prior experience
- They are using this project partly to improve their TypeScript skills - however the decision was made to use Django for this project for speed and familiarity. TypeScript is not in use here.
- The developer runs a judo club with approximately 70 members and 5 coaches/leadership team members. This is the primary real-world use case driving requirements.
- Claude Code is being used in the terminal to assist with development
- All decisions about stack, architecture, naming, and licencing documented above were made deliberately. Do not second-guess them without being asked.
