"""
Module: logic.py
Purpose: Core business functions and mathematical algorithms.
"""
import math


def table_decorator(func):
    """
    Decorator to format function output as a structured table.
    Demonstrates usage of decorators (Requirement 10).
    """

    def wrapper(*args, **kwargs):
        print("\n" + "=" * 85)
        print(f"{'x':^10} | {'n':^10} | {'F(x)':^20} | {'Math F(x)':^20} | {'eps':^10}")
        print("-" * 85)
        result = func(*args, **kwargs)
        print("=" * 85)
        return result

    return wrapper


def calculate_exp_series(x, eps, max_iter=500):
    """
    Task 1: Computes e^x using Taylor series expansion.
    :param x: Argument value.
    :param eps: Precision.
    :param max_iter: Maximum iterations (default 500).
    :return: Tuple (sum_value, iterations_count).
    """
    sum_val = 1.0
    term = 1.0
    n = 1

    while n < max_iter:
        term *= x / n
        sum_val += term
        if abs(term) < eps:
            break
        n += 1
    return sum_val, n


def process_sequence():
    """
    Task 2: Counts non-negative numbers in a sequence.
    Stop condition: entry of a number less than -100.
    """
    count = 0
    print("\n--- Start entering numbers (less than -100 to stop) ---")
    while True:
        try:
            val = int(input("  Enter integer: "))
            if val < -100:
                break
            if val >= 0:
                count += 1
        except ValueError:
            print("  Error: Invalid integer format.")
    return count


def count_lowercase_start_words():
    """
    Task 3: Counts words starting with a lowercase letter.
    No regular expressions used.
    """
    text = input("Enter a string: ")
    if not text:
        return 0

    words = text.split()
    count = 0

    for word in words:
        if word[0].islower():
            count += 1

    return count


def analyze_text(text):
    """
    Task 4: Analyzes the provided string for specific conditions.
    a) Count words with minimum length.
    b) Output words followed by a comma.
    c) Find the longest word ending in 'y'.
    """
    raw_words = text.split()

    clean_words = [w.strip(",.").lower() for w in raw_words]

    min_len = min(len(w) for w in clean_words)
    count_min = sum(1 for w in clean_words if len(w) == min_len)

    words_with_comma = [w.strip(",").lower() for w in raw_words if w.endswith(',')]

    y_words = [w for w in clean_words if w.endswith('y')]
    longest_y_word = max(y_words, key=len) if y_words else None

    return {
        "min_len_count": count_min,
        "comma_words": words_with_comma,
        "longest_y": longest_y_word
    }


def process_float_list(lst):
    """
    Task 5:
    1) Finds max element by absolute value.
    2) Calculates sum between 1st and 2nd positive elements.
    """
    if not lst:
        return None, None

    max_abs_element = max(lst, key=abs)

    positive_indices = [i for i, x in enumerate(lst) if x > 0]

    sum_between = 0
    message = ""

    if len(positive_indices) >= 2:
        idx1 = positive_indices[0]
        idx2 = positive_indices[1]
        sub_list = lst[idx1 + 1: idx2]
        sum_between = sum(sub_list)
        message = f"Sum between index {idx1} and {idx2} (exclusive)"
    else:
        message = "Less than two positive elements found."
        sum_between = None

    return max_abs_element, sum_between, message


def print_list_formatted(lst):
    """Task 5: Displaying the list (Requirement 4)."""
    print(f"Current list: [{', '.join(map(str, lst))}]")