# Library Management System — Design Spec

## Overview

Small-scale library/lending management system for managing book inventory, member accounts, borrowing/returns with rolling loan periods, daily fines, and full reporting.

## Architecture

- **UI Framework**: PyQt6 ONLY (do NOT use PyQt5, do NOT mix versions)
- **Database**: SQLite with `database_init.sql` as single source of truth
- **Language**: Python 3.10+

```
┌─────────────────────────────────────┐
│           Main Window               │
│  (Tab-based: Catalog │ Members │   │
│   Checkouts │ Reports │ Settings)  │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│         Business Logic Layer        │
│  BookService │ MemberService │     │
│  CheckoutService │ ReportService   │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│           SQLite Database           │
│  books │ members │ checkouts │     │
│  fines │ settings                   │
└─────────────────────────────────────┘
```

## Data Model

> **CRITICAL**: This is the SINGLE SOURCE OF TRUTH for all table and column names.
> The `database_init.sql` file MUST be generated exactly from this section.
> All service SQL queries MUST use these exact column names — no synonyms, no abbreviations.

### books
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | |
| title | TEXT | NOT NULL | |
| author | TEXT | NOT NULL | |
| isbn | TEXT | | |
| publisher | TEXT | | |
| publication_year | INTEGER | | |
| category | TEXT | | NOT "genre" |
| total_copies | INTEGER | NOT NULL DEFAULT 1 | |
| available_copies | INTEGER | NOT NULL DEFAULT 1 | |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |

### members
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | NOT "member_id" |
| first_name | TEXT | NOT NULL | name is split into first+last |
| last_name | TEXT | NOT NULL | |
| email | TEXT | UNIQUE NOT NULL | |
| phone | TEXT | | |
| address | TEXT | | |
| membership_date | DATE | NOT NULL DEFAULT today | NOT "join_date" |
| is_suspended | INTEGER | NOT NULL DEFAULT 0 | 0/1 as boolean |
| suspension_reason | TEXT | | |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |

> **Common mistake**: Using `name` (single column) instead of `first_name` + `last_name`.
> Display full name as: `first_name || ' ' || last_name` in SQL.

### checkouts
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | |
| book_id | INTEGER | NOT NULL, FK books.id | |
| member_id | INTEGER | NOT NULL, FK members.id | |
| checkout_date | DATE | NOT NULL DEFAULT today | |
| due_date | DATE | NOT NULL | checkout_date + loan_period |
| return_date | DATE | | NULL if still active |
| status | TEXT | NOT NULL DEFAULT 'active' | 'active' / 'returned' / 'overdue' |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |

> **Common mistake**: Adding `fine_amount`/`is_fine_paid` columns to checkouts table.
> Fines are stored in the SEPARATE `fines` table, linked by `checkout_id`.

### fines
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | |
| checkout_id | INTEGER | NOT NULL, FK checkouts.id | |
| member_id | INTEGER | NOT NULL, FK members.id | |
| amount | REAL | NOT NULL | calculated on return |
| days_overdue | INTEGER | NOT NULL DEFAULT 0 | |
| is_paid | INTEGER | NOT NULL DEFAULT 0 | 0/1 as boolean |
| payment_date | DATE | | NULL until paid |
| payment_amount | REAL | DEFAULT 0 | |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |

### settings
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | |
| setting_key | TEXT | UNIQUE NOT NULL | NOT "key" |
| setting_value | TEXT | NOT NULL | NOT "value" |
| description | TEXT | | |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |

> **Common mistake**: Using `key`/`value` as column names. Must be `setting_key`/`setting_value`.

Default settings:
- `loan_period_days` = 14
- `daily_fine_rate` = 0.50
- `max_checkout_limit` = 5
- `library_name` = "Community Library"
- `currency_symbol` = "$"

## Conventions

