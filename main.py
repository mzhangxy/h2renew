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
                    if sb.is_element_visible('#solver-button'):
                        print("找到 Buster 破解按钮，点击执行自动听写！")
                        sb.click('#solver-button')
                        # 语音识别需要一定时间，多给几秒缓冲
                        sb.sleep(8) 
                    else:
                        print("没有找到 Buster 按钮，可能是插件没正确加载或版本不兼容。")
                        
                        # --- 新增的调试代码：记录案发现场 ---
                        print("正在保存验证码挑战框的截图和 iframe 源码...")
                        screenshot_name = f"no_buster_account_{index + 1}.png"
                        html_name = f"no_buster_iframe_{index + 1}.html"
                        
                        # 保存截图（拍下整个浏览器的画面，看看弹窗是不是真的出来了）
                        sb.save_screenshot(screenshot_name)
                        
                        # 保存当前 iframe 内部的 HTML 源码（非常关键，能看出插件到底有没有把代码塞进去）
                        with open(html_name, "w", encoding="utf-8") as f:
                            f.write(sb.get_page_source())
                            
                        print(f"验证码弹窗截图已保存为: {screenshot_name}")
                        print(f"iframe 源码已保存为: {html_name}")
                        
                    # 极其重要：无论插件有没有找到，处理完弹窗都必须切回主网页！
                    sb.switch_to_default_content() 
                else:
                    print("网络信誉极佳！没有弹出挑战框，直接秒过。")
                
                # --- 最后一步提交 ---
                print("准备点击最终的 'Renew' 提交按钮...")
                sb.click('button:contains("Renew")')
                
                print(f"账户 {index + 1} 续期操作执行完毕！")
                sb.sleep(5) # 给页面提交后一点缓冲时间
                
            except Exception as e:
                print(f"\n[错误] 账户 {index + 1} 处理时发生异常: {e}")
                
                # --- 新增的调试代码 ---
                print("正在保存案发现场截图和网页源码...")
                screenshot_name = f"error_account_{index + 1}.png"
                html_name = f"error_account_{index + 1}.html"
                
                # 保存当前浏览器画面的截图
                sb.save_screenshot(screenshot_name)
                
                # 保存当前网页的完整 HTML 源码
                with open(html_name, "w", encoding="utf-8") as f:
                    f.write(sb.get_page_source())
                    
                print(f"现场截图已保存为: {screenshot_name}")
                print(f"网页源码已保存为: {html_name}")

if __name__ == "__main__":
    main()
