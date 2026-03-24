"""
Program: Taylor Series and Sequence Processor
Lab Work: No. 1 - Standard Types, Collections, Functions, Modules
Version: 1.0
Developer: German Vasilevich
Date: 2026-03-16
"""

import math
import logic
import initialization

@logic.table_decorator
def test_task_1(data_list, eps):
    """
    Tests Task 1 by iterating through data and printing a table.
    """
    for x in data_list:
        f_x, n = logic.calculate_exp_series(x, eps)
        math_f_x = math.exp(x)
        print(f"{x:^10.2f} | {n:^10} | {f_x:^20.8f} | {math_f_x:^20.8f} | {eps:^10.1e}")

def main():
    """
    Main interactive menu with protection against incorrect input.
    """

    while True:
        print("\n--- MAIN MENU ---")
        print("1. Run Task 1 (Taylor Series e^x)")
        print("2. Run Task 2 (Non-negative Counter)")
        print("3. Run Task 3 (Words starting with lowercase)")
        print("4. Run Task 4 (Analysing text)")
        print("5. Run Task 5 (Processing of real lists)")
        print("6. Exit")

        choice = input("Select an option (1-6): ")

        if choice == '1':
            n_elements = initialization.get_safe_number("Enter the size of the list: ", int)
            precision = initialization.get_safe_number("Enter precision (eps): ", float)

            print("\nInitialization methods:")
            print("  1. Manual input (Generator)")
            print("  2. Auto-generation (Generator)")
            init_choice = input("  Choose (1-2): ")

            if init_choice == '1':
                data = list(initialization.input_generator(n_elements))
            else:
                data = list(initialization.auto_generator(n_elements))

            test_task_1(data, precision)

        elif choice == '2':
            result = logic.process_sequence()
            print(f"\n[Result] Number of non-negative elements: {result}")
        elif choice == '3':
            count = logic.count_lowercase_start_words()
            print(f"\n[Result] Number of words starting with a lowercase letter: {count}")
        elif choice == '4':
            text = "So she was considering in her own mind, as well as she could, for the hot day made her feel very sleepy and stupid, whether the pleasure of making a daisy-chain would be worth the trouble of getting up and picking the daisies, when suddenly a White Rabbit with pink eyes ran close by her."
            results = logic.analyze_text(text)

            print("\n--- Analysis Results ---")
            print(f"a) Number of words with min length: {results['min_len_count']}")
            print(f"b) Words followed by a comma: {', '.join(results['comma_words'])}")
            print(f"c) Longest word ending in 'y': {results['longest_y']}")
        elif choice == '5':
            print("\n--- Task 5: Float List Processing ---")
            size = initialization.get_safe_number("Enter list size: ", int)
            my_list = initialization.input_float_list(size)

            logic.print_list_formatted(my_list)

            max_abs, sum_res, msg = logic.process_float_list(my_list)

            print(f"\nResult a) Max element by absolute value: {max_abs}")
            if sum_res is not None:
                print(f"Result b) Sum between 1st and 2nd positive: {sum_res} ({msg})")
            else:
                print(f"Result b) {msg}")

        elif choice == '6':
            print("Exiting.")
            break
        else:
            print("Invalid command. Please try again.")

if __name__ == "__main__":
    main()
