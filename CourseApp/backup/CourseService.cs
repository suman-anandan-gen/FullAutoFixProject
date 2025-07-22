using System;
using System.Linq;
using System.Collections.Generic;

public class CourseService
{
    public void Divide()
    {
        try
        {
            int a = 10;
            int b = 0;
            int result = a / b; // DivideByZeroException
        }
        catch (Exception ex)
        {
            Logger.LogError(ex);
            throw;
        }
    }

public void NullCheck()
{
try
{
string instructor = null;
if(instructor != null)
{
Console.WriteLine(instructor.Length);
}
}
catch (Exception ex)
{
Logger.LogError(ex);
throw;
}
}

    public void FindCourse()
    {
        try
        {
            List<string> courses = new List<string>();
            var course = courses.First(c => c == "Math"); // InvalidOperationException
        }
        catch (Exception ex)
        {
            Logger.LogError(ex);
            throw;
        }
    }
}
