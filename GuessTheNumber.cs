using System;
 
public class Program
{
    public static void Main()
    {
        Random rnd = new Random();
        int targetNumber = rnd.Next(1, 101);
        Console.WriteLine("Guess a number between 1 and 100!");
 
        while (true)
        {
            int input = Convert.ToInt32(Console.ReadLine());
 
            if (input > targetNumber)
            {
                Console.WriteLine("Your guess was higher than the number! Guess again:");
            }
            else if (input < targetNumber)
            {
                Console.WriteLine("Your guess was lower than the number! Guess again:");
            }
            else
            {
                Console.WriteLine("You guessed correctly!");
                break;
            }
        }
    }
}