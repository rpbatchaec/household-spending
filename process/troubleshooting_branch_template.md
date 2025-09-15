# Troubleshooting Branch — TB-<StepID>-<Letter>
_Last updated: 2025-09-12_

**Anchor Step**: <StepID> (from Master Runbook)  
**Symptom**: _(short sentence)_  
**Environment deltas**: _(e.g., corporate proxy, antivirus, different user profile)_

---

## 1) Evidence
- Exact error text (copy/paste)
- Screenshot(s)
- Last commands run
- Relevant logs (e.g., `~/.ipython`, VS Code Output: Jupyter, Python, Git)

## 2) Hypotheses (ordered)
1. 
2. 
3. 

## 3) Triage Plan (fastest first)
- [ ] Quick check 1 (1–2 min)
- [ ] Quick check 2
- [ ] Reproduce in minimal example
- [ ] Controlled test (new temp folder / fresh venv)

## 4) Fix Attempts (one at a time)
For each attempt, note:
- Command(s)/action(s) taken
- Outcome (success/fail/partial)
- New evidence

## 5) Exit Criteria (to close this branch)
- [ ] Anchor step reproduces expected behavior
- [ ] Regression checks (related steps still OK)
- [ ] Document permanent fix in Master Runbook (Evidence column)
- [ ] Close branch and **resume at <StepID>**

---

## Re-entry Prompt (copy-paste back to chat)
```
Resume Master Runbook at <StepID>. Anchor TB-<StepID>-<Letter> is closed.
Confirm the next two steps with preconditions, commands, and quick exit checks.
```

