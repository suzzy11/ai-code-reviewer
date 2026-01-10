def calculate_average(numbers):
    """
    Summary.
        
    Args:
        numbers (list of int or float): A list of numbers for which to calculate the average.
    
    Returns:
        float: The average of the input numbers.
    """
    return sum(numbers) / len(numbers)


def find_max(numbers):
    """
    Summary.
    
    Parameters
    ----------
    param : type
        Description.
    
    Returns
    -------
    type
        Description.
    """
    
    return max(numbers)


def find_min(numbers):
    """
    Find the minimum value in a list of numbers.

    Args:
        numbers (list of int or float): A list containing numeric values.

    Returns:
        int or float: The minimum value in the list.
    """
    return min(numbers)


def process_data(numbers):
    """
    Process numerical data and return basic statistics.

    This function calculates the average, maximum, and minimum
    values from a list of numbers.

    Args:
        numbers (list of int or float): A list containing numeric values.

    Returns:
        dict: A dictionary containing average, max, and min values.
    """
    return {
        "average": calculate_average(numbers),
        "max": find_max(numbers),
        "min": find_min(numbers)
    }
