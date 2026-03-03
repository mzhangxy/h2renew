import os
import json
from seleniumbase import SB

def main():
    # 1. 从环境变量读取多账户配置 (GitHub Secret 传过来的)
    accounts_json = os.environ.get("ACCOUNTS_DATA", "[]")
    
    try:
        accounts = json.loads(accounts_json)
    except json.JSONDecodeError:
        print("解析 Secret 失败，请检查 JSON 格式！")
        return

    # 2. 设置 Buster 插件的相对路径（确保这个文件夹和 main.py 在同一级目录）
    buster_extension_path = "./buster_extension"

    # 3. 循环处理每一个账户
    for index, account in enumerate(accounts):
        url = account.get("url")
        proxy = account.get("proxy")
        
        print(f"\n--- 正在处理第 {index + 1} 个账户 ---")
        print(f"目标 URL: {url}")
        
        # 启动 SeleniumBase (开启 UC 模式，挂载代理，加载本地扩展，无头模式运行)
        with SB(uc=True, proxy=proxy, extension_dir=buster_extension_path, headless=True) as sb:
            try:
                # 访问续期页面
                sb.open(url)
                sb.sleep(5) # 等待页面初始加载
                
                print("页面已加载，准备点击 'Renew server' 按钮...")
                
                # --- 第一步点击 ---
                sb.click('button.btn-primary:contains("Renew server")') 
                sb.sleep(3) # 等待弹窗和 reCAPTCHA iframe 渲染完成
                
                # --- 处理 reCAPTCHA 复选框 ---
                print("准备点击 'I'm not a robot' 复选框...")
                sb.switch_to_frame("iframe[title*='reCAPTCHA']") 
                sb.click('#recaptcha-anchor')
                sb.switch_to_default_content() # 必须切回主页面
                sb.sleep(2) # 给弹窗一点加载时间
                
                # --- 处理可能出现的九宫格/语音挑战弹窗 ---
                print("检查是否弹出了验证码挑战框...")
                # 给插件一点额外的时间来渲染注入的按钮（无头模式下加载通常比较慢）
                sb.sleep(3) 
                
                if sb.is_element_visible("iframe[title*='recaptcha challenge']"):
                    print("检测到挑战弹窗，召唤 Buster 插件出场...")
                    sb.switch_to_frame("iframe[title*='recaptcha challenge']")
                    sb.sleep(1)    
                    
                    # 查找 Buster 注入的黄色小人/耳机按钮
