
def reproduce():
    # Simulate the data structure in app.py
    leg = {'target': None} # Key exists, value is None
    
    # This is the FIX:
    target = leg.get('target') or 0
    print(f"Target is: {target} (Type: {type(target)})")
    
    try:
        if target > 0:
            print("Target > 0")
    except TypeError as e:
        print(f"Caught expected error: {e}")

if __name__ == "__main__":
    reproduce()
