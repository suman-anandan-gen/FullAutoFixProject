import os
import re
import requests
import urllib3

# Disable SSL warnings when verify=False is used
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SOURCE_DIR = "CourseApp"
LOG_FILE = os.path.join(SOURCE_DIR, "logs", "errors.log")
MAX_CONTEXT_LINES = 20
MODEL_NAME = "mistralai/Mixtral-8x7B-Instruct-v0.1"
TOGETHER_API_KEY = "7f41b8a3d7078c14e032cee4f5e7b99b4d1ba5417c3145b1a91edbc48e0218ed"

HEADERS = {
    "Authorization": f"Bearer {TOGETHER_API_KEY}",
    "Content-Type": "application/json"
}

def extract_code_block(text):
    """Extract C# code from AI response, handling various formats"""
    # Remove markdown code block delimiters
    text = re.sub(r'```\s*$', '', text)
    
    lines = text.strip().split('\n')
    method_lines = []
    in_method = False
    brace_count = 0
    
    for line in lines:
        # Skip explanatory text before method
        if not in_method and not re.match(r'\s*(public|private|protected|internal)', line.strip()):
            continue
            
        # Found method signature
        if re.match(r'\s*(public|private|protected|internal)\s+.*\w+\s*\([^)]*\)', line):
            in_method = True
            method_lines.append(line)
            # Count braces on signature line
            brace_count += line.count('{')
            brace_count -= line.count('}')
            continue
            
        if in_method:
            method_lines.append(line)
            brace_count += line.count('{')
            brace_count -= line.count('}')
            
            # Method complete when braces are balanced
            if brace_count == 0 and len(method_lines) > 1:
                break
    
    if method_lines:
        result = '\n'.join(method_lines)
        if validate_method_code(result):
            return result
    
    # Fallback: return cleaned text
    return text.strip()

def validate_method_code(code):
    """Validate that extracted code is a complete C# method"""
    if not code or not code.strip():
        return False
    
    lines = [line.strip() for line in code.split('\n') if line.strip()]
    if not lines:
        return False
    
    # Check for method signature
    first_line = lines[0]
    if not re.match(r'\s*(public|private|protected|internal)\s+.*\w+\s*\([^)]*\)', first_line):
        return False
    
    # Check for balanced braces
    if not has_balanced_braces(code):
        return False
    
    # Ensure method has opening brace
    if '{' not in code:
        return False
    
    return True

def call_together_ai(file_path, method_context, error_line, exception, message):
    """Call Together AI with improved prompt for better results"""
    prompt = f"""Fix this C# method that has a {exception} error at line {error_line}.

Error message: {message}

Current broken method:
{method_context}

Requirements:
1. Return ONLY the complete fixed method with proper C# syntax
2. Include full method signature with access modifiers
3. Include all opening and closing braces
4. Fix the specific error: {exception}
5. Keep the try-catch structure intact
6. Ensure proper exception handling

Return the complete fixed method:"""

    response = requests.post(
        "https://api.together.xyz/v1/chat/completions",
        headers=HEADERS,
        json={
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": "You are a C# expert. Return only valid, complete C# method code without markdown or explanations."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 1024,
        },
        timeout=60,
        verify=False
    )
    
    response.raise_for_status()
    raw = response.json()["choices"][0]["message"]["content"].strip()
    return extract_code_block(raw)

def parse_log_line(line):
    """Parse error log line to extract file, line number, exception type and message"""
    match = re.match(r'\[ERROR\] \[(.*?)\] \[(.*?):(\d+)\] (\w+): (.*)', line)
    if match:
        _, file_name, line_num, ex_type, message = match.groups()
        return file_name, int(line_num), ex_type, message
    return None

def find_method_bounds(lines, error_line_num):
    """Find start and end bounds of method containing the error line"""
    method_start = None
    method_end = None
    
    # Scan upwards for method signature
    for idx in range(error_line_num - 1, -1, -1):
        line = lines[idx].strip()
        # Look for method signature pattern
        if re.match(r'^\s*(public|private|protected|internal)?\s*[\w<>,\[\]\s]*\s+\w+\s*\([^)]*\)', line):
            method_start = idx
            break
        # Also check previous line + opening brace pattern
        if line == '{' and idx > 0:
            prev_line = lines[idx-1].strip()
            if re.match(r'^\s*(public|private|protected|internal)?\s*[\w<>,\[\]\s]*\s+\w+\s*\([^)]*\)', prev_line):
                method_start = idx - 1
                break
    
    if method_start is None:
        return None, None
    
    # Find method end by counting braces
    brace_count = 0
    found_opening = False
    
    for idx in range(method_start, len(lines)):
        line = lines[idx]
        open_count = line.count('{')
        close_count = line.count('}')
        
        if open_count > 0:
            found_opening = True
        
        brace_count += open_count - close_count
        
        # Method ends when braces are balanced and we found at least one opening
        if found_opening and brace_count == 0 and idx > method_start:
            method_end = idx
            break
    
    if method_end is None:
        return None, None
    
    return method_start, method_end + 1

