import requests, os, json

from dotenv import load_dotenv
load_dotenv()  

url = "https://api.asi1.ai/v1/chat/completions"
headers = {
"Authorization": f"Bearer {os.getenv('ASI_ONE_API_KEY')}",
"Content-Type": "application/json"
}
print({os.getenv('ASI_ONE_API_KEY')})
body = {
"model": "asi1-mini",
"messages": [{"role": "user", "content": "Hello! How can you help me today?"}]
}
# print(requests.post(url, headers=headers, json=body).json()["choices"][0]["message"]["content"])



resp = requests.post(url, headers=headers, json=body, timeout=30)

print("Status:", resp.status_code)
print("Raw response:", resp.text)   # 🔎 See what server actually sent

if resp.ok:
    data = resp.json()
    print("Reply:", data["choices"][0]["message"]["content"])