### Task Ordering (tasks MUST follow this order)
1. **Phase 1 — Schema**: Create `database_init.sql` with ALL tables, indexes, triggers, views, default data
2. **Phase 2 — Data Layer**: Create `db_manager.py`, `models.py`, all `*_service.py` files
3. **Phase 3 — UI Views**: Create all `*_tab.py` / `*_view.py` / `*_form.py` / `*_dialog.py`
4. **Phase 4 — Shell**: Create `main_window.py`, `main.py`, `styles.qss`
5. **Phase 5 — Verify**: Run smoke test, fix errors

### Database Access Rules
- `execute_read()` returns `dict` (key = column name). Always use `row['column_name']`, **NEVER** `row[0]`
- Services are the ONLY layer that writes SQL. UI views call service methods, no raw SQL in UI code
- Each service receives `DatabaseManager` via constructor injection
- SQL column names MUST match Data Model section exactly

### Column Naming Rules
- Primary key: `id` (not `member_id`, `book_id` as self-PK)
- Foreign key: `{table_singular}_id` (e.g. `book_id` → `books.id`)
- Timestamps: `_at` suffix (`created_at`, `updated_at`)
- Booleans: `is_` prefix (`is_suspended`, `is_paid`), stored as INTEGER 0/1
- Dates: `_date` suffix (`checkout_date`, `due_date`)

### UI Framework Rules
- PyQt6 ONLY across ALL files — no mixed imports
- MainWindow creates `DatabaseManager` + all services, passes to views via constructor
- Each view/tab declares required services in `__init__` signature

## Features

### Catalog Tab
- Table view: Title, Author, Category, Available/Total Copies
- Filters: category dropdown, author search, availability toggle
- Add/Edit/Delete books with form dialog
- Manage copies (total vs available)

### Members Tab
- Table view: Name, Email, Phone, Status (Active/Suspended)
- Search by name or email
- Add/Edit/Delete members with form dialog
- Toggle suspension status

### Checkouts Tab
- **Check out**: Select book → Select member → auto-calculate due date from settings
- **Check in**: Select active checkout → mark returned → calculate fine if overdue
- **Overdue handling**: Fine = days_overdue × daily_fine_rate, stored in `fines` table
- View active checkouts with overdue highlighting
- Record fine payments (partial or full)

### Reports Tab
- Most borrowed books (date range filter)
- Active members with checkout counts
- Overdue rate statistics
- Fine revenue report (total collected vs outstanding)

### Settings Tab
- Loan period in days
- Daily fine rate
- Library name
- Max checkout limit

## Error Handling & Edge Cases

- **Book unavailable**: Prevent checkout if `available_copies = 0`; show error message
- **Suspended member**: Block checkout, show warning dialog
- **Overdue return**: Auto-calculate fine on return; allow partial or full payment recording
- **Duplicate ISBN**: Warn but allow
- **Delete book with active checkout**: Prevent deletion
- **Delete member with active checkout**: Prevent deletion
- **Empty required fields**: Validate on add/edit forms

## Acceptance Criteria

1. Can add, edit, delete books with all catalog fields
2. Can add, edit, delete members
3. Can check out a book (reduces `available_copies`)
4. Can check in a book (increases `available_copies`, calculates fine if overdue)
5. Suspended members cannot check out books
6. Filters work correctly on catalog view
7. Reports show accurate data for date ranges
8. Settings changes affect new checkouts immediately
9. Fines can be recorded as paid (partial or full)
10. Cannot delete books/members with active checkouts

## Smoke Test Checklist

- [ ] App starts without errors
- [ ] Add a book → book appears in catalog table
- [ ] Edit a book → changes reflected in table
- [ ] Delete a book → removed from table
- [ ] Add a member → member appears in members table
- [ ] Check out a book → `available_copies` decrements
- [ ] Check in a book → `available_copies` increments
- [ ] Overdue return creates a fine record in `fines` table
- [ ] Category/author filter works on catalog
- [ ] Settings page loads and saves correctly
