# Things to Remember

- Error log format:
  ```
  [ERROR] [YYYY-MM-DD HH:MM:SS] [FileName.cs:LineNumber] ExceptionType: Message
  ```

- AI used:
  - Provider: Together.ai
  - Model: `deepseek-coder-33b-instruct`

- Fixing logic:
  - Extracts 10 lines around the error
  - Sends it to AI to get a corrected block
  - Replaces the original block (with a `.bak` backup)

- GitHub:
  - Pull request is created on a new branch
  - Token must have `repo` access
