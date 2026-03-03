import os
import json
import requests
from seleniumbase import SB

def get_nopecha_token(api_key, sitekey, page_url):
    """
    负责将网站信息发送给 NopeCha，并等待返回破解好的 Token
    """
    print("正在呼叫 NopeCha 平台进行云端打码...")
    url = "https://api.nopecha.com/"
    payload = {
        "key": api_key,
        "type": "recaptcha2",
        "sitekey": sitekey,
        "url": page_url
    }
    
    try:
        # NopeCha 破解一般需要几秒到十几秒，这里设置 60 秒超时
        response = requests.post(url, json=payload, timeout=60)
        result = response.json()
        
        if "data" in result:
            print("太棒了！NopeCha 成功返回了 Token！")
            return result["data"]
        else:
            print(f"NopeCha 报错了: {result.get('message', '未知错误')}")
            return None
    except Exception as e:
        print(f"请求 NopeCha API 时发生网络错误: {e}")
        return None

def main():
    # 1. 读取账户配置
    accounts_json = os.environ.get("ACCOUNTS_DATA", "[]")
    # 2. 读取你的 NopeCha API 密钥 (我们稍后要在 GitHub 里配置它)
    nopecha_api_key = os.environ.get("NOPECHA_API_KEY", "")
    
    try:
        accounts = json.loads(accounts_json)
    except json.JSONDecodeError:
        print("解析 Secret 失败，请检查 JSON 格式！")
        return

    # 循环处理每一个账户
    for index, account in enumerate(accounts):
        target_url = account.get("url")
        proxy = account.get("proxy")
        
        print(f"\n--- 正在处理第 {index + 1} 个账户 ---")
        print(f"目标 URL: {target_url}")
        
        # 启动 SeleniumBase (删除了插件加载，保持干净的无头模式)
        with SB(uc=True, proxy=proxy, headless=True) as sb:
            try:
                # 访问网页
                sb.open(target_url)
                sb.sleep(5) 
                
                print("页面已加载，准备点击 'Renew server' 按钮...")
                sb.click('button.btn-primary:contains("Renew server")') 
                sb.sleep(3) # 等待验证码模块加载
                
                # --- 开始 NopeCha 纯协议打码流程 ---
                print("开始调用 NopeCha API...")
                
                if not nopecha_api_key:
                    print("[致命错误] 找不到 NOPECHA_API_KEY，请检查环境变量配置！")
                    continue
                
                # 网页里固定的 reCAPTCHA 身份识别码
                target_sitekey = "6LeUAtQiAAAAADTs_7zmhdpi_78S9bW-zzDFmpV2"
                
                # 获取 Token
                token = get_nopecha_token(nopecha_api_key, target_sitekey, target_url)
                
                if token:
                    print("准备将 Token 隐身注入到网页内部...")
                    
                    # 关键魔法：直接用一段 JavaScript 把 Token 塞进页面的隐藏表单里
                    inject_js = f'document.getElementById("g-recaptcha-response").innerHTML="{token}";'
                    sb.execute_script(inject_js)
                    sb.sleep(1)
                    
                    # 提交
                    print("准备点击最终的 'Renew' 提交按钮...")
                    sb.click('button:contains("Renew")')
                    print(f"账户 {index + 1} 续期操作执行完毕！")
                else:
                    print(f"账户 {index + 1} 因为未获取到 Token，跳过执行。")
                
                sb.sleep(5) # 给页面提交后一点缓冲时间
                
            except Exception as e:
                print(f"\n[错误] 账户 {index + 1} 处理时发生异常: {e}")
                
                # --- 错误现场拍照 ---
                screenshot_name = f"error_account_{index + 1}.png"
                html_name = f"error_account_{index + 1}.html"
                
                sb.save_screenshot(screenshot_name)
                with open(html_name, "w", encoding="utf-8") as f:
                    f.write(sb.get_page_source())
                    
                print(f"现场截图已保存为: {screenshot_name}")

if __name__ == "__main__":
    main()
