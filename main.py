import os
import sys
import time
import random
import requests
from xvfbwrapper import Xvfb
from seleniumbase import SB

try:
    import speech_recognition as sr
    from pydub import AudioSegment
except ImportError:
    pass

# ==============================================================================
# Telegram 通知模块
# ==============================================================================
def send_tg_message(token, chat_id, message):
    """发送 Telegram 通知"""
    if not token or not chat_id:
        print("未配置 TG_TOKEN 或 TG_CHAT_ID，跳过通知。")
        return
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Telegram 通知发送成功！")
        else:
            print(f"❌ Telegram 通知发送失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ Telegram 通知请求异常: {e}")

# ==============================================================================
# 语音验证码破解模块 (已适配 SeleniumBase 语法)
# ==============================================================================
class RecaptchaAudioSolver:
    def __init__(self, sb):
        self.sb = sb
        self.log_func = print

    def log(self, msg):
        self.log_func(f"[Solver] {msg}")

    def solve(self):
        self.log("🎧 启动过盾流程...")
        try:
            # 尝试定位音频按钮
            if not self.sb.is_element_visible('#recaptcha-audio-button'):
                self.log("❌ 未找到验证按钮，可能被 Google 屏蔽")
                return False
            
            self.sb.click('#recaptcha-audio-button')
            time.sleep(random.uniform(3, 5))
            
            # 循环尝试获取音频源
            src = None
            for attempt in range(3):
                src = self.get_audio_source()
                if src:
                    break
                self.log(f"⚠️ 第 {attempt+1} 次获取TOKEN失败，尝试点击刷新...")
                if self.sb.is_element_visible('#recaptcha-reload-button'):
                    self.sb.click('#recaptcha-reload-button')
                    time.sleep(random.uniform(4, 6))
            
            if not src:
                self.log("❌ 最终无法获取链接 (IP 可能被暂时封禁验证)")
                return False

            # 下载并识别
            self.log("📥 正在处理数据...")
            r = requests.get(src, timeout=15)
            with open("audio.mp3", 'wb') as f: f.write(r.content)
            
            sound = AudioSegment.from_mp3("audio.mp3")
            sound.export("audio.wav", format="wav")
            
            recognizer = sr.Recognizer()
            with sr.AudioFile("audio.wav") as source:
                audio_data = recognizer.record(source)
                key_text = recognizer.recognize_google(audio_data)
                self.log(f"🗣️ 识别结果: [{key_text}]")

            # 输入结果
            if self.sb.is_element_visible('#audio-response'):
                # 模拟逐字输入
                for char in key_text:
                    self.sb.add_text('#audio-response', char)
                    time.sleep(random.uniform(0.1, 0.2))
                
                time.sleep(1)
                self.sb.click('#recaptcha-verify-button')
                self.log("🚀 提交验证...")
                time.sleep(3)
                return True
        except Exception as e:
            self.log(f"💥 异常: {e}")
            return False
        finally:
            for f in ["audio.mp3", "audio.wav"]:
                if os.path.exists(f): os.remove(f)

    def get_audio_source(self):
        try:
            if self.sb.is_element_visible('.rc-audiochallenge-ndownload-link'):
                return self.sb.get_attribute('.rc-audiochallenge-ndownload-link', 'href')
            elif self.sb.is_element_visible('xpath', '//a[contains(@href, ".mp3")]'):
                return self.sb.get_attribute('xpath', '//a[contains(@href, ".mp3")]', 'href')
            return None
        except: 
            return None

