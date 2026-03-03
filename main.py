import os
import json
from seleniumbase import SB

# 引入 NopeCha 的官方库
from nopecha.api.requests import RequestsAPIClient

def main():
    # 1. 读取账户配置
    accounts_json = os.environ.get("ACCOUNTS_DATA", "[]")
    # 2. 读取 NopeCha API 密钥
    nopecha_api_key = os.environ.get("NOPECHA_API_KEY", "")
    
    try:
        accounts = json.loads(accounts_json)
    except json.JSONDecodeError:
        print("解析 Secret 失败，请检查 JSON 格式！")
        return

    # 实例化你的官方 API Client
    if nopecha_api_key:
        api = RequestsAPIClient(nopecha_api_key)
    else:
        print("[致命错误] 找不到 NOPECHA_API_KEY，请检查环境变量配置！")
        api = None

    # 循环处理每一个账户
    for index, account in enumerate(accounts):
        target_url = account.get("url")
        proxy = account.get("proxy")
        
        print(f"\n--- 正在处理第 {index + 1} 个账户 ---")
        print(f"目标 URL: {target_url}")
        
        with SB(uc=True, proxy=proxy, headless=True) as sb:
            try:
                # 访问网页
                sb.open(target_url)
                sb.sleep(5) 
                
                print("页面已加载，准备点击 'Renew server' 按钮...")
                sb.click('button.btn-primary:contains("Renew server")') 
                sb.sleep(3) # 等待验证码模块加载
                
                if api:
                    # --- 开始 NopeCha 官方库打码流程 ---
                    print("开始调用 NopeCha 官方接口...")
                    
                    target_sitekey = "6LeUAtQiAAAAADTs_7zmhdpi_78S9bW-zzDFmpV2"
                    
                    try:
                        # 官方提供的方法
                        solution = api.solve_recaptcha2(target_sitekey, target_url)
                        token = solution.get("data")
                    except Exception as e:
                        print(f"NopeCha API 获取失败：{e}")
                        token = None
                    
                    if token:
                        print("太棒了！NopeCha 成功返回了 Token！")
                        print("准备将 Token 隐身注入到网页内部...")
                        
                        inject_js = f'document.getElementById("g-recaptcha-response").innerHTML="{token}";'
                        sb.execute_script(inject_js)
                        sb.sleep(1)
                        
                        # 提交
                        print("准备点击最终的 'Renew' 提交按钮...")
                        sb.click('button:contains("Renew")')
                        print(f"账户 {index + 1} 续期操作执行完毕！")
                    else:
                        print(f"账户 {index + 1} 因为未获取到 Token，跳过执行。")
                
                sb.sleep(5) 
                
            except Exception as e:
                print(f"\n[错误] 账户 {index + 1} 处理时发生异常: {e}")
                
                screenshot_name = f"error_account_{index + 1}.png"
                html_name = f"error_account_{index + 1}.html"
                
                sb.save_screenshot(screenshot_name)
                with open(html_name, "w", encoding="utf-8") as f:
                    f.write(sb.get_page_source())
                    
                print(f"现场截图已保存为: {screenshot_name}")

if __name__ == "__main__":
    main()
