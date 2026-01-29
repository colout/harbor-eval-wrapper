#!/bin/bash

# Turn 1: Fix multiply bug
sed -i '/def multiply/,/^def\|^$/s/return a + b/return a * b/' /workspace/calculator.py

# Verify turn 1
if ! python3 /usr/local/lib/.phase1.pyc; then
    echo "Phase 1 failed"
    exit 1
fi

# Turn 2: Add power function
cat >> /workspace/calculator.py << 'EOF'


def power(base, exponent):
    return base ** exponent
EOF
