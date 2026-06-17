import json
import urllib.request
import os
import time

with open(r"C:\Users\himan\.gemini\antigravity-ide\mcp_config.json") as f:
    config = json.load(f)

server_url = config['mcpServers']['stitch']['serverUrl']
headers = config['mcpServers']['stitch']['headers']
headers['Content-Type'] = 'application/json'

def mcp_call(method, params):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": method,
            "arguments": params
        }
    }
    req = urllib.request.Request(
        server_url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        return result

print("Creating Project...")
proj_res = mcp_call("create_project", {"title": "HJAI High-Fidelity"})
print(json.dumps(proj_res, indent=2))

# Extract project ID
content_text = proj_res.get('result', {}).get('content', [{}])[0].get('text', '{}')
try:
    proj_data = json.loads(content_text)
    # The name is like "projects/12345"
    project_id = proj_data.get('name', '').split('/')[-1]
except Exception as e:
    project_id = ''
    print(f"Error extracting project_id: {e}")

print(f"Project ID: {project_id}")

if project_id:
    print("Generating Screen...")
    with open(r"C:\Users\himan\Downloads\HJAI\frontend\.stitch\next-prompt.md", "r") as f:
        prompt = f.read()
        
    screen_res = mcp_call("generate_screen_from_text", {
        "projectId": project_id,
        "prompt": prompt,
        "deviceType": "DESKTOP"
    })
    
    print("Screen generated. Saving results...")
    
    # The output is in the result.content text
    screen_text = screen_res.get('result', {}).get('content', [{}])[0].get('text', '{}')
    
    with open(r"C:\Users\himan\Downloads\HJAI\frontend\.stitch\mcp_output.json", "w") as out:
        out.write(screen_text)
        
    print("Done! Check frontend/.stitch/mcp_output.json")
