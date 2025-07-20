using System;
using System.Linq;
using System.Collections.Generic;

public class CourseService
{
    public void Divide()
    {
        int a = 10;
        int b = 0;
        int result = a / b; // DivideByZeroException
    }

    public void NullCheck()
    {
        string instructor = null;
        Console.WriteLine(instructor.Length); // NullReferenceException
    }

    public void FindCourse()
    {
        List<string> courses = new List<string>();
        var course = courses.First(c => c == "Math"); // InvalidOperationException
    }
}
