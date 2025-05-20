import os
import re

# Path to the file containing the URL reference
hybrid_search_file = "/opt/jarvis/hybrid_search/hybrid_search.py"

def fix_openwebui_url():
    # Get the correct URL from environment variable or use default
    openwebui_url = os.environ.get('OPENWEBUI_API_BASE_URL', 'http://open-webui:8080')
    
    if os.path.exists(hybrid_search_file):
        with open(hybrid_search_file, 'r') as file:
            content = file.read()
        
        # Replace hardcoded localhost:3000 references with the correct service URL
        updated_content = re.sub(
            r'http://localhost:3000', 
            openwebui_url, 
            content
        )
        
        with open(hybrid_search_file, 'w') as file:
            file.write(updated_content)
        
        print(f"Updated OpenWebUI URL to {openwebui_url} in {hybrid_search_file}")
    else:
        print(f"Warning: Could not find file {hybrid_search_file}")

if __name__ == "__main__":
    fix_openwebui_url()
