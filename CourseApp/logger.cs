using System;
using System.Diagnostics;
using System.IO;

public static class Logger
{
    public static void LogError(Exception ex)
    {
        // Get stack frame for the throwing method
        var st = new StackTrace(ex, true);
        // Take the first frame with a file name (most relevant)
        StackFrame frame = null;
        foreach (var f in st.GetFrames())
        {
            if (!string.IsNullOrEmpty(f.GetFileName()))
            {
                frame = f;
                break;
            }
        }

        string file = frame?.GetFileName() ?? "Unknown";
        string fileName = Path.GetFileName(file);
        int line = frame?.GetFileLineNumber() ?? 0;
        string timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
        string logLine = $"[ERROR] [{timestamp}] [{fileName}:{line}] {ex.GetType().Name}: {ex.Message}";

        // Log to file
        File.AppendAllText("errors.log", logLine + Environment.NewLine);
    }
}
