Got it ✅ I’ll prepare a clear **README.md** for your Streamlit project so anyone on your team (or even you later) can quickly set up and run the portal.

Here’s a good starting version:

---

# 🐉 Dragonboat Team Portal

A **Streamlit-based web portal** for managing team availability, biodata, training schedules, and activity tracking for your dragonboat team.

The portal provides **separate secure dashboards** for:

* **Junior Team**
* **Senior Team**
* **Pull Up Warrior**

Each portal has its own password and dedicated resources. Team members can log in, mark progress on required items, and their submissions will be logged with timestamps and names.

---

## ✨ Features

* 🔐 **Password-protected portals** (separate for Junior, Senior, and Pull Up Warrior).
* 📂 **Resource tracking** with links to Google Sheets/Forms.
* ⏰ **Deadlines & priority indicators** (red = high, yellow = medium, green = low).
* ✅ **Submission logging** with **name, role, item, status, timestamp, and notes**.
* 📊 **Recent activity dashboard** (shows last 10 updates per team).
* 📈 **Completion statistics** (per portal: total items, team completions, completion rate).
* 💾 **Local persistence** (`portal_data.json` file).
* 🔒 **Session timeout** (default: 1 hour).

---

## 🚀 Getting Started

### 1. Clone or Download

```bash
git clone https://github.com/your-repo/dragonboat-portal.git
cd dragonboat-portal
```

Or save `app.py` and `portal_data.json` in a folder.

---

### 2. Install Dependencies

Make sure you have Python 3.9+ installed. Then:

```bash
pip install streamlit pandas
```

---

### 3. Run the Portal

```bash
streamlit run app.py
```

This will start a local server at:

```
http://localhost:8501
```

---

### 4. Login Credentials

Default passwords (you can change in `Config.PASSWORDS` or via environment variables):

* Junior → `dragon_junior`
* Senior → `dragon_senior`
* Pull Up Warrior → `dragon_pullup`

---

### 5. Data Storage

All submissions are logged into a local file:

```
portal_data.json
```

Each entry includes:

* `timestamp`
* `name`
* `role` (Junior, Senior, Pull Up Warrior)
* `item` (resource name)
* `status` (Completed / In Progress)
* `notes`
* `session_id`

---

## 🛠 Configuration

You can customize the portal in `Config` class inside `app.py`:

* **Passwords** → set via environment variables or edit `Config.PASSWORDS`.
* **Session timeout** → adjust `SESSION_TIMEOUT`.
* **Resources** → update `Config.RESOURCES` with links, deadlines, descriptions, and priorities.

---

## 📊 Example Usage

1. Junior member logs in with password `dragon_junior`.
2. Opens **Junior Water Availability** tab.
3. Enters name → marks as **Completed**.
4. Submission is saved in `portal_data.json`.
5. Recent activity dashboard updates in real-time.

---

## 🔒 Security Notes

* Do not hardcode production passwords. Use environment variables:

  ```bash
  export JUNIOR_PASSWORD="your_secret"
  export SENIOR_PASSWORD="your_secret"
  export PULLUP_PASSWORD="your_secret"
  ```
* Deploy behind HTTPS if making public.

---

## 📌 Roadmap / Improvements

* Sync data to Google Sheets instead of local JSON.
* Admin dashboard with filters & search.
* Email/Slack notifications on submissions.
* User accounts instead of shared passwords.

---

👨‍💻 Built with ❤️ using [Streamlit](https://streamlit.io).

---

Would you like me to also include a **sample `portal_data.json`** structure in the README so your teammates know how the log looks without opening it?