def has_balanced_braces(code):
    """Check if code has balanced braces"""
    stack = []
    for char in code:
        if char == '{':
            stack.append('{')
        elif char == '}':
            if not stack:
                return False
            stack.pop()
    return len(stack) == 0

def apply_method_patch(file_path, method_start, method_end, fixed_method_code):
    """Apply the AI-generated patch to the source file"""
    # Create backup directory
    backup_dir = os.path.join(SOURCE_DIR, "backup")
    os.makedirs(backup_dir, exist_ok=True)
    
    # Read original file
    with open(file_path, "r") as f:
        lines = f.readlines()
    
    # Create backup
    backup_path = os.path.join(backup_dir, os.path.basename(file_path))
    with open(backup_path, "w") as f:
        f.writelines(lines)
    
    # Prepare fixed method lines
    fixed_lines = []
    for line in fixed_method_code.strip().splitlines():
        if not line.endswith('\n'):
            line += '\n'
        fixed_lines.append(line)
    
    # Validate brace balance before applying patch
    remaining_code = "".join(lines[:method_start] + lines[method_end:])
    if not has_balanced_braces(remaining_code):
        print(f"❗ Original code has unbalanced braces in {file_path}")
        return False
    
    # Check if patch maintains balance
    patched_code = "".join(lines[:method_start] + fixed_lines + lines[method_end:])
    if not has_balanced_braces(patched_code):
        print(f"❗ Patch would create unbalanced braces in {file_path}")
        return False
    
    # Apply the patch
    updated_lines = lines[:method_start] + fixed_lines + lines[method_end:]
    
    try:
        with open(file_path, "w") as f:
            f.writelines(updated_lines)
        print(f"✅ Successfully patched {file_path} (backup: {backup_path})")
        return True
    except Exception as e:
        print(f"❌ Failed to write patched file {file_path}: {e}")
        return False

def analyze_and_patch_all():
    """Main function to analyze error logs and apply AI-generated patches"""
    if not os.path.exists(LOG_FILE):
        print(f"❌ Log file not found: {LOG_FILE}")
        return

    # Read and parse error log
    with open(LOG_FILE, "r") as f:
        log_lines = f.readlines()

    error_entries = []
    seen_errors = set()

    for line in log_lines:
        line = line.strip()
        if line and "[ERROR]" in line:
            result = parse_log_line(line)
            if result:
                file_name, line_num, exception, message = result
                error_key = f"{file_name}:{line_num}:{exception}"
                if error_key not in seen_errors:
                    error_entries.append((file_name, line_num, exception, message))
                    seen_errors.add(error_key)

    if not error_entries:
        print("✅ No valid error logs found to process.")
        return

    print(f"📋 Found {len(error_entries)} unique errors to fix\n")

    # Process each error
    for index, (file_name, line_num, exception, message) in enumerate(error_entries, 1):
        print(f"\n🔍 [{index}/{len(error_entries)}] Processing {file_name}:{line_num}")
        print(f"Exception: {exception}")
        print(f"Message: {message}")
        
        source_path = os.path.join(SOURCE_DIR, file_name)
        
        if not os.path.exists(source_path):
            print(f"❌ Source file not found: {source_path}")
            continue

        # Read source file
        try:
            with open(source_path, "r") as f:
                source_lines = f.readlines()
        except Exception as e:
            print(f"❌ Failed to read {source_path}: {e}")
            continue

        # Find method boundaries
        method_start, method_end = find_method_bounds(source_lines, line_num)
        
        if method_start is None or method_end is None:
            print(f"❗ Could not locate method bounds for error at line {line_num}")
            continue

        # Extract method context
        method_context = "".join(source_lines[method_start:method_end])
        print(f"📄 Method context extracted ({method_end - method_start} lines)")

        # Get AI fix
        try:
            print("🤖 Requesting AI fix...")
            ai_patch = call_together_ai(file_name, method_context, line_num, exception, message)
            
            if not ai_patch or not validate_method_code(ai_patch):
                print(f"❌ AI generated invalid or empty method code")
                continue
                
            print("✅ AI generated valid fix:")
            print("-" * 40)
            print(ai_patch)
            print("-" * 40)
            
            # Apply the patch
            print("🔧 Applying patch...")
            success = apply_method_patch(source_path, method_start, method_end, ai_patch)
            
            if success:
                print("✅ Patch applied successfully!")
            else:
                print("❌ Patch application failed")
                
        except Exception as e:
            print(f"❌ Error during AI processing: {e}")
            continue
        
        print("\n" + "=" * 60)

    print(f"\n🎉 Processing complete! Check the backup directory for original files.")

if __name__ == "__main__":
    if not TOGETHER_API_KEY:
        print("❌ TOGETHER_API_KEY environment variable not set.")
        print("Please set it with: export TOGETHER_API_KEY='your-api-key'")
    else:
        analyze_and_patch_all()
