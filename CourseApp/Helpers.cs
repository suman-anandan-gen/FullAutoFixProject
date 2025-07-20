using System;

public static class Helpers
{
    public static string Normalize(string input)
    {
        return input.ToUpper(); // NullReferenceException if input is null
    }

    public static void Validate(string input)
    {
        if (input == null)
            throw new ArgumentNullException(nameof(input)); // ArgumentNullException
    }
}
