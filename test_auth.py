import json
import requests

cfg = json.load(open("config/feishu-config.json"))
r = requests.post(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    json={"app_id": cfg["app_id"], "app_secret": cfg["app_secret"]}
)
print(r.json())
