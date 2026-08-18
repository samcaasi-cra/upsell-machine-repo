# Deploying to PythonAnywhere (alternative to Render)

This is an alternative to [DEPLOY.md](DEPLOY.md) for teams that prefer or already use
PythonAnywhere. The two are independent — picking this one doesn't require touching
the Render setup, and vice versa.

**Read "Before you deploy" first.** PythonAnywhere's platform shape is different enough
from Render's that a few things are worth deciding deliberately.

---

## Before you deploy

**1. This needs a paid PythonAnywhere plan — free accounts can't reach the APIs this
app depends on.** Free PythonAnywhere accounts can only make outbound requests to a
small allowlist of well-known public APIs, over HTTP(S). SecurityScorecard's API and
OpenAI's API are not on that list, so on a free account the board would fail to load
entirely. Any paid tier (currently PythonAnywhere's "Developer" plan and up) removes
this restriction.

**2. One process serves both the API and the frontend.** PythonAnywhere's entry paid
tier gives you one web app. Render's setup is two separate services (API + static
site); here, the FastAPI backend serves the built React app directly instead, via an
opt-in flag (`SERVE_FRONTEND_DIST=1`, added specifically for this — see
`backend/app/main.py`). This also sidesteps a real platform gap: PythonAnywhere's
built-in static-file-mappings feature
[doesn't support ASGI sites](https://help.pythonanywhere.com/pages/ASGICommandLine/)
(only their older WSGI hosting), so serving the frontend from within the app is the
straightforward path, not a workaround.

**3. ASGI hosting is newer and CLI-driven.** PythonAnywhere's guided "create a web app"
wizard only offers WSGI frameworks. FastAPI is ASGI, so this uses their `pa website`
command-line tool instead — a few explicit commands rather than a form.

**4. This puts real client data on the internet**, same as the Render deployment. The
shared password keeps it out of public view, but treat the password like the data
behind it.

**5. Your API keys move onto PythonAnywhere.** `API_KEY` reaches real SSC portfolios.
If that's not acceptable, deploy without `OPENAI_API_KEY` (research degrades to the
copy/paste flow) or don't deploy at all.

**6. One thing that's actually easier here than Render's free tier: the filesystem
persists.** No sleep-on-idle, no wipe on redeploy — researched news, imported
decision-makers, and actioned state survive restarts. `customers.json` still ships in
the repo either way.

---

## Steps

### 1. Get a paid account and an API token

Sign up or upgrade at [pythonanywhere.com](https://www.pythonanywhere.com/pricing/).
Then, under **Account → API Token**, generate a token — the `pa` command-line tool
needs it to manage your web app from the console.

### 2. Push the repo to GitHub (if you haven't already)

Same prerequisite as the Render path — see [DEPLOY.md](DEPLOY.md#1-push-the-repo-to-github)
step 1. Skip this if it's already on GitHub from a Render deploy.

### 3. Clone the repo and set up the backend

Open a **Bash console** from the PythonAnywhere dashboard:

```bash
git clone https://github.com/YOUR-ORG/YOUR-REPO.git upsell_machine
cd upsell_machine/backend

mkvirtualenv upsell-machine --python=python3.12
pip install -r requirements.txt
pip install --upgrade pythonanywhere   # the `pa` CLI tool
```

(`mkvirtualenv` activates the new virtualenv automatically; reactivate it in future
sessions with `workon upsell-machine`.)

### 4. Create `backend/.env`

Same file, same variables as local development — see the README's
[Credentials](README.md#2-credentials) section. Add one PythonAnywhere-specific line:

```bash
API_KEY=your-securityscorecard-key
OPENAI_API_KEY=your-openai-key        # optional
APP_PASSWORD=your-shared-team-password
CSM_NAME=Alex

# Serve the built frontend from this same process (see "Before you deploy" above).
SERVE_FRONTEND_DIST=1
```

`ALLOWED_ORIGINS` isn't needed — frontend and backend now share one origin, so there's
no cross-origin request to allow.

### 5. Build the frontend and get it onto PythonAnywhere

`frontend/dist` is gitignored, and PythonAnywhere's preinstalled Node/npm tend to be
outdated (or missing) — simplest is to build it **locally**, on your own machine, then
upload the result:

```bash
# On your own machine:
cd frontend
VITE_API_BASE_URL="https://YOURUSERNAME.pythonanywhere.com" npm run build
```

Then upload the resulting `frontend/dist` folder to
`upsell_machine/frontend/dist` on PythonAnywhere — zip it and use the **Files** tab's
upload button (unzip with `unzip dist.zip` in a Bash console), or `scp`/`rsync` if your
plan includes SSH access.

Rebuild and re-upload any time the frontend changes — `VITE_*` values are baked in at
build time, so there's no way to change the API URL without a rebuild.

### 6. Create the ASGI website

Still in the Bash console, with the virtualenv active:

```bash
pa website create \
  --domain YOURUSERNAME.pythonanywhere.com \
  --command "/home/YOURUSERNAME/.virtualenvs/upsell-machine/bin/uvicorn --app-dir /home/YOURUSERNAME/upsell_machine/backend --uds \${DOMAIN_SOCKET} app.main:app"
```

Replace `YOURUSERNAME` in both places. This points uvicorn at `app.main:app` (same
ASGI app the Render deployment runs) listening on the Unix domain socket PythonAnywhere
provides, instead of a TCP port.

### 7. Check it

Open `https://YOURUSERNAME.pythonanywhere.com`. You should get the password screen,
then the dashboard after signing in.

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://YOURUSERNAME.pythonanywhere.com/customers
```

Must print **401** — same gate check as the Render path. If it prints 200,
`APP_PASSWORD` isn't set.

---

## After any code or `.env` change

Unlike `uvicorn --reload` locally or Render's auto-redeploy, PythonAnywhere's ASGI
hosting doesn't pick up changes on its own. After `git pull` or editing `.env`:

```bash
pa website reload --domain YOURUSERNAME.pythonanywhere.com
```

---

## Troubleshooting

**Board is empty / "Failed to load."** Check `API_KEY` is set in `backend/.env`, then
reload the website (see above — env changes don't apply until you do).

**Blank page / assets 404 at the root URL.** `SERVE_FRONTEND_DIST` isn't set, or
`frontend/dist` doesn't exist yet on the server. Confirm step 5 actually uploaded the
built files to `upsell_machine/frontend/dist`, then reload.

**Changes don't show up after `git pull`.** You forgot `pa website reload` — nothing
restarts automatically.

**`pa: command not found`.** The virtualenv the `pythonanywhere` package was installed
into isn't active — run `workon upsell-machine` first.

**Logs**, if something 500s: `/var/log/YOURUSERNAME.pythonanywhere.com.error.log`,
`.server.log`, and `.access.log`, viewable from the Files page or a console.

---

## Rotating the password

Change `APP_PASSWORD` in `backend/.env`, then `pa website reload`. Same session
behavior as Render — existing sessions stop working within 12 hours, or immediately if
`APP_SECRET` is also changed.

---

## Sharing with the team

Same guidance as [DEPLOY.md](DEPLOY.md#sharing-with-the-team) — send the URL and
password separately, and say plainly that it shows real customer data.
