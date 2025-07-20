import os
import sys

# === ENV CHECK ===
if not os.environ.get("TOGETHER_API_KEY"):
    print("❌ TOGETHER_API_KEY is not set.")
    sys.exit(1)

if not os.environ.get("GITHUB_TOKEN"):
    print("❌ GITHUB_TOKEN is not set.")
    sys.exit(1)

# === STEP 1: CREATE BRANCH ===
try:
    from create_branch import create_branch
    print("\n🚀 Step 1: Creating git branch...")
    create_branch()
except Exception as e:
    print("❌ Failed in create_branch.py:", e)
    sys.exit(1)

# === STEP 2: ANALYZE ERROR ===
try:
    from analyze_and_fix_together import analyze_latest_error
    print("\n🔍 Step 2: Analyzing latest error log...")
    analyze_latest_error()
except Exception as e:
    print("❌ Failed in analyze_and_fix_together.py:", e)
    sys.exit(1)

# === STEP 3: APPLY FIX ===
try:
    from apply_fix import analyze_and_patch
    print("\n🛠 Step 3: Applying patch...")
    analyze_and_patch()
except Exception as e:
    print("❌ Failed in apply_fix.py:", e)
    sys.exit(1)

# === STEP 4: COMMIT AND CREATE PR ===
try:
    from create_pr import commit_changes, create_pull_request, get_branch_name
    print("\n📤 Step 4: Committing and creating PR...")
    branch = get_branch_name()
    commit_changes()
    create_pull_request(branch)
except Exception as e:
    print("❌ Failed in create_pr.py:", e)
    sys.exit(1)