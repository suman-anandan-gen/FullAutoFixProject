using System;

public class CourseController
{
public void HandleRequest()
{
    try
    {
        string[] courses = new string[2];
        if (courses.Length > 5)
        {
            Console.WriteLine(courses[5]);
        }
        else
        {
            Console.WriteLine("There are only " + courses.Length + " elements in the array.");
        }
    }
    catch (Exception ex)
    {
        Logger.LogError(ex);
        throw; // Optionally rethrow or handle as needed
    }
}
}
