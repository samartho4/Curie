# Demo day — setup & reset (do this right before you record)

Four things: **(1) reset the stage clean · (2) arrange two windows · (3) stage the long prompts so typing
never looks slow · (4) run the preflight.** ~15 minutes total.

---

## 1) Reset the stage — SAFE, ~5 min

The channel already has good six-month history + the canvases + the two workflows. We only need to (a) reset
the belief ledger so H2 is *Refuted* again (so the LoRA run flips it live), (b) clear today's test messages,
(c) drop the cold-open anchor at the bottom. **No mass-delete scripts — nothing destructive.**

**Recommended (keep everything, targeted):**

1. **Reset the ledger.** On the box: `python -m seed.seed_list` → copy the new `CURIE_LIST_ID` into `.env` →
   restart Curie (`sudo systemctl restart curie`) → re-share the List into `#experiments` if it isn't already.
   This makes **H2 = Refuted, 0-for-2** again — required, or the Claude-Science run has nothing to flip.
2. **Clear today's test messages** in `#experiments` (you're the owner, so hover → ⋮ → *Delete message*). Delete
   only the demo probes — keep the Anika/Marco/Priya history and the canvases:
   - every `@Curie …` message I posted while testing **and Curie's replies** to them,
   - the `📊 Run exp-301 …` and `📊 Run exp-314 …` messages (tagged *Sent using Claude*),
   - any Curie **"Heads up — your belief … changed"** alert from the tests.
   *(Rule of thumb: if it's from today and it's not Anika/Marco/Priya, delete it.)*
3. **Drop the cold-open anchor.** On the box: `python -m seed.run --cold-open` → posts Priya's *"did anyone try
   the full ESM fine-tune?"* → Marco's *"Anika left… good luck"* to the **bottom** of `#experiments`. That's the
   exact message the film scrolls up from.
4. **Verify:** type `@Curie where does the lab stand?` → H2 must read **Refuted**. Delete that check message after.

**Pristine alternative (only if you'd rather not delete anything):** archive the current `#experiments`, make a
fresh one, run the full `python -m seed.run`, point `CURIE_CHANNEL_ID` at the new channel, restart, and re-share
the canvases + re-feature the two workflows. Cleaner, but ~5 more steps and more that can go wrong — not worth it
this close to the deadline unless the targeted clean feels messy.

---

## 2) Two windows — the split-screen

- **Record in the Slack _desktop app_, not the browser** — no address bar/tabs in frame, and macOS Text
  Replacement (below) fires there. Log into the Anfinsen Lab workspace in the desktop app first.
- **Window A — Slack** (`#experiments`): full screen for the whole film *except* the 0:50 beat.
- **Window B — Claude Science** (`localhost:8765`): only needed at 0:50.
- **Easiest arrangement:** if you have a second monitor, put Claude Science there and just cut to it. Single
  screen? Grab **Rectangle** (free) — snap Slack to the left half, Claude Science to the right half with a hotkey,
  so CUT ① is one keypress. If even that's fussy: keep Slack full-frame, and at 0:50 **cut to Claude Science
  full-screen**, type the run prompt, show it post, cut back. The split looks better; the cut-to-full is safer.
- Before rolling: in Claude Science open the project that has the Slack connector on, and start a **fresh empty
  chat** so the run prompt is the first thing on screen.

---

## 3) Long prompts on Mac — so typing never looks slow

Two-part fix: **most prompts are now short enough to just type**, and the one long one you stage.

**A. macOS Text Replacement (built-in, instant, looks like fast typing).** System Settings → Keyboard → Text
Replacements → **+**. Add these (Replace → With = the full prompt from the cue sheet):
`;plan` · `;run` · `;standing` · `;stand` · `;why`. In the demo you type the short trigger, hit space, and the
full line appears. Works great in the **Slack desktop app**. ⚠️ It's flaky in browsers and probably won't fire
inside Claude Science — so use it for the four Slack prompts, not for `;run`.

**B. Clipboard manager for the Claude Science prompt (and as a backstop for all of them).** Install **Raycast**
or **Maccy** (both free) → enable clipboard history. Before recording, copy all five cue-sheet prompts once. At
each beat, pop the clipboard history hotkey, pick the prompt, paste (⌘V), Enter. Works everywhere — Slack web,
Slack desktop, and Claude Science. Pasting reads as normal; nobody blinks at a paste.

**Zero-install fallback:** a **Stickies** note off to the side with all five prompts — triple-click one, ⌘C, click
the composer, ⌘V, Enter.

> My pick: Text Replacement for the four Slack lines + clipboard for the Claude Science line. One less thing to
> think about mid-take.

---

## 4) The cue sheet — exact prompts, in order (copy these verbatim)

**#1 · The plan → collision** *(Slack `#experiments`; trigger `;plan`)*
```
@Curie planning a full fine-tune of ESM2-650M, lr 1e-4, batch 32, on the v1 split
```

**#2 · Claude Science → posts the run** *(Claude Science; clipboard-paste this one)*
```
Log our latest ESM run to the #experiments Slack channel. Post one message, exactly this format and nothing else: 📊 Run exp-314 | status: succeeded | outcome: LoRA head-scaling beat the full fine-tune baseline, +2.6% Spearman | params: model=ESM2-650M, method=LoRA, rank=16, split=v1
```

**#3 · Standing instruction** *(Slack; trigger `;standing`)*
```
@Curie from now on, check every plan in this channel before we run it — and every Monday, post which beliefs the week's evidence changed.
```

**#4 · The map** *(Slack; trigger `;stand`)*
```
@Curie where does the lab stand?
```

**#5 · The callback** *(Slack; trigger `;why`)*
```
@Curie why did we drop the full ESM fine-tune?
```

*(When you type `@Curie`, wait for the autocomplete and press Enter to turn it into a real mention — otherwise it's
plain text and the bot won't fire.)*

---

## 5) Preflight (60 seconds before the first take)
- [ ] Curie shows a **green dot** in the sidebar (bot is up after the restart).
- [ ] `#experiments` ends on the **cold-open anchor** (Priya → Marco), nothing test-y below it.
- [ ] `@Curie where does the lab stand?` → **H2 Refuted** (then delete that message).
- [ ] Claude Science: fresh chat, Slack connector on, `#experiments` = `C0BGT5XV082` (or your new channel).
- [ ] Text Replacement / clipboard loaded with all five prompts.
- [ ] Light theme, notifications off (Do Not Disturb), one silent dry-run end to end.
