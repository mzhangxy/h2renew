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
# Telegram 通知模块 (修复 400 错误版)
# ==============================================================================
def send_tg_message(token, chat_id, message):
    """发送 Telegram 通知，增加安全过滤"""
    if not token or not chat_id:
        print("未配置 TG_TOKEN 或 TG_CHAT_ID，跳过通知。")
        return
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    # 移除 HTML 标签或确保格式简单，避免解析错误
    safe_message = message.replace('<b>', '').replace('</b>', '')
    
    payload = {
        "chat_id": chat_id,
        "text": safe_message,
        "parse_mode": "None" # 临时改用纯文本模式确保送达
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Telegram 通知发送成功！")
        else:
            print(f"❌ Telegram 通知发送失败，状态码: {response.status_code}, 响应: {response.text}")
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
# 核心续期业务逻辑 (SeleniumBase 稳定增强版)
# ==============================================================================
def renew_host2play(url, proxy_url=None):
    print("启动 Xvfb 虚拟桌面...")
    vdisplay = Xvfb(width=1280, height=720, colordepth=24)
    vdisplay.start()
    
    success = False
    msg = ""
    
    try:
        # 使用更长的延迟和更强的探测模式
        with SB(uc=True, proxy=proxy_url, headless=False, browser="chrome") as sb:
            print(f"🌐 访问续期目标网址: {url}")
            sb.uc_open_with_reconnect(url, 5) 
            
            print("⏳ 等待页面初步加载...")
            time.sleep(6) 

            print("🧹 正在清理页面广告干扰...")
            sb.execute_script("""
                const selectors = ['iframe[src*="googleads"]', 'ins.adsbygoogle', 'div[id^="google_ads"]', '.ad-container', '#dismiss-button'];
                selectors.forEach(s => document.querySelectorAll(s).forEach(el => el.remove()));
            """)
            
            print("📜 向下滚动页面...")
            sb.execute_script("window.scrollBy(0, 480);")
            time.sleep(2)

            first_btn_xpath = '//button[normalize-space(text())="Renew server"]'
            
            solved_captcha = False
            for attempt in range(3):
                print(f"\n⚡ 第 {attempt+1} 次尝试获取验证码弹窗...")
                
                if not sb.is_element_visible(first_btn_xpath):
                    print("⚠️ 按钮不可见，尝试刷新...")
                    sb.refresh()
                    time.sleep(6)
                    sb.execute_script("window.scrollBy(0, 480);")
                        
                print(f"🖱️ 尝试物理点击初始 'Renew server' 按钮...")
                try:
                    # 尝试先聚焦再点击
                    sb.focus(first_btn_xpath)
                    time.sleep(1)
                    sb.uc_click(first_btn_xpath)
                except Exception as e:
                    print(f"⚠️ 点击异常，尝试 JS 备用点击: {e}")
                    sb.execute_script(f"document.evaluate('{first_btn_xpath}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click();")
                
                time.sleep(7) # 增加等待弹窗的时间
                
                print("🔍 寻找验证码弹窗...")
                anchor_iframe_xpath = '//iframe[contains(@src, "recaptcha/api2/anchor")]'
                
                if sb.is_element_visible(anchor_iframe_xpath):
                    print("✅ 成功加载出 reCAPTCHA 验证码框！")
                    sb.switch_to_frame(anchor_iframe_xpath)
                    sb.uc_click('#recaptcha-anchor')
                    time.sleep(5)
                    
                    checked = sb.get_attribute('#recaptcha-anchor', 'aria-checked')
                    sb.switch_to_default_content() 
                    
                    if checked != 'true':
                        print("🎲 触发验证挑战，调用破解器...")
                        bframe_xpath = '//iframe[contains(@src, "recaptcha/api2/bframe")]'
                        if sb.is_element_visible(bframe_xpath):
                            sb.switch_to_frame(bframe_xpath)
                            solver = RecaptchaAudioSolver(sb)
                            if not solver.solve():
                                msg = "❌ 验证破解失败"
                                sb.switch_to_default_content()
                                continue
                            sb.switch_to_default_content() 
                    
                    solved_captcha = True
                    break
                else:
                    print("⚠️ 未发现弹窗，记录截图...")
                    sb.save_screenshot(f'debug_click_attempt_{attempt}.png')
                    sb.press_keys('body', '\x1b') 
                    time.sleep(2)

            if solved_captcha:
                print("🚀 验证完成，点击最终 Renew...")
                final_btn = '//button[normalize-space(text())="Renew"]'
                if sb.is_element_visible(final_btn):
                    sb.uc_click(final_btn)
                    time.sleep(10)
                    msg = "🎉 续期操作成功！"
                    success = True
                else:
                    msg = "❌ 找不到最终 Renew 按钮"
            else:
                msg = "❌ 无法唤出验证码弹窗"

    except Exception as e:
        msg = f"💥 运行异常: {str(e)[:100]}"
    finally:
        vdisplay.stop()
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
        
    send_tg_message(tg_token, tg_chat_id, tg_msg)
    
    if not is_success:
        sys.exit(1)
