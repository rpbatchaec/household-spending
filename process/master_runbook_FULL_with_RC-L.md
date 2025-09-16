# Master Runbook — VS Code + Python + GitHub + Jupyter
_Last updated: 2025-09-13_

---

## ⚠️ Important: Branches in This Runbook vs Git Branches

This runbook uses the term **"Troubleshooting Branch"** (e.g., TB-S04-A).  
These are **ChatGPT/log branches** — conversation forks to isolate troubleshooting context.

- ✅ You **stay on `main` in Git** the entire time unless you explicitly choose to make a Git branch for code changes.  
- ✅ Troubleshooting branches live only in ChatGPT and in these Markdown files.  
- ❌ They do **not** correspond to Git branches.  

Think of it like this:  
- **Git branches** → versions of code in your repo.  
- **Runbook branches** → versions of conversations in ChatGPT.

---

## Steps S01–S08

| # | StepID | Description | Expected Result | Evidence/Notes | ChatGPT URL Anchor | Status |
|---|--------|-------------|-----------------|----------------|--------------------|--------|
| 1 | **S01** | Verify Python & PATH | Python version prints | | (paste branch/thread URL here) | [ ] |
| 2 | **S02** | Create & activate venv | `( .venv )` shows in prompt | | (paste branch/thread URL here) | [ ] |
| 3 | **S03** | Install libs & Jupyter | Packages install cleanly | | (paste branch/thread URL here) | [ ] |
| 4 | **S04** | Register kernel | Kernel selectable in VS Code | | (paste branch/thread URL here) | [ ] |
| 5 | **S05** | Git init & nbstripout | .gitattributes updated | | (paste branch/thread URL here) | [ ] |
| 6 | **S06** | Add remote | origin listed | | (paste branch/thread URL here) | [ ] |
| 7 | **S07** | First commit & push | Branch visible on GitHub | | (paste branch/thread URL here) | [ ] |
| 8 | **S08** | Jupyter sanity test | Cell executes `print("ok")` | | (paste branch/thread URL here) | [ ] |

---

## Stabilization Track — Reintroducing Older Code Safely (ST-01 … ST-07)

### ST-01 — Create LKG worktree
```powershell
git worktree add ..\household-spending-LKG <commit>
```
Exit check: new folder exists and matches the chosen commit.

### ST-02 — Prove baseline & pin env
```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip freeze > requirements.txt
python - << 'PY'
print("env-ok")
PY
```

### ST-03 — Create stabilization branch from LKG
```powershell
git switch -c stabilize/2025-09-13 <commit>
```

### ST-04 — Quarantine ChatGPT drafts
```powershell
mkdir -p experiments\chatgpt_drop
git add experiments/chatgpt_drop
git commit -m "chore: add drafts (quarantined)"
```

### ST-05 — Reintroduce changes in tiny slices
```powershell
git diff -- experiments/chatgpt_drop\file.py src\file.py
git add src\file.py
git commit -m "feat: replace parse_txn() (passes smoke test)"
```

### ST-06 — Notebook hygiene (optional)
```powershell
pip install jupytext nbstripout
jupytext --set-formats "ipynb,py:percent" notebooks\*.ipynb
nbstripout --install
git add .gitattributes
git commit -m "chore: enable jupytext + nbstripout"
```

### ST-07 — Lock dependencies after green tests
```powershell
pip freeze > requirements.txt
git add requirements.txt
git commit -m "chore: lock deps after stabilization step"
```

### RC‑S — Stabilization checkpoint
- [ ] 2–3 green commits since ST‑04
- [ ] Smoke test + unit tests pass
- [ ] requirements.txt updated
- [ ] Optional tag: `v0.0.1-stabilized-2025-09-13`

---

### ChatGPT URL Anchors (Stabilization Steps)
- ST‑01: ___________________________
- ST‑02: ___________________________
- ST‑03: ___________________________
- ST‑04: ___________________________
- ST‑05: ___________________________
- ST‑06: ___________________________
- ST‑07: ___________________________

---

## Recovery Checkpoint — Local Changes (RC‑L)
_Last updated: 2025-09-13_

Use this when VS Code / Git shows **“Unstaged files detected”**, or when a commit/pull/rebase is blocked by local edits.

### RC‑L‑01: Inspect current state
```powershell
git status
git log --oneline -5
```

### RC‑L‑02: Safety snapshot
```powershell
git stash push -u -m "backup before recovery (RC-L)"
```

### RC‑L‑03: Choose your path
A) Keep everything  
```powershell
git add .
git commit -m "WIP: save local changes (RC-L)"
```
B) Keep only some files  
```powershell
git add path\to\file1.py
git commit -m "fix: selective commit (RC-L)"
```
C) Discard changes  
```powershell
git restore path\to\file
git restore .
```

### RC‑L‑04: If warning persists
Check `git log` and VS Code Source Control (ensure STAGED CHANGES is empty).

### RC‑L‑05: If a pull/rebase/merge is involved
```powershell
git pull --rebase
# or rebase/merge continue after resolving conflicts
```

### RC‑L‑06: Restore stashed work
```powershell
git stash list
git stash pop
```

### RC‑L‑07: Wrap up
- Run smoke/pytest tests
- Push if needed: `git push`
- Paste ChatGPT URL Anchor for this recovery here

# APPENDIX

# How to Anchor a ChatGPT Thread
_Last updated: 2025-09-16_

You can attach troubleshooting threads to your Master Runbook by saving their URLs.

## Steps

1. Open the ChatGPT conversation you want to link (e.g., a troubleshooting session for S05).
2. Copy the unique URL from the browser address bar. It will look like:

   ```
   https://chat.openai.com/c/abc123xyz
   ```

3. Paste this URL into the **ChatGPT URL Anchor** field of your Master Runbook.

   Example (Markdown table row):

   ```markdown
   | 5 | **S05** | Git init & nbstripout | .gitattributes updated | | [TB-S05-A](https://chat.openai.com/c/abc123xyz) | [ ] |
   ```

   → This creates a clickable link.

4. In the **fillable PDF**, paste the URL into the blank field for that step.

## Notes
- Keep the Master Runbook “clean” (happy path only).
- Spawn new troubleshooting threads for problems, and link them back here.
- Each step (S01–S08, ST-01…ST-07, RC-L…) has its own Anchor field.
