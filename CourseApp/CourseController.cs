using System;

public class CourseController
{
    public void HandleRequest()
    {
        try
        {
            string[] courses = new string[2];
            Console.WriteLine(courses[5]); // IndexOutOfRangeException
        }
        catch (Exception ex)
        {
            Logger.LogError(ex);
            throw; // Optionally rethrow or handle as needed
        }
    }
}
