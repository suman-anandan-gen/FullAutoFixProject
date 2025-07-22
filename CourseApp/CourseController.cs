using System;

public class CourseController
{
public void HandleRequest()
{
    try
    {
        string input = "not a number";
        int number;
        if (int.TryParse(input, out number))
        {
            string[] courses = new string[2];
            if (courses.Length > 5)
            {
                Console.WriteLine(courses[5]);
            }
            else
            {
                Console.WriteLine("Array index out of range.");
            }
        }
        else
        {
            throw new FormatException("Input string was not in a correct format.");
        }
    }
    catch (FormatException ex)
    {
        Logger.LogError(ex);
        throw; // Optionally rethrow or handle as needed
    }
    catch (Exception ex)
    {
        Logger.LogError(ex);
        throw; // Optionally rethrow or handle as needed
    }
}
}
