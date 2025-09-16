# 📝 Daily Git Workflow (Python + VS Code + pre-commit)

## 1. Prep
- ✅ Activate your venv  
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
- ✅ Make sure you’re on the right branch  
  ```powershell
  git status
  ```

## 2. Edit & Test
- 🖊️ Edit your code in VS Code.  
- ▶️ Run scripts or tests locally:  
  ```powershell
  pytest
  ```

## 3. Run Pre-commit
- 🧹 Check & auto-fix style/lint before staging:  
  ```powershell
  python -m pre_commit run --all-files
  ```
  - **nbstripout**: clears Jupyter outputs  
  - **black**: reformats Python files  
  - **ruff**: lints & fixes simple issues  

> If Black reformats files → re-`git add -A`, then re-run `pre-commit` to confirm all clean.

## 4. Stage Changes
```powershell
git add -A
git status   # confirm staged files
```

## 5. Commit
```powershell
git commit -m "feat: short but clear message here"
```

## 6. Sync With Remote
- Get the latest updates:
  ```powershell
  git pull --rebase origin main
  ```
- Resolve any conflicts if prompted (VS Code highlights them).  
- Then push:
  ```powershell
  git push -u origin main
  ```

## 7. Verify
- Check your repo on GitHub: file updates & commit history.  
- Celebrate with ☕ 🎉  

---

### 🔑 Quick Tips
- **Commit often**: small, focused commits are easier to debug and roll back.  
- **Branch for features**:  
  ```powershell
  git checkout -b feature/vendor-normalization
  ```
- **Don’t fight pre-commit**: let it format code; it’s saving you work.  
- **Conflicts**: if you see `<<<<<<< HEAD` markers, pause and resolve, then:  
  ```powershell
  git add <fixed files>
  git rebase --continue
  ```
