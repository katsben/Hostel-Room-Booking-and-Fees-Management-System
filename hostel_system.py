"""
Hostel Room Booking and Fees Management System
------------------------------------------------
A console-based Python programme that replaces a paper ledger for tracking
hostel room bookings and student fee payments.

Group members and primary responsibilities (see group report for detail):
    Member 1 - Data setup & file persistence     (Section A, Section E)
    Member 2 - Registration & room allocation     (Section B)
    Member 3 - Fee payment recording              (Section C)
    Member 4 - Search & reporting                 (Section D)
    All members - Menu integration & testing      (Section F)

All data is persisted to hostel_data.json so records survive between runs.
"""

import json
import os

DATA_FILE = "hostel_data.json"

# A student who has not made any part-payment yet still owes the full fee
# recorded at registration, so no separate "unpaid" flag is needed - the
# balance is always computed as total_fee - sum(payments).
DEFAULT_TOTAL_FEE = 500_000  # UGX, used as a suggested default at registration


# =============================================================================
# SECTION A - Data setup                                    (Member 1)
# =============================================================================
def get_initial_blocks():
    """
    Return the fixed hostel layout: a dictionary mapping each block name to
    a dictionary of {room_number: capacity}. This structure is predefined
    in code (as required) rather than entered by the warden, since the
    physical building layout does not change at runtime.
    """
    return {
        "Block A": {101: 2, 102: 2, 103: 3, 104: 3},
        "Block B": {201: 2, 202: 2, 203: 4, 204: 1},
        "Block C": {301: 1, 302: 2, 303: 2, 304: 3, 305: 2},
    }


def get_room_occupants(students, block, room):
    """Return a list of reg_no for every student currently assigned to this room."""
    return [
        reg_no for reg_no, s in students.items()
        if s["block"] == block and s["room"] == room
    ]


def get_room_occupancy_count(students, block, room):
    """Return how many students currently occupy the given room."""
    return len(get_room_occupants(students, block, room))


def print_occupancy_overview(blocks, students):
    """Print a brief one-line-per-block occupancy summary when the programme starts."""
    print("\n--- Hostel Occupancy Overview ---")
    for block, rooms in blocks.items():
        total_capacity = sum(rooms.values())
        total_occupied = sum(
            get_room_occupancy_count(students, block, room) for room in rooms
        )
        vacancies = total_capacity - total_occupied
        print(f"{block:<10} | {len(rooms)} rooms | "
              f"Capacity: {total_capacity:<3} | Occupied: {total_occupied:<3} | "
              f"Vacant: {vacancies}")
    print()


