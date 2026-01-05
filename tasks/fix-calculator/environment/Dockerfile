FROM python:3.12-slim

WORKDIR /workspace

# Create the buggy calculator.py (multiply uses + instead of *)
RUN cat > calculator.py << 'EOF'
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a + b

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
EOF

# Create main.py that uses the calculator
RUN cat > main.py << 'EOF'
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
EOF

RUN mkdir -p /logs/agent /logs/verifier
