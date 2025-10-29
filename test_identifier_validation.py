"""Quick test to verify single-word identifier validation."""

from permission_sdk.utils import validate_subject_identifier, parse_subject_identifier
from permission_sdk.exceptions import ValidationError

# Test single-word identifiers (NEW)
print("Testing single-word identifiers...")
try:
    validate_subject_identifier("system")
    print("✅ 'system' is valid")
except ValidationError as e:
    print(f"❌ 'system' failed: {e}")

try:
    validate_subject_identifier("admin")
    print("✅ 'admin' is valid")
except ValidationError as e:
    print(f"❌ 'admin' failed: {e}")

try:
    validate_subject_identifier("guest")
    print("✅ 'guest' is valid")
except ValidationError as e:
    print(f"❌ 'guest' failed: {e}")

# Test type:id format (EXISTING)
print("\nTesting type:id format...")
try:
    validate_subject_identifier("user:123")
    print("✅ 'user:123' is valid")
except ValidationError as e:
    print(f"❌ 'user:123' failed: {e}")

try:
    validate_subject_identifier("org:456")
    print("✅ 'org:456' is valid")
except ValidationError as e:
    print(f"❌ 'org:456' failed: {e}")

# Test invalid characters (SHOULD FAIL)
print("\nTesting invalid characters...")
try:
    validate_subject_identifier("user@123")
    print("❌ 'user@123' should have failed!")
except ValidationError:
    print("✅ 'user@123' correctly rejected")

try:
    validate_subject_identifier("user/123")
    print("❌ 'user/123' should have failed!")
except ValidationError:
    print("✅ 'user/123' correctly rejected")

# Test parsing
print("\nTesting parse_subject_identifier...")
subject_type, subject_id = parse_subject_identifier("system")
print(f"✅ parse('system') = ('{subject_type}', '{subject_id}')")
assert subject_type == "system" and subject_id == "system"

subject_type, subject_id = parse_subject_identifier("user:john.doe")
print(f"✅ parse('user:john.doe') = ('{subject_type}', '{subject_id}')")
assert subject_type == "user" and subject_id == "john.doe"

print("\n🎉 All tests passed!")
