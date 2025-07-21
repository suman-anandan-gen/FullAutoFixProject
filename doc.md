# AutoFixProject: Complete System Documentation & Code Logic Walkthrough

---

## Overview

**AutoFixProject** is an automated pipeline that analyzes C# application logs, identifies errors, and leverages AI (via Together.ai) to generate code fixes, apply them, and create GitHub pull requests. This system integrates AI, Git, and CI/CD best practices for streamlined debugging.

---

## High-Level Workflow

1. **Branch Creation**: Creates a new Git branch.
2. **Error Analysis**: Parses logs and queries Together.ai for fixes.
3. **Patch Application**: Applies AI-generated fixes and backs up original files.
4. **Pull Request Creation**: Commits and pushes changes, then creates a PR.

---

## File-by-File Breakdown

### 1. `create_branch.py`

* **Purpose**: Creates a new git branch from `master` for fixes.
* **Key Logic**:

  * Uses `uuid.uuid4().hex[:6]` for a unique branch suffix.
  * Executes git commands: `checkout master`, `pull`, `checkout -b <branch>`.
  * Stores branch name in `.branch_name`.
* **Tools**:

  * `subprocess` for shell interaction.

---

### 2. `analyze_and_fix_together.py`

* **Purpose**: Reads logs, extracts code context, and queries Together.ai for fixes.
* **Key Components**:

#### a. Configuration

```python
SOURCE_DIR = "CourseApp"
LOG_FILE = os.path.join(SOURCE_DIR, "logs", "errors.log")
MODEL_NAME = "mistralai/Mixtral-8x7B-Instruct-v0.1"
```

#### b. Parsing Logs

```python
[ERROR] [TIMESTAMP] [FileName.cs:LineNumber] ExceptionType: Message
```

* Regex parses: `\[ERROR\] \[(.*?)\] \[(.*?):(\d+)\] (\w+): (.*)`

#### c. Code Context Extraction

```python
Get 10 lines of code around the line number (5 above and 5 below).
```

#### d. AI Call

* Sends context, exception type, and message to Together.ai.
* Expects **only code block** as response.
* Uses `together-python` SDK (`Together` class).

---

### 3. `apply_fix.py`

* **Purpose**: Applies AI-generated fixes to code files.
* **Differences from analyzer**:

  * Uses `requests` instead of `together-python`.

#### Key Steps:

1. **Log Parsing** (Same regex as before)
2. **Backup**:

   * Creates `CourseApp/backup/<filename>` before writing changes.
3. **Patch Application**:

   * Replaces `start:end` lines (surrounding context) with AI patch.
   * Ensures newline formatting for each inserted line.

---

### 4. `create_pr.py`

* **Purpose**: Stages, commits, pushes changes and creates a GitHub pull request.

#### a. GitHub Info

```python
REPO_OWNER = "Akshita-solanki"
REPO_NAME = "FullAutoFixProject"
```

#### b. Commit and Push

* Git operations via `subprocess`:

  * `git add .`
  * `git commit -m "fix: auto-applied patch from error logs"`
  * `git push --set-upstream origin <branch>`

#### c. PR Creation

* REST API call to GitHub:

  * Auth: `Authorization: token $GITHUB_TOKEN`
  * JSON body includes title, body, head, and base branch.

---

### 5. `run_all.py`

* **Purpose**: Orchestrator script.
* **Logic Flow**:

```python
check TOGETHER_API_KEY and GITHUB_TOKEN
|↳ create_branch()
|↳ analyze_all_errors()
|↳ analyze_and_patch_all()
|↳ commit_changes() + create_pull_request()
```

* Catches and reports errors in each step.

---

## Utility Functions & Techniques

### a. `extract_code_block(text)`

* Extracts code from markdown-style triple backtick blocks.
* If not found, filters plausible C# lines heuristically.

### b. `call_together_ai(...)`

* Creates a natural language prompt for the AI.
* Sends prompt and returns the response using either `requests` or SDK.

### c. `get_code_context_lines(...)`

* Fetches the surrounding lines around the error.

### d. `apply_patch(...)`

* Backs up the original file.
* Applies the patch by slicing and merging the original content.

---

## Tools & Dependencies

* **Python Libraries**:

  * `requests`, `re`, `subprocess`, `uuid`, `os`
* **AI Model**:

  * Provider: Together.ai
  * Model: `mistralai/Mixtral-8x7B-Instruct-v0.1`
* **GitHub**:

  * Token-based REST API auth
* **Environment Variables**:

  * `TOGETHER_API_KEY`, `GITHUB_TOKEN`

---

## Safety & Resilience

* ✅ Logs are filtered for unique entries.
* ✅ Files are backed up before modification.
* ✅ Uses separate git branches for all changes.
* ✅ Git operations are encapsulated with error handling.
* ✅ Pull requests isolate fixes for review.

---

## Example Run

```bash
export TOGETHER_API_KEY=...
export GITHUB_TOKEN=...
python run_all.py
```

---

## Final Thoughts

This system is designed for automation but also for safety. While Together.ai provides powerful code repair suggestions, this project ensures each step is controlled, auditable, and reversible.

---

**Maintainer Tip**: Review each PR manually before merging — AI is helpful, but not always perfect.
