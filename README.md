# How to run the Gold & Silver Recap Mailer

You don't run this on your own computer. You put three files in a GitHub repo,
add four secrets, and GitHub runs it automatically every weekday at open and
close. Total setup time: ~15–20 minutes, one time.

The files:
- `recap.py`            — the script
- `requirements.txt`    — its dependencies
- `recap.yml`           — the scheduler (goes at `.github/workflows/recap.yml`)

---

## Step 1 — Create a GitHub repo
1. Sign in (or sign up free) at github.com.
2. Click **New** (top-left, or github.com/new).
3. Name it anything (e.g. `gold-recap`). Private is fine. Click **Create repository**.

## Step 2 — Add the three files
Easiest way, no Git knowledge needed:
1. In the new repo, click **Add file ▸ Upload files**.
2. Upload `recap.py` and `requirements.txt`.
3. The workflow file must live in a specific folder. Click **Add file ▸ Create new file**,
   and in the filename box type exactly:  `.github/workflows/recap.yml`
   (typing the slashes creates the folders automatically). Paste in the contents
   of `recap.yml`, then **Commit**.

Your repo should now contain:
```
recap.py
requirements.txt
.github/workflows/recap.yml
```

## Step 3 — Get your Anthropic API key (the one paid piece)
1. Go to console.anthropic.com and sign in.
2. **Billing** ▸ add a payment method and a little credit ($5 lasts a long time —
   two short recaps a day cost pennies).
3. **API keys** ▸ **Create key** ▸ copy it. You'll paste it in Step 5.

## Step 4 — Get a Gmail App Password
A normal Gmail password won't work for sending — you need an App Password.
1. On the sending Google account, turn on **2-Step Verification**
   (Google Account ▸ Security). Required before App Passwords appear.
2. Go to **Google Account ▸ Security ▸ App passwords**.
3. Generate one (name it "recap"). Copy the 16-character code (no spaces).

## Step 5 — Add the four secrets to the repo
In your repo: **Settings ▸ Secrets and variables ▸ Actions ▸ New repository secret**.
Add these four, one at a time (name on the left, value on the right):

| Secret name          | Value                                            |
|----------------------|--------------------------------------------------|
| `ANTHROPIC_API_KEY`  | the key from Step 3                              |
| `GMAIL_ADDRESS`      | the sending Gmail (e.g. goldengamesllc@gmail.com)|
| `GMAIL_APP_PASSWORD` | the 16-char App Password from Step 4            |
| `RECIPIENT`          | where it's delivered (goldengamesllc@gmail.com)  |

(Sender and recipient can be the same address.)

## Step 6 — Test it right now
1. Click the **Actions** tab.
2. If prompted, click the button to enable workflows.
3. Pick **Gold & Silver Recap** on the left.
4. Click **Run workflow** ▸ choose `OPEN` or `CLOSE` ▸ **Run workflow**.
5. Wait ~1 minute, refresh. A green check = success. Check the inbox for the email.

## Step 7 — Nothing else
It now runs itself every weekday: ~8:30 AM ET (open) and ~5:00 PM ET (close).
You're done.

---

## If the test fails (red X)
Click the failed run ▸ the **send** job ▸ open the **Send recap** step. The last
line starting with `ERROR:` tells you what's wrong. Usual causes:
- **Authentication failed** → the Gmail value isn't an App Password, or 2FA isn't on.
- **401 / invalid x-api-key** → the Anthropic key is wrong or has no billing credit.
- **KeyError 'price'** → your metals API returns a different field name; open
  `recap.py` and adjust the field in `fetch_spot()` to match its docs.

## Good to know
- Cron times in `recap.yml` are set for Eastern *daylight* time. In winter they
  fire an hour earlier in ET unless you add 1 to each cron hour.
- GitHub pauses schedules after ~60 days of repo inactivity; any commit re-enables them.
- Scheduled runs can be delayed a few minutes under load — normal.

---

## Alternative: run it on your own computer
Only if you'd rather not use GitHub. Your machine must be awake at send times.
1. Install **Python 3.9+**.
2. In the folder with the files: `pip install -r requirements.txt`
3. Set the four values as environment variables, then run `python recap.py`
   (it auto-picks OPEN/CLOSE by time, or set `EDITION=OPEN`).
   - Mac/Linux test run:
     ```
     export ANTHROPIC_API_KEY=...   GMAIL_ADDRESS=...   GMAIL_APP_PASSWORD=...   RECIPIENT=goldengamesllc@gmail.com
     python recap.py
     ```
4. Schedule it with **cron** (Mac/Linux) or **Task Scheduler** (Windows) at your
   two times. This is more fiddly than GitHub and only runs when your computer is on.
