import json
import urllib.request
import os

with open(r"C:\Users\himan\.gemini\antigravity-ide\mcp_config.json") as f:
    config = json.load(f)

server_url = config['mcpServers']['stitch']['serverUrl']
headers = config['mcpServers']['stitch']['headers']
headers['Content-Type'] = 'application/json'

payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
}

req = urllib.request.Request(
    server_url,
    data=json.dumps(payload).encode('utf-8'),
    headers=headers,
    method='POST'
)

try:
    with urllib.request.urlopen(req) as response:
        result = response.read().decode('utf-8')
        print(result)
except Exception as e:
    print(f"Error: {e}")
