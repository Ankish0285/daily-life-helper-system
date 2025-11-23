import json
import os
from datetime import date, datetime

try:
    from getpass import getpass
except:
    def getpass(msg):
        return input(msg)

DB_USER_FILE = "users.json"
DB_DATA_FILE = "data.json"
DB_PASS_FILE = "secure_notes.json"


# ------------ JSON LOAD/SAVE ------------
def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default


def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except:
        print("Error saving file:", path)


# ------------ STORAGE INIT ------------
users = load_json(DB_USER_FILE, {})
data = load_json(DB_DATA_FILE, {})
secure_notes = load_json(DB_PASS_FILE, {})


# ------------ HELPERS ------------
def clear():
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
    except:
        pass


def read_float(prompt, default=None):
    while True:
        s = input(prompt).strip()
        if s == "" and default is not None:
            return default
        try:
            return float(s)
        except:
            print("Enter valid number.")


def read_int(prompt, default=None):
    while True:
        s = input(prompt).strip()
        if s == "" and default is not None:
            return default
        try:
            return int(s)
        except:
            print("Enter valid integer.")


def today_iso():
    return date.today().isoformat()


def ensure_user_folder(u):
    if u not in data:
        data[u] = {
            "entries": [],
            "expenses": [],
            "atm": {"balance": 0, "tx": []},
            "notes": []
        }


# ------------ LOGIN / REGISTER ------------
def register():
    name = input("Choose a username: ").strip()
    if not name:
        print("Invalid username.")
        return None

    if name not in users:
        pw = getpass("Set password: ").strip()
        users[name] = {"pass": pw, "created": datetime.now().isoformat()}
        save_json(DB_USER_FILE, users)
        print("Account created.")
    else:
        pw = getpass("Enter password: ").strip()
        if users[name]["pass"] != pw:
            print("Wrong password.")
            return None
        print("Login successful.")

    ensure_user_folder(name)
    save_json(DB_DATA_FILE, data)
    return name


# ------------ HEALTH ANALYSIS ------------
NEG = ['sad', 'depress', 'tired', 'angry', 'stressed', 'anxious', 'low']
POS = ['happy', 'good', 'great', 'fine', 'ok', 'relaxed', 'energetic']


def analyze_entry(e):
    score = 50
    alerts = []

    try:
        s = float(e["sleep"])
        if s < 5:
            score -= 20
            alerts.append("Very low sleep.")
        elif s < 7:
            score -= 5
        else:
            score += 5
    except:
        pass

    try:
        p = float(e["phone"])
        if p > 6:
            score -= 15
        elif p > 3:
            score -= 5
    except:
        pass

    try:
        w = int(e["water"])
        if w < 3:
            score -= 10
        else:
            score += 5
    except:
        pass

    try:
        st = int(e["steps"])
        if st < 2000:
            score -= 5
    except:
        pass

    mood = e["mood"].lower()
    if any(k in mood for k in NEG):
        score -= 10
    if any(k in mood for k in POS):
        score += 5

    score = max(0, min(100, score))
    e["score"] = score
    e["alert"] = " | ".join(alerts) if alerts else "All good."

    return e


# ------------ ADD ENTRY ------------
def add_daily_entry(u):
    ensure_user_folder(u)
    print("\nEnter today's health info:")

    ent = {
        "date": today_iso(),
        "sleep": read_float("Sleep hours: ", 0),
        "phone": read_float("Phone use hours: ", 0),
        "water": read_int("Glasses of water: ", 0),
        "steps": read_int("Steps walked: ", 0),
        "mood": input("Mood: ").strip(),
        "hr": input("Heart rate: ").strip()
    }

    ent = analyze_entry(ent)
    data[u]["entries"].append(ent)
    save_json(DB_DATA_FILE, data)

    print("\nSaved. Score:", ent["score"])
    print("Alert:", ent["alert"])


# ------------ HISTORY ------------
def show_history(u):
    lst = data[u]["entries"]
    if not lst:
        print("No entries yet.")
        return

    print("\nLast 10 entries:")
    for e in lst[-10:]:
        print(f"{e['date']} | score:{e['score']} | {e['alert']}")

    if input("Show full? (y/n): ").lower() == 'y':
        for e in lst:
            print("-" * 40)
            for k, v in e.items():
                print(k, ":", v)


# ------------ EXPENSE TRACKER ------------
def expenses_menu(u):
    while True:
        print("\n--- EXPENSES ---")
        print("1) Add expense")
        print("2) View summary")
        print("3) View all")
        print("4) Back")
        ch = input("Choice: ")

        if ch == "1":
            cat = input("Category: ") or "misc"
            amt = read_float("Amount: ")
            note = input("Note: ")
            data[u]["expenses"].append(
                {"date": today_iso(), "cat": cat, "amt": amt, "note": note}
            )
            save_json(DB_DATA_FILE, data)
            print("Saved.")
        elif ch == "2":
            ex = data[u]["expenses"]
            total = sum(x["amt"] for x in ex)
            print("Total:", total)
        elif ch == "3":
            for x in data[u]["expenses"]:
                print(x)
        elif ch == "4":
            return
        else:
            print("Invalid.")