# ==============================================================================
# 核心续期业务逻辑 (SeleniumBase UC 模式)
# ==============================================================================
def renew_host2play(url, proxy_url=None):
    print("启动 Xvfb 虚拟桌面...")
    vdisplay = Xvfb(width=1280, height=720, colordepth=24)
    vdisplay.start()
    
    success = False
    msg = ""
    
    try:
        # 启动 UC 模式。无头设为 False，由 Xvfb 接管虚拟显示器
        with SB(uc=True, proxy=proxy_url, headless=False, browser="chrome") as sb:
            print(f"🌐 访问续期目标网址: {url}")
            # uc_open 会自动处理基础的 Cloudflare 盾
            sb.uc_open_with_reconnect(url, 4) 
            
            print("⏳ 等待页面加载...")
            time.sleep(3) 
            
            print("📜 向下滚动页面...")
            sb.execute_script("window.scrollBy(0, 500);")
            time.sleep(1)

            first_btn_xpath = '//button[normalize-space(text())="Renew server"]'
            
            # ================= 触发续期弹窗循环 =================
            solved_captcha = False
            for attempt in range(3):
                print(f"\n⚡ 第 {attempt+1} 次尝试获取验证码弹窗...")
                
                if not sb.is_element_visible(first_btn_xpath):
                    refresh_xpath = '//button[contains(text(), "Refresh page")]'
                    if sb.is_element_visible(refresh_xpath):
                        print("🔄 发现 'Refresh page' 按钮，尝试原生刷新...")
                        sb.refresh()
                        time.sleep(5)
                        sb.execute_script("window.scrollBy(0, 500);")
                    else:
                        print("❌ 未找到初始的 'Renew server' 按钮")
                        sb.save_screenshot('error_no_first_btn.png')
                        break
                        
                print(f"🖱️ 尝试物理点击初始 'Renew server' 按钮...")
                # uc_click 是终极武器，模拟真实物理点击，绕过 CF 事件拦截
                sb.uc_click(first_renew_btn_xpath := first_btn_xpath)
                time.sleep(5) 
                
                # 检测是否报错
                refresh_xpath = '//button[contains(text(), "Refresh page")]'
                if sb.is_element_visible(refresh_xpath):
                    print("💥 检测到服务器内部错误 (Internal server error)！")
                    print("🔄 正在强制刷新浏览器页面进行自愈重试...")
                    sb.refresh()
                    time.sleep(5)
                    sb.execute_script("window.scrollBy(0, 500);")
                    continue 
                
                print("🔍 寻找验证码弹窗...")
                anchor_iframe_xpath = '//iframe[contains(@src, "recaptcha/api2/anchor")]'
                
                if sb.is_element_visible(anchor_iframe_xpath):
                    print("✅ 成功加载出 reCAPTCHA 验证码框！")
                    
                    # 切换进 iframe 内部去点复选框
                    sb.switch_to_frame(anchor_iframe_xpath)
                    print("🖱️ 物理点击验证码复选框...")
                    sb.uc_click('#recaptcha-anchor')
                    time.sleep(4)
                    
                    # 检查是否变成对勾
                    checked = sb.get_attribute('#recaptcha-anchor', 'aria-checked')
                    sb.switch_to_default_content() # 切回主页面
                    
                    if checked != 'true':
                        print("🎲 触发验证挑战，调用破解器...")
                        bframe_xpath = '//iframe[contains(@src, "recaptcha/api2/bframe")]'
                        if sb.is_element_visible(bframe_xpath):
                            # 切入 challenge iframe
                            sb.switch_to_frame(bframe_xpath)
                            solver = RecaptchaAudioSolver(sb)
                            if not solver.solve():
                                msg = "❌ 破解未能通过"
                                print(msg)
                                sb.switch_to_default_content()
                                sb.save_screenshot('error_solver_fail.png')
                                return False, msg
                            sb.switch_to_default_content() # 破解完毕，切回主页面
                    else:
                        print("✨ 验证秒过！")
                        
                    solved_captcha = True
                    break
                else:
                    print("⚠️ 未加载出验证码弹窗。尝试按 ESC 清除可能的遮罩层...")
                    sb.press_keys('body', '\x1b') # 模拟按下 ESC
                    time.sleep(2)
            # ========================================================

            if solved_captcha:
                print("🚀 验证完成，点击弹窗中最终的 Renew 按钮...")
                final_renew_btn_xpath = '//button[normalize-space(text())="Renew"]'
                
                if sb.is_element_visible(final_renew_btn_xpath):
                    sb.uc_click(final_renew_btn_xpath)
                    print("⏳ 等待续期请求处理...")
                    time.sleep(8) 
                    
                    msg = "🎉 恭喜！服务器续期操作成功执行，时间已延长。"
                    print(msg)
                    success = True
                    sb.save_screenshot('success_renew.png')
                else:
                    msg = "❌ 找不到弹窗中的最终 Renew (紫色) 按钮"
                    print(msg)
                    sb.save_screenshot('error_no_final_btn.png')
            else:
                if not msg:
                    msg = "❌ 3次尝试均未能找到 reCAPTCHA iframe，放弃操作。"
                print(msg)
                sb.save_screenshot('error_no_iframe_final.png')

    except Exception as e:
        msg = f"💥 执行过程中出现异常: {e}"
        print(f"\n{msg}")
    finally:
        vdisplay.stop()
        print("Xvfb 虚拟桌面已关闭。")
        return success, msg

# ==============================================================================
# 程序主入口
# ==============================================================================
if __name__ == "__main__":
    renew_url = os.getenv("RENEW_URL")
    tg_token = os.getenv("TG_TOKEN")
    tg_chat_id = os.getenv("TG_CHAT_ID")
    
    # 确保走本地 Xray 代理
    proxy_url = "http://127.0.0.1:10808"
    
    if not renew_url:
        error_msg = "❌ 未找到环境变量 RENEW_URL，程序退出。请在 GitHub Secrets 中配置。"
        print(error_msg)
        send_tg_message(tg_token, tg_chat_id, f"❌ <b>续期任务失败</b>\n\n<b>原因：</b>缺少 RENEW_URL 环境变量。")
        sys.exit(1)
        
    print("🚀 开始执行自动续期任务...")
    
    is_success, result_message = renew_host2play(renew_url, proxy_url)
    
    if is_success:
        tg_msg = f"✅ <b>服务器续期成功</b>\n\n<b>详情：</b>{result_message}\n<b>状态：</b>时间已成功延长 8 小时。"
    else:
        tg_msg = f"❌ <b>服务器续期失败</b>\n\n<b>详情：</b>{result_message}\n<b>状态：</b>请登录 GitHub Actions 查看错误日志和截图。"
        
    send_tg_message(tg_token, tg_chat_id, tg_
