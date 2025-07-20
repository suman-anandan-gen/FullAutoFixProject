# AutoFixProject

## 🛠 Setup

1. Install dependencies:
   ```bash
   pip install requests
   ```

2. Set API keys:
   ```bash
   export TOGETHER_API_KEY=your_together_api_key
   export GITHUB_TOKEN=your_github_token
   ```

3. Run the pipeline:
   ```bash
   python analyze_and_fix_together.py   # Gets a fix
   python apply_fix.py                  # Applies it to code
   python create_pr.py                  # Creates git commit + PR
   ```

---

## 🧪 Sample Output
Logs are located in `CourseApp/logs/errors.log` and code lives in `CourseApp/`.

---

## 📦 Contents

- `CourseApp/`: Sample buggy C# project
- `logs/errors.log`: Mock errors
- Python scripts for fix, patch, and PR creation