# ------------ ATM SIMULATOR ------------
def atm_menu(u):
    while True:
        bal = data[u]["atm"]["balance"]
        print("\n--- ATM ---")
        print("Balance:", bal)
        print("1) Deposit")
        print("2) Withdraw")
        print("3) Transaction log")
        print("4) Set balance")
        print("5) Back")

        ch = input("Choice: ")

        if ch == "1":
            a = read_float("Deposit: ")
            bal += a
            data[u]["atm"]["balance"] = bal
            data[u]["atm"]["tx"].append(
                {"date": today_iso(), "type": "deposit", "amt": a}
            )
            save_json(DB_DATA_FILE, data)
            print("Done.")

        elif ch == "2":
            a = read_float("Withdraw: ")
            if a <= bal:
                bal -= a
                data[u]["atm"]["balance"] = bal
                data[u]["atm"]["tx"].append(
                    {"date": today_iso(), "type": "withdraw", "amt": a}
                )
                save_json(DB_DATA_FILE, data)
                print("Collect cash.")
            else:
                print("Insufficient funds.")

        elif ch == "3":
            for t in data[u]["atm"]["tx"]:
                print(t)

        elif ch == "4":
            a = read_float("Set new balance: ")
            data[u]["atm"]["balance"] = a
            save_json(DB_DATA_FILE, data)
            print("Updated.")

        elif ch == "5":
            return
        else:
            print("Invalid.")


# ------------ MINI TOOLS ------------
def calculator():
    print("\nCalculator (example: 12 + 3)")
    expr = input("Expr: ")
    try:
        val = eval(expr, {"__builtins__": None}, {})
        print("Result:", val)
    except Exception as e:
        print("Error:", e)


def converter():
    print("\n1) C→F  2) F→C  3) kg→g  4) g→kg  5) inch→cm")
    c = input("Choice: ")

    if c == "1":
        x = read_float("C: ")
        print("F:", x * 9/5 + 32)
    elif c == "2":
        x = read_float("F: ")
        print("C:", (x - 32) * 5/9)
    elif c == "3":
        x = read_float("kg: ")
        print("g:", x * 1000)
    elif c == "4":
        x = read_float("g: ")
        print("kg:", x / 1000)
    elif c == "5":
        x = read_float("inch: ")
        print("cm:", x * 2.54)
    else:
        print("Invalid.")


def tools_menu():
    while True:
        print("\n--- TOOLS ---")
        print("1) Calculator")
        print("2) Converter")
        print("3) Back")
        ch = input("Choice: ")

        if ch == "1":
            calculator()
        elif ch == "2":
            converter()
        elif ch == "3":
            return
        else:
            print("Invalid.")


# ------------ SECURE NOTES ------------
def secure_notes_menu(u):
    while True:
        print("\n--- SECURE NOTES ---")
        print("1) Add note")
        print("2) View notes")
        print("3) Delete note")
        print("4) Back")
        ch = input("Choice: ")

        if ch == "1":
            key = getpass("Master key: ").strip()
            if not key:
                print("Required.")
                continue
            label = input("Label: ")
            secret = getpass("Secret: ")

            secure_notes.setdefault(u, []).append({
                "label": label,
                "secret": secret,
                "created": datetime.now().isoformat(),
                "key_hint": key[:2]
            })
            save_json(DB_PASS_FILE, secure_notes)
            print("Saved.")

        elif ch == "2":
            key = getpass("Enter key: ").strip()
            notes = secure_notes.get(u, [])
            for r in notes:
                if r["key_hint"] == key[:2]:
                    print(r["label"], ":", r["secret"])
                else:
                    print(r["label"], ":", "(locked)")

        elif ch == "3":
            notes = secure_notes.get(u, [])
            if not notes:
                print("None.")
                continue

            for i, r in enumerate(notes, 1):
                print(i, ")", r["label"])

            sel = read_int("Delete number: ", 0)
            if 1 <= sel <= len(notes):
                notes.pop(sel - 1)
                save_json(DB_PASS_FILE, secure_notes)
                print("Deleted.")
            else:
                print("Invalid.")

        elif ch == "4":
            return
        else:
            print("Invalid.")


# ------------ EXPORT REPORT ------------
def export_report(u):
    fname = f"report_{u}_{today_iso()}.txt"
    with open(fname, "w", encoding="utf-8") as f:
        f.write(f"Report for {u} - {datetime.now().isoformat()}\n\n")
        f.write("Entries:\n")
        for e in data[u]["entries"]:
            f.write(str(e) + "\n")
        f.write("\nExpenses:\n")
        for x in data[u]["expenses"]:
            f.write(str(x) + "\n")
        f.write("\nATM:\n")
        for t in data[u]["atm"]["tx"]:
            f.write(str(t) + "\n")

    print("Saved:", fname)


# ------------ MAIN LOOP ------------
def main_loop():
    user = None

    while True:
        clear()
        print("==== Daily Helper ====")

        if not user:
            print("1) Login/Register  2) Exit")
            cmd = input("Choice: ")

            if cmd == "1":
                user = register()
            elif cmd == "2":
                print("Goodbye.")
                break
            else:
                print("Invalid.")
            input("Press Enter...")
            continue

        print(f"\nUser: {user}\n")
        print("1) Add daily entry")
        print("2) Show history")
        print("3) Expenses")
        print("4) ATM")
        print("5) Tools")
        print("6) Secure notes")
        print("7) Export report")
        print("8) Logout")

        ch = input("Choice: ")

        if ch == "1":
            add_daily_entry(user)
        elif ch == "2":
            show_history(user)
        elif ch == "3":
            expenses_menu(user)
        elif ch == "4":
            atm_menu(user)
        elif ch == "5":
            tools_menu()
        elif ch == "6":
            secure_notes_menu(user)
        elif ch == "7":
            export_report(user)
        elif ch == "8":
            user = None
            print("Logged out.")
        else:
            print("Invalid.")

        input("Press Enter...")


if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\nExiting.")
