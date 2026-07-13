# Curie — pre-submission audit & punch-list

_Deep pass on Sat Jul 11, after the full live demo drive. Deadline: Mon Jul 13, 5pm PDT (organizers reward submitting by Sun Jul 12)._

## Fixed this session (in code, in your folder)

1. **False collision on a novel plan** — search was retrieving your own just-posted `@Prior` message and colliding the plan with itself. Fixed with a timestamp self-exclusion in RTS (`tools/rts.py`), wired through both the mention and ambient paths, plus a near-verbatim self-text backstop in `pipeline/preflight.py`. Proven live: same GAT plan went ⚠️ → ✅.
2. **Lab Record "access denied"** — the bot-owned List wasn't shared to humans, so "Open the Lab Record" dead-ended. Added `scripts/share_list.py` (uses `slackLists.access.set`, verified against Slack docs) and patched `seed/seed_list.py` to share on create.
3. **Dead "Messages" tab (agent DM loop)** — `message.im` had no handler, so DMing the agent did nothing (the whole point of the agent messaging experience). Added a DM handler in `listeners/app_mention.py` that runs the same streamed preflight. Verified it registers alongside the ambient channel handler with no conflict.
4. **"0 collisions caught" stuck at zero** — `note_collision()` was defined but never called. Now wired from the verdict path (fires on a collision verdict).
5. **`@Curie` startup string** — `app.py` told users to mention `@Curie`, which doesn't resolve. Corrected to `@Prior`.

All modules compile; calibration guard still passes all four cases; all five listeners register on a real Bolt app.

## Two things to run now (on the Mac)

- **Share the List (one-off, no restart):** `python -m scripts.share_list` — grants #experiments read access so judges can open the native List.
- **Restart the app once** to load fixes #3–#5: Ctrl+C, then `python app.py`. (The self-collision fix from earlier is already live; these new ones need the restart.)

## Still to do — prioritized

### P0 — Deployment durability (the #1 risk to winning)
The product is done; if it's **down when judges test it (Jul 14–Aug 6), none of it counts.** Socket Mode needs an always-on process (no public URL, so Vercel/serverless is a poor fit). Two zero-budget options:

- **A. Harden the Mac (fastest, already running here):** `caffeinate -dimsu` so it never sleeps + a launchd `KeepAlive` plist so it auto-restarts on crash/reboot + a daily "alive ✅" self-ping DM so silence tells you within hours. None of these three exist yet — I can build them.
- **B. Free always-on VM (most robust):** Oracle Cloud Always Free or GCP e2-micro (card-verify, $0 charged), or your existing AWS free-tier EC2. Needs the code on the box (git push/clone) + a systemd unit. Higher setup, survives your laptop being closed.

_Recommendation: do **A** today to be safe immediately, add **B** by Sunday if you want laptop-independence._

### P1 — Submission assets
- **~3-min video** — every beat now works on screen; storyboard in `demo-and-submission.md`. I can drive the exact demo sequence in Chrome while you record.
- **Devpost writeup** — first paragraph + impact, in your voice (draft in `demo-and-submission.md`).
- **Architecture diagram** — Mermaid → PNG, upload via Devpost's file field.

### P2 — Judge access & cleanup
- Invite `slackhack@salesforce.com` + `testing@devpost.com` as **Members** of the sandbox; add them to #experiments (so the shared List resolves for them).
- Make the demo video public; test in an incognito window.
- Optional channel tidy: the live drive left two identical GAT plans (the 4:03 false-collision thread can be deleted so the recording is clean) and a few test mentions. The bot can't delete your messages — hover → ⋯ → Delete.

## Known-and-accepted (not bugs)
- **"Re-run setup" button** is an honest stub that points to `python -m seed.seed_list` (setup is a one-time dev step, not automated from the button). Fine to leave.
- **Bot user is permanently "Prior"** — by design (dual-name: product = Curie, agent = @Prior, Bubble Lab pattern). Not a wart.
