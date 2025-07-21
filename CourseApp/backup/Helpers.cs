using System;

public static class Helpers
{
public static string Normalize(string input)
{
    try
    {
        if(input == null)
            return ""; // Return empty string if input is null

        return input.ToUpper();
    }
    catch (Exception ex)
    {
        Logger.LogError(ex);
        throw;
    }
}

    public static void Validate(string input)
    {
        try
        {
            if (input == null)
                throw new ArgumentNullException(nameof(input)); // ArgumentNullException
        }
        catch (Exception ex)
        {
            Logger.LogError(ex);
            throw;
        }
    }
}
