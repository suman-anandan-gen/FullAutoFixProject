using System;

public class CourseController
{
    public void HandleRequest()
    {
        string[] courses = new string[2];
        Console.WriteLine(courses[5]); // IndexOutOfRangeException
    }
}