# =============================================================================
# Shared input-validation helpers
# =============================================================================
def get_non_empty_string(prompt):
    """Repeatedly prompt until the user enters some non-blank text."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("  -> This field cannot be empty. Please try again.")


def get_positive_number(prompt):
    """Repeatedly prompt until a valid positive number is entered."""
    while True:
        raw_value = input(prompt).strip()
        try:
            value = float(raw_value)
        except ValueError:
            print("  -> That doesn't look like a number. Please try again.")
            continue
        if value <= 0:
            print("  -> Value must be greater than zero. Please try again.")
            continue
        return value


def get_non_negative_number(prompt):
    """Repeatedly prompt until a valid number >= 0 is entered (0 itself is allowed)."""
    while True:
        raw_value = input(prompt).strip()
        try:
            value = float(raw_value)
        except ValueError:
            print("  -> That doesn't look like a number. Please try again.")
            continue
        if value < 0:
            print("  -> Value cannot be negative. Please try again.")
            continue
        return value


def get_valid_block(prompt, blocks):
    """Repeatedly prompt until the user names an existing hostel block."""
    while True:
        block = input(prompt).strip()
        # Case-insensitive match against the predefined block names.
        for existing in blocks:
            if existing.lower() == block.lower():
                return existing
        print(f"  -> No such block. Available blocks: {', '.join(blocks.keys())}")


def get_valid_room(prompt, blocks, block):
    """Repeatedly prompt until the user names an existing room number in `block`."""
    while True:
        raw_room = input(prompt).strip()
        try:
            room = int(raw_room)
        except ValueError:
            print("  -> Room number must be a whole number. Please try again.")
            continue
        if room not in blocks[block]:
            print(f"  -> Room {room} does not exist in {block}. "
                  f"Valid rooms: {sorted(blocks[block].keys())}")
            continue
        return room


# =============================================================================
# SECTION B - Student registration and room allocation       (Member 2)
# =============================================================================
def register_student(students, blocks):
    """
    Register a new student and allocate them to a specified room, but only
    if space remains in it. Rejects the allocation with a clear explanation
    if the room is already full, and updates occupancy automatically since
    occupancy is always derived from the `students` dictionary.
    """
    print("\n--- Register New Student ---")
    reg_no = get_non_empty_string("Registration number: ").upper()

    if reg_no in students:
        print(f"  -> A student with registration number '{reg_no}' is already "
              f"registered ({students[reg_no]['name']}). Registration cancelled.\n")
        return

    name = get_non_empty_string("Full name: ")
    block = get_valid_block(f"Block ({', '.join(blocks.keys())}): ", blocks)
    room = get_valid_room("Room number: ", blocks, block)

    capacity = blocks[block][room]
    current_occupancy = get_room_occupancy_count(students, block, room)

    if current_occupancy >= capacity:
        print(f"  -> Allocation REJECTED: Room {room} in {block} is already full "
              f"({current_occupancy}/{capacity} occupants). Please choose another "
              f"room.\n")
        return

    fee_prompt = f"Total hostel fee due (UGX) [default {DEFAULT_TOTAL_FEE}]: "
    raw_fee = input(fee_prompt).strip()
    if raw_fee == "":
        total_fee = DEFAULT_TOTAL_FEE
    else:
        try:
            total_fee = float(raw_fee)
            if total_fee <= 0:
                print("  -> Fee must be positive; using default instead.")
                total_fee = DEFAULT_TOTAL_FEE
        except ValueError:
            print("  -> Invalid amount; using default instead.")
            total_fee = DEFAULT_TOTAL_FEE

    students[reg_no] = {
        "name": name,
        "block": block,
        "room": room,
        "total_fee": total_fee,
        "payments": [],  # list of individual payment amounts
    }

    new_occupancy = current_occupancy + 1
    print(f"  -> Allocation SUCCESSFUL: {name} ({reg_no}) assigned to {block} "
          f"Room {room} ({new_occupancy}/{capacity} occupants). "
          f"Fee due: UGX {total_fee:,.0f}\n")


# =============================================================================
# SECTION C - Fee payment recording                          (Member 3)
# =============================================================================
def get_total_paid(student):
    """Sum every payment made so far by this student."""
    return sum(student["payments"])


def get_balance(student):
    """Outstanding balance = total fee due minus everything paid so far (never negative)."""
    return max(0.0, student["total_fee"] - get_total_paid(student))


def record_payment(students):
    """
    Record a full or partial fee payment against a student's account and
    correctly update their outstanding balance. Supports multiple payments
    made over time for the same student.
    """
    print("\n--- Record Fee Payment ---")
    reg_no = get_non_empty_string("Student registration number: ").upper()

    if reg_no not in students:
        print(f"  -> No student found with registration number '{reg_no}'.\n")
        return

    student = students[reg_no]
    balance_before = get_balance(student)
    print(f"  Student: {student['name']}  |  Current balance: UGX {balance_before:,.0f}")

    if balance_before == 0:
        print("  -> This student has already fully paid their fees. "
              "No further payment is required.\n")
        return

    amount = get_positive_number("Payment amount (UGX): ")

    student["payments"].append(amount)
    balance_after = get_balance(student)

    print(f"  -> Payment of UGX {amount:,.0f} recorded for {student['name']}.")
    if amount > balance_before:
        overpaid = amount - balance_before
        print(f"  -> Note: this payment exceeds the outstanding balance by "
              f"UGX {overpaid:,.0f} (balance is now UGX 0).")
    print(f"  -> New outstanding balance: UGX {balance_after:,.0f}\n")


# =============================================================================
# SECTION D - Search and reporting                           (Member 4)
# =============================================================================
def search_student(students):
    """
    Search for a student by exact registration number or by a case-insensitive
    substring match on their name, and display their full record.
    """
    print("\n--- Search for a Student ---")
    query = get_non_empty_string("Enter name or registration number: ").strip()
    query_lower = query.lower()

    matches = []
    for reg_no, s in students.items():
        if reg_no.lower() == query_lower or query_lower in s["name"].lower():
            matches.append((reg_no, s))

    if not matches:
        print(f"No student found matching '{query}'.\n")
        return

    print(f"\n{'Reg. No.':<12}{'Name':<20}{'Block':<10}{'Room':<7}"
          f"{'Fee Due':<12}{'Paid':<12}{'Balance':<12}")
    print("-" * 85)
    for reg_no, s in matches:
        paid = get_total_paid(s)
        balance = get_balance(s)
        print(f"{reg_no:<12}{s['name']:<20}{s['block']:<10}{s['room']:<7}"
              f"{s['total_fee']:<12,.0f}{paid:<12,.0f}{balance:<12,.0f}")
    print()


def generate_block_report(blocks, students, block_name=None):
    """
    Print a full occupancy report. If `block_name` is None, report on every
    block; otherwise report on just that one block.
    """
    blocks_to_report = [block_name] if block_name else list(blocks.keys())

    for block in blocks_to_report:
        print(f"\n--- Occupancy Report: {block} ---")
        print(f"{'Room':<8}{'Capacity':<10}{'Occupied':<10}{'Vacant':<8}Occupants")
        print("-" * 70)

        block_capacity = 0
        block_occupied = 0
        for room, capacity in sorted(blocks[block].items()):
            occupants = get_room_occupants(students, block, room)
            occupied = len(occupants)
            vacant = capacity - occupied
            names = ", ".join(students[r]["name"] for r in occupants) or "-"
            print(f"{room:<8}{capacity:<10}{occupied:<10}{vacant:<8}{names}")
            block_capacity += capacity
            block_occupied += occupied

        print("-" * 70)
        print(f"Block total: {block_occupied}/{block_capacity} occupied "
              f"({block_capacity - block_occupied} vacant)\n")


def list_fee_defaulters(students, threshold):
    """
    Print every student whose outstanding balance is strictly above
    `threshold`, sorted from the highest balance to the lowest. Shows a
    clear message if there are no defaulters rather than an empty table.
    """
    defaulters = [
        (reg_no, s, get_balance(s))
        for reg_no, s in students.items()
        if get_balance(s) > threshold
    ]

    print(f"\n--- Fee Defaulters (balance above UGX {threshold:,.0f}) ---")
    if not defaulters:
        print("No fee defaulters found above this threshold. Good news!\n")
        return

    defaulters.sort(key=lambda item: item[2], reverse=True)

    print(f"{'Reg. No.':<12}{'Name':<20}{'Block':<10}{'Room':<7}{'Balance':<12}")
    print("-" * 65)
    for reg_no, s, balance in defaulters:
        print(f"{reg_no:<12}{s['name']:<20}{s['block']:<10}{s['room']:<7}{balance:<12,.0f}")
    print()


# =============================================================================
# SECTION E - File persistence                                (Member 1)
# =============================================================================
def save_data(blocks, students):
    """Save the current blocks layout and every student record to DATA_FILE."""
    payload = {"blocks": blocks, "students": students}
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        # `default=str` is a safety net in case any non-JSON-native type
        # sneaks in; keys must be strings for JSON, so room numbers below
        # are converted back to int on load.
        json.dump(payload, f, indent=2)
    print(f"All records saved to '{DATA_FILE}'.")


def load_data():
    """
    Load blocks and students from DATA_FILE if it exists and is valid.
    Falls back to the predefined block layout and an empty student list if
    the file is missing (first run) or damaged/corrupted, so the programme
    never crashes on startup.
    """
    default_blocks = get_initial_blocks()

    if not os.path.exists(DATA_FILE):
        # Expected on the very first run - nothing to load yet.
        print(f"No existing data file found ('{DATA_FILE}'). "
              f"Starting fresh with the predefined hostel layout.\n")
        return default_blocks, {}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            payload = json.load(f)

        # JSON object keys are always strings, so room numbers need
        # converting back from "101" to 101 for each block.
        raw_blocks = payload.get("blocks", default_blocks)
        blocks = {
            block: {int(room): capacity for room, capacity in rooms.items()}
            for block, rooms in raw_blocks.items()
        }

        students = payload.get("students", {})
        # Room numbers inside each student record must also be int, and
        # payments must be a list, to behave correctly with the rest of
        # the programme's logic.
        for s in students.values():
            s["room"] = int(s["room"])
            s["payments"] = list(s.get("payments", []))

        return blocks, students

    except (json.JSONDecodeError, KeyError, ValueError, TypeError, OSError) as error:
        # The file exists but is unreadable/corrupted - warn the warden and
        # start fresh rather than crashing the whole programme.
        print(f"Warning: '{DATA_FILE}' could not be read ({error}). "
              f"Starting with a fresh, empty dataset instead.\n")
        return default_blocks, {}


# =============================================================================
# SECTION F - Menu-driven driver programme                    (All members)
# =============================================================================
def display_menu():
    """Print the main menu in plain language a non-programmer warden can follow."""
    print("=" * 46)
    print("   HOSTEL ROOM BOOKING & FEES MANAGEMENT")
    print("=" * 46)
    print("1. Register a new student & allocate a room")
    print("2. Record a fee payment")
    print("3. Search for a student")
    print("4. View occupancy report (all blocks or one)")
    print("5. View fee defaulters")
    print("6. Save and exit")


def handle_occupancy_report_menu(blocks, students):
    """Sub-menu: let the warden view all blocks at once or pick a single block."""
    choice = input("View (A)ll blocks or (S)ingle block? [A/S]: ").strip().lower()
    if choice == "s":
        block = get_valid_block(f"Which block? ({', '.join(blocks.keys())}): ", blocks)
        generate_block_report(blocks, students, block)
    else:
        generate_block_report(blocks, students)


def handle_defaulters_menu(students):
    """Sub-menu: ask for the balance threshold before listing defaulters."""
    threshold = get_non_negative_number("Show students owing more than (UGX): ")
    list_fee_defaulters(students, threshold)


def main():
    """
    Programme entry point. Loads existing data, prints the startup occupancy
    overview, then loops through the menu until the warden chooses to save
    and exit. Every menu choice is validated so the programme never crashes
    on unexpected input.
    """
    blocks, students = load_data()
    print_occupancy_overview(blocks, students)

    while True:
        display_menu()
        choice = input("Enter your choice (1-6): ").strip()

        if choice == "1":
            register_student(students, blocks)
        elif choice == "2":
            record_payment(students)
        elif choice == "3":
            search_student(students)
        elif choice == "4":
            handle_occupancy_report_menu(blocks, students)
        elif choice == "5":
            handle_defaulters_menu(students)
        elif choice == "6":
            save_data(blocks, students)
            print("Goodbye! Records are safely saved for next time.")
            break
        else:
            print("Invalid choice. Please enter a number from 1 to 6.\n")


if __name__ == "__main__":
    main()
