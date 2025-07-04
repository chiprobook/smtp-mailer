# ✉️ Whaya Mail

![Python](https://img.shields.io/badge/Language-Python-blue)
![Flet](https://img.shields.io/badge/UI-Flet-orange)
![Status](https://img.shields.io/badge/Status-In_Progress-yellow)
![License](https://img.shields.io/badge/License-MIT-green)
![Database](https://img.shields.io/badge/SQLite-ShowMeGrace.db-lightgrey)

---

![Whaya Mail Splash](whayamail.png)

## 📘 Overview

**Whaya Mail** is a fully functional desktop-style email client built with [Flet](https://flet.dev/) and Python. It enables users to log in, manage accounts, compose, save drafts, send messages, and organize inboxes across multiple providers. UI transitions are smooth, interactions are intuitive, and everything lives inside a modular, interactive experience.

---

## 🚀 Features

- 👤 **User Authentication** — Login & Signup with SQLite-backed credentials
- 📩 **Email Composition** — Recipient type (To, Cc, Bcc), Reply-To, subject, body & attachments
- 🗂️ **Mail Views** — Inbox, Drafts, Sent, Outbox — all accessible via NavigationRail
- 💾 **Draft Saving & Editing** — Store unfinished messages and load them back seamlessly
- 🔄 **Forwarding & Replying** — Built-in controls to forward or reply to messages
- 🔍 **Search & Filter** — Dynamic mail filtering for inbox, draft, sent, and outbox
- ✅ **Select & Delete** — Bulk select, toggle visibility, and delete mail across views
- 🔐 **Custom SMTP Setup** — Choose from presets or add custom server/port configurations
- 🔔 **Feedback Overlays** — Live loading spinners & messageboxes guide interaction
- 📊 **Email Plan Limits** — Apply basic/standard/advanced limits via code

---

## 🧰 Technologies

| Layer         | Stack                                                  |
|---------------|--------------------------------------------------------|
| UI            | [Flet](https://flet.dev/)                              |
| Backend       | Python 3                                               |
| Email Logic   | `smtplib`, `email.mime`, `imaplib`                     |
| Database      | `sqlite3` – local database (`ShowMeGrace.db`)          |
| Components    | `Container`, `Row`, `Column`, `ListView`, `Dropdown`  |

---

## 📦 Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/chiprobook/flutter-smtp-mailer.git
   cd flutter-smtp-mailer

2. Install dependencies:
   bash
   pip install flet
 
3. Run the app:
   bash
   python main.py
   On first launch, the app auto-creates ShowMeGrace.db with the required Grace table.

🔐 User Auth Flow

signup() creates a new user entry in SQLite
login() verifies existing credentials
Feedback messages appear on screen using overlay popups
Credentials are stored locally — future extensions can enable secure hashing or encrypted vaults

💌 Compose & Send

Customizable SMTP server and port
Attachment support (pick_files → MIMEBase)
Recipients handled via dropdown (To, Cc, Bcc)
Validation checks prevent empty field sends
Emails saved to Sent or Outbox based on success

📥 Inbox & Mail Views

Each mail category features:
List rendering with search filter
Select All and bulk delete logic
Individual message view with Forward / Reply options
Dynamic layouts adjusting to NavigationRail width

📝 Draft Logic

Save draft via popup prompt
Load and edit saved drafts with full field population
Stored in self.drafts and self.draft_save_emails

📤 Sent & Outbox

Sent messages tracked in self.sent_emails
Failed sends saved to self.outbox_emails
Both views feature filters, selectors, detail view, and delete logic

📊 Mail Limits

Supports basic tiered email plans:
python
def get_limit(self):
    if self.plan == 'basic': return 50
    elif self.plan == 'standard': return 100
    elif self.plan == 'advanced': return 150
    elif self.plan == 'free': return 10
Future integration can tie this to account storage or paid tiers.

📜 License
Licensed under the MIT License. See LICENSE for terms.

👨‍💻 Author
Created with ❤️ by Reginald 📫 Contact: chiprobook@hotmail.com

🎯 What's Next?

🔐 OAuth integration per email provider (Gmail, Outlook, Yahoo, etc.)
📥 Real IMAP inbox syncing & parsing
🛡️ Secure password hashing
🌍 Multiple language or theme support
📤 Scheduled email logic
