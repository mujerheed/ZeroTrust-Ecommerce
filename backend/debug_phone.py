#!/usr/bin/env python3
"""
Debug script to check vendor phone numbers normalization
"""

import sys
sys.path.insert(0, '/home/secure/Desktop/Shobhit University/3rd Semester/Minor Project/ZeroTrust-Ecommerce/backend')

from auth_service.auth_logic import normalize_phone

# Test all possible user input formats
# NOTE: Nigerian numbers are 10 digits after the 0, e.g., 0801234567**8** (11 chars total with 0)
test_cases = [
    # Format: (user_input, expected_output, description)
    ("08012345678", "+2348012345678", "✓ Correct: Local format (0 + 10 digits)"),
    ("0801234567", "+234801234567", "✗ Wrong: Only 9 digits after 0 (too short)"),
    ("08012345678", "+2348012345678", "✓ Correct: Local with spaces"),
    ("2348012345678", "+2348012345678", "✓ Correct: Without + prefix"),
    ("+2348012345678", "+2348012345678", "✓ Correct: Already correct"),
    ("+234 801 234 5678", "+2348012345678", "✓ Correct: With spaces"),
    ("8012345678", "+2348012345678", "✓ Correct: No prefix (assumes 234)"),
    ("0 801 234 5678", "+2348012345678", "✓ Correct: Local with spaces"),
    ("+234-801-234-5678", "+2348012345678", "✓ Correct: With dashes"),
    
    # Your case with 11 digits after 0 (WRONG)
    ("09067766240", "+23409067766240", "✗ Wrong: 11 digits after 0 (should be 10)"),
    # Correct version (10 digits after 0)
    ("0906776624", "+2349906776624", "✗ Wrong: This gives 9 digits! Should be 0906776624X"),
]

print("=" * 90)
print("PHONE NORMALIZATION TEST - NIGERIAN PHONE FORMAT")
print("=" * 90)
print("\nNIGERIAN PHONE STANDARD:")
print("  - Format: 0 + [7/8/9] + [0/1] + 8 digits = 11 characters total")
print("  - Example: 08012345678 (0 + 10 digits)")
print("  - Normalized: +2348012345678 (14 characters)")
print("=" * 90)

all_passed = True
for user_input, expected, description in test_cases:
    result = normalize_phone(user_input)
    passed = result == expected
    all_passed = all_passed and passed
    
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"\n{description}")
    print(f"   Input:    '{user_input}' ({len(user_input)} chars)")
    print(f"   Expected: '{expected}' ({len(expected)} chars)")
    print(f"   Got:      '{result}' ({len(result)} chars)")
    if not passed:
        print(f"   ⚠️  ERROR: Mismatch!")

print("\n" + "=" * 90)
print("\n⚠️  YOUR ISSUE:")
print("  You have: '09067766240' (11 digits after 0 = WRONG)")
print("  Should be: '09067766240' → Remove last digit → '0906776624X'")
print("  Or check if the vendor was created with wrong number")
print("=" * 90)


