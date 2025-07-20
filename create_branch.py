# create_branch.py
import os
import subprocess
import uuid

BRANCH_NAME = f"auto-fix-{uuid.uuid4().hex[:6]}"

def run_git(cmds):
    result = subprocess.run(["git"] + cmds, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Git error: {result.stderr}")
        exit(1)
    return result.stdout.strip()

def create_branch():
    print(f"📦 Creating and switching to branch {BRANCH_NAME}...")
    run_git(["checkout", "master"])
    run_git(["pull", "origin", "master"])
    run_git(["checkout", "-b", BRANCH_NAME])
    print(f"✅ Branch {BRANCH_NAME} ready.")
    with open(".branch_name", "w") as f:
        f.write(BRANCH_NAME)

if __name__ == "__main__":
    create_branch()
