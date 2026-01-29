from calculator import add, subtract, multiply, divide


def run_calculations():
    results = {
        "add": add(10, 5),
        "subtract": subtract(10, 5),
        "multiply": multiply(10, 5),
        "divide": divide(10, 5),
    }
    return results


if __name__ == "__main__":
    results = run_calculations()
    for op, result in results.items():
        print(f"{op}: {result}")
