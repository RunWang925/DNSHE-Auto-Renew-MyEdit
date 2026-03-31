import requests
import os

# 配置
API_KEY = os.environ.get('DNSHE_API_KEY')
API_SECRET = os.environ.get('DNSHE_API_SECRET')
PUSHPLUS_TOKEN = os.environ.get('PUSHPLUS_TOKEN')
PUSHPLUS_TOPIC = os.environ.get('PUSHPLUS_TOPIC')

BASE_URL = "https://api005.dnshe.com/index.php?m=domain_hub"

def send_pushplus(content):
    if not PUSHPLUS_TOKEN:
        print("未配置 PushPlus Token，跳过推送")
        return
    url = "http://www.pushplus.plus/send"
    data = {
        "token": PUSHPLUS_TOKEN,
        "title": "DNSHE 域名自动续期报告",
        "content": content,
        "template": "txt",
        "topic": PUSHPLUS_TOPIC
    }
    requests.post(url, json=data)

def main():
    headers = {
        "X-API-Key": API_KEY,
        "X-API-Secret": API_SECRET,
        "Content-Type": "application/json"
    }

    # 获取域名列表
    list_url = f"{BASE_URL}&endpoint=subdomains&action=list"
    try:
        resp = requests.get(list_url, headers=headers)
        subdomains = resp.json().get('subdomains', [])
    except Exception as e:
        send_pushplus(f"获取域名列表失败: {str(e)}")
        return

    results = []
    
    for domain in subdomains:
        domain_id = domain['id']
        full_domain = domain['full_domain']

        renew_url = f"{BASE_URL}&endpoint=subdomains&action=renew"
        payload = {"subdomain_id": domain_id}
        
        try:
            r_resp = requests.post(renew_url, headers=headers, json=payload).json()

            # 未到续期时间
            if r_resp.get("error_code") == "renewal_not_yet_available":
                days = r_resp.get("days_until_window")
                results.append(f"⏳ {full_domain}：还未到续期时间，剩余 {days} 天")
                continue

            # 续期成功（按官方文档字段显示）
            if r_resp.get('success'):
                old_expiry = r_resp.get('previous_expires_at', '未知')
                new_expiry = r_resp.get('new_expires_at', '未知')
                results.append(f"✅ {full_domain}：续期成功！原到期：{old_expiry} → 新到期：{new_expiry}")
            else:
                msg = r_resp.get('message', '未知错误')
                results.append(f"❌ {full_domain}：续期失败 → {msg}")

        except Exception as e:
            results.append(f"❌ {full_domain}：请求异常")

    if results:
        msg = "\n".join(results)
        print(msg)
        send_pushplus(msg)

if __name__ == "__main__":
    main()
