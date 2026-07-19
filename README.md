# 🏪 Rental Management System
> **Odoo × KSV Hackathon Submission** — Built with Django 5, Bootstrap 5 & SQLite

A fully functional web-based Rental Management System that covers the complete rental lifecycle: quotations → pickup → return → invoice → security deposit & late-fee management.

---

## ✨ Features at a Glance

| Module | Key Functionality |
|---|---|
| **Dashboard** | KPI cards (revenue, active rentals, overdue), Chart.js graphs |
| **Products** | Catalog with categories, pricing tiers, stock tracking, search/filter |
| **Customers** | Customer profiles, rental history, payment tracking |
| **Quotations** | Draft → Confirmed quotation workflow, PDF-ready print view |
| **Rentals** | Cart → Order → Pickup Inspection → Return Inspection lifecycle |
| **Payments** | Security deposit collection, auto-refund/deduction on return |
| **Late Fees** | Grace period + hourly penalty auto-calculated on overdue returns |
| **Invoices** | Auto-generated per rental, browser print / PDF export |
| **Reports** | Revenue, rental volume, top products — tabular + chart-based |
| **Notifications** | In-app notification bell for lifecycle events |
| **Auth** | Session-based login/register, Admin vs Customer portal roles |

---

## 🗂 Project Structure

```
rental_system/
├── rental_system/          # Project config (settings, urls, wsgi)
├── accounts/               # Authentication, user profiles, context_processors
├── dashboard/              # Admin KPI dashboard with Chart.js analytics
├── products/               # Product catalog, categories, pricelists
├── customers/              # Customer CRM model and views
├── quotations/             # Quotation draft/confirm workflow
├── rentals/                # Core rental lifecycle: order, pickup, return
├── payments/               # Payment and deposit management
├── reports/                # Reports module with CSV/print export
├── notifications/          # In-app notification system
├── templates/              # All HTML templates (base.html + per-app)
├── static/                 # CSS, JS, images
├── media/                  # Uploaded product images
├── seed_data.py            # Demo data seeder
├── manage.py
└── db.sqlite3
```

---

## ⚙️ Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12 + Django 5.x |
| ORM | Django ORM (SQLite) |
| Frontend | HTML5 + CSS3 + Bootstrap 5 |
| Charts | Chart.js (CDN) |
| Icons | Font Awesome 6 (CDN) |
| Auth | Django built-in session authentication |
| Database | SQLite (local) |

---

## 🚀 Quick Start

### 1. Clone / Navigate to project

```bash
cd C:\Users\DELL\.gemini\antigravity\scratch\rental_system
```

### 2. Install dependencies

```bash
pip install django pillow
```

> **Python 3.12 required.** Django 5.2 is already listed in `requirements.txt`.

### 3. Apply migrations

```bash
python manage.py migrate
```

### 4. Seed demo data

```bash
python seed_data.py
```

This creates:
- 1 admin superuser: `admin` / `admin123`
- 5 demo customers with login credentials
- 8 rental products across 4 categories
- Historical rental orders, payments, invoices

### 5. Run the development server

```bash
python manage.py runserver
```

Open → [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🔑 Demo Credentials

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Customer 1 | `john_doe` | `password123` |
| Customer 2 | `jane_smith` | `password123` |
| Customer 3 | `robert_wilson` | `password123` |

---

## 🔄 Rental Lifecycle Flow

```
Customer Browses Catalog
        ↓
   Add to Cart
        ↓
   Checkout → RentalOrder Created (status: pending)
        ↓
   Security Deposit Collected
        ↓
   Admin: Pickup Inspection → Order confirmed (status: active)
        ↓
   Admin: Return Inspection
        ↓
   Late Fee Calculated (if overdue past grace period)
        ↓
   Deposit Refunded / Deducted
        ↓
   Invoice Generated (status: returned)
```

---

## 👤 User Roles

### Admin (Staff/Superuser)
- Full Dashboard with analytics
- Manage products, categories, customers
- Process pickup & return inspections
- View and generate reports
- Access Django Admin panel (`/admin/`)

### Customer (Portal User)
- Browse product catalog
- Place rental orders via cart
- View personal rental history and invoices
- Receive lifecycle notifications

---

## 🧪 Running Tests

```bash
python manage.py test rentals --verbosity=2
```

**Test Coverage:**
- `test_order_creation_saves_successfully` — DB write with correct defaults
- `test_pricing_multiplier` — Base price × rental period multiplier
- `test_late_fee_calculation_threshold` — Overdue hour-based penalty accumulation

---

## 📦 Requirements

```
Django==5.2
Pillow>=10.0
```

Install with:

```bash
pip install -r requirements.txt
```

---

## 📋 Known Limitations (Scope)

- No real payment gateway (simulated as "fully paid")
- Email notifications are placeholder (Django console backend)
- PDF export uses browser's native print dialog (`window.print()`)
- Single-branch, single-warehouse setup

---

## 📄 License

This project was developed as a submission for the **Odoo × KSV Hackathon**.  
For educational and demonstration purposes only.
