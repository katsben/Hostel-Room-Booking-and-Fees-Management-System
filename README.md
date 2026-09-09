# Hostel Room Booking and Fees Management System

A console-based Python system that replaces a paper ledger for tracking
hostel room bookings and student fee payments at a university hostel.
Built as a group assignment (Option 1).

## Features

- **Predefined hostel layout** — 3 blocks (A, B, C), each with a fixed
  number of rooms and a maximum capacity per room. A brief occupancy
  overview is printed on startup.
- **Registration & room allocation** — a student is only allocated to a
  room if space remains; a full room is rejected with a clear message,
  and occupancy is always derived live from student records so it never
  drifts out of sync.
- **Fee payment recording** — supports full or partial payments made over
  time for the same student; the outstanding balance is always correctly
  recomputed from the sum of every payment.
- **Search & reporting** — search by name (case-insensitive) or exact
  registration number; a full per-block occupancy report; a list of fee
  defaulters above a chosen balance threshold.
- **File persistence** — every student, room and payment record is saved
  to `hostel_data.json` and reloaded automatically on the next run. A
  missing or corrupted file is handled gracefully instead of crashing.
- **Menu-driven interface** — a single looping menu, validated throughout,
  designed to be usable by a non-programmer warden.

## Running it

```bash
python3 hostel_system.py
```

Requires only the Python standard library (no external dependencies).

## Project structure

```
hostel_system.py     # the entire application
hostel_data.json      # created automatically on first "Save and exit"
```

## Group members & responsibilities

| Member | Section |
|---|---|
| Member 1 - [KATEEA BERNARD] | Data setup & file persistence (Sections A, E) |
| Member 2 - [KYAGULANYI SHARIF] | Registration & room allocation (Section B) |
| Member 3 - [LUSWATA EDWIN] | Fee payment recording (Section C) |
| Member 4 - [MBABAZI BRIDGET] | Search & reporting (Section D) |
| All members | Menu integration & testing (Section F) |

See the group report for full design details, work division and
challenges overcome.
