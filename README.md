# <img width="600" height="327" alt="Dojo" src="https://github.com/user-attachments/assets/e477db25-db4f-45b8-8df3-3902b4b8e4a9" />
Open source club and class management platform. Manage members, attendance, billing, and documents. Self-hostable or run as a SaaS.

---

## What is Dojo?

Dojo is a free, open source platform for clubs, gyms, and coaching centres to manage everything in one place. Built to replace spreadsheets and disconnected tools, Dojo handles your members, classes, coaches, attendance, invoicing, and documents, with a parent-facing portal for payments and communication.

Dojo is sport and activity agnostic. Whether you run a judo club, a dance school, a boxing gym, or a music centre, Dojo adapts to your needs.

---

## Features

- **Multi-organisation** - run multiple clubs or centres from a single instance
- **Class management** - create classes, assign coaches, and enrol members
- **Role-based permissions** - org admins, class coaches, and members each see only what they should
- **Member profiles** - store personal details, emergency contacts, and custom fields you define
- **Attendance tracking** - log registers per session, view history per member
- **Billing and invoicing** - generate invoices, track payments, and integrate with Stripe
- **Parent portal** - tokenised links for parents to view attendance, invoices, and pay online
- **Document management** - send, sign, and store health and safety documents per member
- **Custom progression** - define your own grading or level system (belts, grades, stages, whatever fits your activity)
- **Self-hostable** - deploy on your own infrastructure and own your data

---

## Tech Stack

- **Backend** - Django (Python)
- **Database** - MySQL
- **Frontend** - Django Templates + HTMX
- **Payments** - Stripe and Stripe Connect
- **File Storage** - AWS S3 / Cloudflare R2
- **E-signatures** - DocuSeal

---

## Getting Started

Dojo runs in Docker. You'll need [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/) installed.

```bash
git clone https://github.com/M4ttW00d/dojo.git
cd dojo

# Copy the example env file and fill in your values
cp .env.example .env

# Start the database and web server
docker compose up -d

# Run database migrations
docker compose exec web python manage.py migrate

# Create your admin account
docker compose exec web python manage.py createsuperuser
```

Then open [http://localhost:8000/admin/](http://localhost:8000/admin/) to create your first organisation, then head to [http://localhost:8000/](http://localhost:8000/) to log in.

**Stopping Dojo:**

```bash
docker compose down
```

---

## Roadmap

- [x] Core multi-tenant architecture
- [x] Member management (add, edit, archive, guardian support, emergency contacts)
- [x] Class management with schedule builder
- [x] Attendance register
- [x] Staff and coach management
- [x] Custom fields per organisation
- [x] Audit logging
- [ ] Billing and invoicing
- [ ] Stripe payment integration
- [ ] Member tokenised portal
- [ ] Progression / grading system
- [ ] Document signing and storage
- [ ] Email notifications
- [ ] SaaS mode (Dojo Cloud)

---

## Contributing

Dojo is in early development. Contributions, ideas, and feedback are very welcome.

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes
4. Open a pull request

Please open an issue before starting any significant work so we can discuss it first.

---

## Licence

Dojo is licensed under the [GNU Affero General Public License v3.0](./LICENSE).

You are free to self-host and modify Dojo. If you run a modified version as a service over a network, you must make your modifications available under the same licence.

Commercial hosted plans are available at [getdojo.app](https://getdojo.app) (coming soon).
