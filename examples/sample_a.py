def calculate_average(numbers):
    total = sum(numbers)
    count = len(numbers)
    return total / count


def find_max(numbers):
    return max(numbers)


def find_min(numbers):
    return min(numbers)


def process_data(data):
    avg = calculate_average(data)
    maximum = find_max(data)
    minimum = find_min(data)

    return {
        "average": avg,
        "max": maximum,
        "min": minimum
    }
