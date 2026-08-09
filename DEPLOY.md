# Deploying to Render

Gets the dashboard onto a URL your teammates can open, behind a shared password.

**Read the "Before you deploy" section first** — there are two things worth deciding
deliberately rather than discovering later.

---

## Before you deploy

**1. This puts real client data on the internet.**
The dashboard shows Cyber Rescue customer names, their SecurityScorecard ratings,
named decision-makers, and detected supplier relationships. The shared password keeps
it out of public view, but it's still one shared credential — anyone who has it, or who
it gets forwarded to, sees everything. Treat the password like the data behind it.

**2. Your API keys move onto Render.**
`API_KEY` reaches Cyber Rescue's real SSC portfolios. Render stores env vars encrypted
and they're standard practice, but it is one more place a live credential exists. If
that's not acceptable, deploy without `OPENAI_API_KEY` (research degrades to the
copy/paste flow) or don't deploy at all and share the repo instead.

**3. Free tier caveats.**
- The backend **sleeps after ~15 minutes idle**; the first request then takes ~30-60s.
  Open the URL a minute before demoing.
- The filesystem is **ephemeral** — researched news, imported decision-makers and
  actioned state are wiped on every redeploy and on wake from sleep. `customers.json`
  ships in the repo so the roster survives; caches don't. For a persistent deployment
  you'd add a Render Disk or move storage to a database.

---

## Steps

### 1. Push the repo to GitHub

Render deploys from a git remote. The repo has no remote yet:

```bash
git remote add origin https://github.com/YOUR-ORG/YOUR-REPO.git
git push -u origin master
```

Make it **private** — `customers.json` contains the customer roster.

`.env` is gitignored and will not be pushed. Confirm before pushing:

```bash
git ls-files | grep -c "\.env$"
```

That must print `0`.

### 2. Create the services

1. Sign in at [render.com](https://render.com) with GitHub.
2. **New → Blueprint**, pick the repo. Render reads `render.yaml` and proposes two
   services: `upsell-machine-api` and `upsell-machine`.
3. It will prompt for the secret env vars. Fill in:

| Variable | Service | Value |
|---|---|---|
| `API_KEY` | api | Your SecurityScorecard key |
| `OPENAI_API_KEY` | api | Optional — omit to disable automated research |
| `APP_PASSWORD` | api | The shared team password. **Set this** — no password means no gate |
| `ALLOWED_ORIGINS` | api | Leave blank for now (step 4) |
| `VITE_API_BASE_URL` | frontend | Leave blank for now (step 4) |

4. Apply. First build takes a few minutes.

### 3. Note the two URLs

Render assigns something like:
- API: `https://upsell-machine-api.onrender.com`
- Frontend: `https://upsell-machine.onrender.com`

### 4. Wire them together

Two env vars need each other's URLs, which is why they were left blank:

- On **api**, set `ALLOWED_ORIGINS` to the frontend URL
  (`https://upsell-machine.onrender.com`, no trailing slash)
- On **frontend**, set `VITE_API_BASE_URL` to the API URL

Redeploy both. The frontend one matters — `VITE_*` vars are baked in at build time, so
it needs a rebuild, not just a restart.

### 5. Check it

Open the frontend URL. You should get the password screen, and the dashboard after
signing in. If the board is empty, the backend is probably still waking — reload.

---

## Verifying the gate actually works

Confirm the API is not open, from any terminal:

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://upsell-machine-api.onrender.com/customers
```

Must print **401**. If it prints 200, `APP_PASSWORD` isn't set — fix that before
sharing the link.

---

## Sharing with the team

Send the frontend URL and the password **separately** (not in the same message), and
say plainly that it shows real customer data and shouldn't be forwarded outside the
team.

---

## Rotating the password

Change `APP_PASSWORD` on the api service and redeploy. Existing sessions stop working
within 12 hours, or immediately if you also change `APP_SECRET`.
