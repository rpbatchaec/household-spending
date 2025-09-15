# ChatGPT Branching Prompt Snippets
_Last updated: 2025-09-12_

## A) Start a New Troubleshooting Branch
```
We’re at Anchor <StepID> in the Master Runbook.
Create a troubleshooting branch named TB-<StepID>-A.
Context: Windows 11, PowerShell, Python 3.12, VS Code {version}.
Symptom: <one sentence>. Include hypotheses, a triage plan, and exit criteria.
Important: Don’t change steps outside this branch.
```

## B) While Troubleshooting — Keep the Cursor Visible
```
In each reply, include a single line at the end:
Cursor: <StepID> | Branch: TB-<StepID>-A
```

## C) Ask for a Minimal Repro
```
Give me the smallest set of commands to reproduce this error in a new temp folder,
with a fresh venv. Assume no admin rights. PowerShell only.
```

## D) Re-entry After Fix
```
Resume Master Runbook at <StepID>. Anchor TB-<StepID>-A is closed.
Show the next 2 steps with:
- Preconditions
- Exact commands
- Expected outputs
- Quick exit checks
```

## E) Snapshot Header (paste at top of any message when context is messy)
```
RUNBOOK: <project> | Cursor: <StepID> | Branch: TB-<StepID>-A | OS: Win11 | Shell: PS | Python: 3.12 | VS Code: <v> | Repo: <path>
```
