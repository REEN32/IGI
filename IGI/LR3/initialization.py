"""
Module: initialization.py
Purpose: Functions for data initialization and safe user input.
"""

def input_generator(n):
    """
    Generator function to yield N numeric values from user keyboard.
    :param n: Number of elements to input.
    """
    for i in range(n):
        while True:
            try:
                val = float(input(f"  [{i+1}] Enter value: "))
                yield val
                break
            except ValueError:
                print("  Error: Please enter a valid number.")

def auto_generator(n):
    """
    Generator function to automatically create a sequence of numbers.
    :param n: Number of elements to generate.
    """
    for i in range(n):
        yield float(i * 0.5)

def get_safe_number(prompt, num_type=float):
    """
    Helper function to ensure user enters correct data type.
    :param prompt: Text to display.
    :param num_type: Expected type (int or float).
    """
    while True:
        try:
            return num_type(input(prompt))
        except ValueError:
            print(f"  Input Error: Expected a {num_type.__name__}.")


def input_float_list(size):
    """
    Task 5: Creates a list of floats from user input.
    :param size: Number of elements.
    """
    result = []
    print(f"--- Entering {size} float elements ---")
    for i in range(size):
        while True:
            try:
                val = float(input(f"  Element [{i}]: "))
                result.append(val)
                break
            except ValueError:
                print("  Error: Please enter a valid float number.")
    return result