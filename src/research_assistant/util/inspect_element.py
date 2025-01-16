
def inspect_elements_data(elements_data):
    """Deep inspection of elements data structure"""
    print("\n[Data Inspector] Starting deep inspection of elements data")
    
    # Basic type information
    print(f"\n[Basic Type Info]")
    print(f"Type: {type(elements_data)}")
    print(f"Base Type: {elements_data.__class__.__base__}")
    
    # Size information
    try:
        length = len(elements_data)
        print(f"Length: {length}")
    except:
        print("Object has no length")
    
    # Content sample
    print("\n[Content Preview]")
    print(f"Raw data preview: {str(elements_data)[:200]}...")
    
    # If it's a collection, inspect first item
    if isinstance(elements_data, (list, tuple, set)):
        if len(elements_data) > 0:
            first_item = elements_data[0]
            print("\n[First Item Analysis]")
            print(f"First item type: {type(first_item)}")
            print(f"First item preview: {str(first_item)[:200]}...")
            
            # If first item is an object, inspect its attributes
            if hasattr(first_item, '__dict__'):
                print("\n[First Item Attributes]")
                for attr in dir(first_item):
                    if not attr.startswith('_'):  # Skip private attributes
                        print(f"Attribute '{attr}': {type(getattr(first_item, attr))}")
    
    # If it's a dictionary, inspect keys and value types
    if isinstance(elements_data, dict):
        print("\n[Dictionary Analysis]")
        print("Keys:", list(elements_data.keys()))
        print("\nValue types:")
        for key, value in elements_data.items():
            print(f"Key '{key}': {type(value)}")
    
    # Memory size estimation
    import sys
    try:
        memory_size = sys.getsizeof(elements_data)
        print(f"\nApproximate memory size: {memory_size} bytes")
    except:
        print("Could not determine memory size")
    
    # Serialization test
    print("\n[Serialization Test]")
    try:
        import json
        json.dumps(elements_data)
        print("✓ Can be JSON serialized")
    except Exception as e:
        print(f"✗ Cannot be JSON serialized: {str(e)}")
    
    try:
        import pickle
        pickle.dumps(elements_data)
        print("✓ Can be Pickled")
    except Exception as e:
        print(f"✗ Cannot be Pickled: {str(e)}")