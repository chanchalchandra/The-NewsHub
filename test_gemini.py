import google.generativeai as genai

# Configure API key
genai.configure(api_key="AIzaSyC0wbVjZs70LqWDgjoSgWf6c_5vfBuo0ps")

# Try a simple test
try:
    # List available models
    for m in genai.list_models():
        print(f"Model: {m.name}")
        print(f"Display name: {m.display_name}")
        print(f"Description: {m.description}")
        print("---")
except Exception as e:
    print(f"Error: {str(e)}") 