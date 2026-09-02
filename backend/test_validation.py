from app.schemas.cinematography import ColorPlan as ColorSchema, CameraSchema, CompositionSchema, LightingSchema
from pydantic import ValidationError
import sys

def run_tests():
    print("Testing ColorSchema Validation...")
    
    # Valid
    try:
        color_valid = ColorSchema(
            palette=["#18324A", "#2F5872"],
            temperature_kelvin=4100,
            contrast=0.72,
            saturation=0.58,
            mood="Melancholic"
        )
        print("PASS Valid ColorSchema parsed correctly.")
    except Exception as e:
        print(f"FAIL Failed on valid ColorSchema: {e}")

    # Invalid hex
    try:
        color_invalid_hex = ColorSchema(
            palette=["#18324A", "invalid-color"]
        )
        print("FAIL Failed to catch invalid hex color.")
    except ValidationError:
        print("PASS Correctly caught invalid hex color.")

    # Invalid temp
    try:
        color_invalid_temp = ColorSchema(
            temperature_kelvin=13000
        )
        print("FAIL Failed to catch out-of-range temperature.")
    except ValidationError:
        print("PASS Correctly caught out-of-range temperature.")

    # Invalid contrast
    try:
        color_invalid_contrast = ColorSchema(
            contrast=3.0
        )
        print("FAIL Failed to catch out-of-range contrast.")
    except ValidationError:
        print("PASS Correctly caught out-of-range contrast.")

    # Valid Camera
    print("\nTesting CameraSchema Validation...")
    try:
        cam_valid = CameraSchema(
            angle="EYE_LEVEL",
            focal_length_mm=50,
            lens_type="PRIME",
            movement="STATIC"
        )
        print("PASS Valid CameraSchema parsed correctly.")
    except Exception as e:
        print(f"FAIL Failed on valid CameraSchema: {e}")

    # Invalid Camera (missing angle)
    try:
        cam_invalid = CameraSchema(
            focal_length_mm=50
        )
        print("FAIL Failed to catch missing angle.")
    except ValidationError:
        print("PASS Correctly caught missing required field (angle).")

    print("\nAll validation tests complete.")

if __name__ == "__main__":
    run_tests()
