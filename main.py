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
    if not token or not chat_id:
        print("未配置 TG_TOKEN 或 TG_CHAT_ID，跳过通知。")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    safe_message = message.replace('<b>', '').replace('</b>', '')
    payload = {"chat_id": chat_id, "text": safe_message, "parse_mode": "None"}
    try:
        requests.post(url, json=payload, timeout=10)
        print("✅ Telegram 通知发送成功！")
    except Exception as e:
        print(f"❌ Telegram 通知请求异常: {e}")

# ==============================================================================
# 语音验证码破解模块 (深度融合仿人类行为与容错逻辑)
# ==============================================================================
class RecaptchaAudioSolver:
    def __init__(self, sb):
        self.sb = sb
        self.log_func = print

    def log(self, msg):
        self.log_func(f"[Solver] {msg}")

    def human_type(self, selector, text):
        """完全模拟人类的不规则打字节奏"""
        self.sb.click(selector)
        time.sleep(random.uniform(0.1, 0.3))
        # SeleniumBase 的 type/add_text 默认会清空或直接追加，这里模拟逐字敲击
        for char in text:
            # 使用 send_keys 模拟真实键盘敲击
            self.sb.send_keys(selector, char)
            time.sleep(random.uniform(0.08, 0.25))
        time.sleep(random.uniform(0.3, 0.8))

    def solve(self):
        self.log("🎧 启动过盾流程...")
        try:
            # 引入随机悬停，避免坐标瞬移
            if self.sb.is_element_visible('#recaptcha-audio-button'):
                self.sb.hover('#recaptcha-audio-button')
                time.sleep(random.uniform(0.5, 1.2))
                self.sb.click('#recaptcha-audio-button')
                self.log("🖱️ 点击了音频破解按钮")
            else:
                self.log("❌ 未找到验证按钮，可能被 Google 屏蔽")
                return False

            time.sleep(random.uniform(3, 5))

            src = None
            for attempt in range(3):
                src = self.get_audio_source()
                if src:
                    break
                
                # 检查是否被 Google 直接弹出红色错误提示（吸取第一个代码的经验）
                if self.sb.is_element_visible('.rc-audiochallenge-error-message'):
                    error_txt = self.sb.get_text('.rc-audiochallenge-error-message')
                    if error_txt and "try again" not in error_txt.lower():
                        self.log(f"⛔ Google 拒绝提供音频: {error_txt}")
                
                self.log(f"⚠️ 第 {attempt+1} 次获取TOKEN失败，尝试点击刷新...")
                if self.sb.is_element_visible('#recaptcha-reload-button'):
                    self.sb.hover('#recaptcha-reload-button')
                    time.sleep(random.uniform(0.3, 0.8))
                    self.sb.click('#recaptcha-reload-button')
                    time.sleep(random.uniform(4, 7)) # 刷新后多等一会

            if not src:
                self.log("❌ 最终无法获取链接 (IP 可能被暂时风控)")
                return False

            self.log("📥 正在下载并处理音频数据...")
            r = requests.get(src, timeout=15)
            with open("audio.mp3", 'wb') as f:
                f.write(r.content)

            try:
                sound = AudioSegment.from_mp3("audio.mp3")
                sound.export("audio.wav", format="wav")
            except Exception as e:
                self.log(f"❌ ffmpeg 转码失败: {e}")
                return False

            key_text = ""
            recognizer = sr.Recognizer()
            with sr.AudioFile("audio.wav") as source:
                audio_data = recognizer.record(source)
                try:
                    key_text = recognizer.recognize_google(audio_data)
                    self.log(f"🗣️ 识别结果: [{key_text}]")
                except Exception as e:
                    self.log("❌ 语音识别失败 (可能音频含糊或引擎无响应)")
                    return False

            if self.sb.is_element_visible('#audio-response'):
                # 替换掉原有的机械输入，使用仿人类输入
                self.human_type('#audio-response', key_text)
                
                self.sb.hover('#recaptcha-verify-button')
                time.sleep(random.uniform(0.5, 1.0))
                self.sb.click('#recaptcha-verify-button')
                self.log("🚀 提交验证...")
                time.sleep(4)
                
                # 验证是否通过
                if self.sb.is_element_visible('.rc-audiochallenge-error-message'):
                    err = self.sb.get_text('.rc-audiochallenge-error-message')
                    if err:
                        self.log(f"❌ 验证未通过: {err}")
                        return False
                
                return True
            return False

        except Exception as e:
            self.log(f"💥 异常: {e}")
            return False
        finally:
            for f in ["audio.mp3", "audio.wav"]:
                if os.path.exists(f):
                    os.remove(f)

    def get_audio_source(self):
        try:
            if self.sb.is_element_visible('.rc-audiochallenge-ndownload-link'):
                return self.sb.get_attribute('.rc-audiochallenge-ndownload-link', 'href')
            elif self.sb.is_element_visible('xpath', '//a[contains(@href, ".mp3")]'):
                return self.sb.get_attribute('xpath', '//a[contains(@href, ".mp3")]', 'href')
            elif self.sb.is_element_visible('#audio-source'):
                return self.sb.get_attribute('#audio-source', 'src')
            return None
        except:
            return None

# ==============================================================================
# 核心续期业务逻辑
# ==============================================================================
def renew_host2play(url, proxy_url=None):
    print("启动 Xvfb 虚拟桌面...")
    vdisplay = Xvfb(width=1280, height=720, colordepth=24)
    vdisplay.start()

    success = False
    msg = ""

    try:
        # 增加隐蔽性参数
        with SB(uc=True, proxy=proxy_url, headless=False, browser="chrome", 
                uc_cdp_events=True,  # 增强对反爬虫的绕过
                disable_csp=True) as sb:
            
            print(f"🌐 访问续期目标网址: {url}")
            sb.uc_open_with_reconnect(url, 5)
            time.sleep(random.uniform(5, 8))

            print("🧹 清理遮挡元素...")
            sb.execute_script("""
                const cssSelectors = ['ins.adsbygoogle', 'iframe[src*="ads"]', '.modal-backdrop'];
                cssSelectors.forEach(sel => {
                    document.querySelectorAll(sel).forEach(el => el.remove());
                });
            """)
            time.sleep(2)

            try:
                if sb.is_element_visible('button:contains("Consent")'):
                    sb.uc_click('button:contains("Consent")')
                    time.sleep(3)
            except:
                pass

            sb.execute_script("window.scrollBy(0, 500);")
            time.sleep(random.uniform(1.0, 2.5))

            print("🖱️ 打开续期弹窗...")
            try:
                sb.uc_click('//button[contains(text(), "Renew server")]')
            except:
                sb.execute_script("document.querySelectorAll('button').forEach(b => {if(b.textContent.includes('Renew server')) b.click();});")
            time.sleep(3)

            for i in range(8):
                if sb.is_text_visible("Expires in:") or sb.is_text_visible("Deletes on:"):
                    break
                time.sleep(1)

            try:
                sb.uc_click('button:contains("Renew server")')
            except:
                pass
            
            # 给验证码充分的加载时间，并引入随机波动
            time.sleep(random.uniform(7, 10))   

            solved_captcha = False
            anchor_iframe_xpath = '//iframe[contains(@src, "recaptcha/api2/anchor")]'

            if sb.is_element_visible(anchor_iframe_xpath):
                print("✅ 锁定 reCAPTCHA 框架")
                sb.switch_to_frame(anchor_iframe_xpath)

                for _ in range(20):
                    if sb.is_element_visible('#recaptcha-anchor'):
                        break
                    time.sleep(1)
                else:
                    msg = "❌ reCAPTCHA checkbox 超时"
                    sb.switch_to_default_content()
                    return success, msg

                # ========================================================
                # 🚨 核心改动：废弃高风险的 JS 派发事件，改为物理拟人点击
                # ========================================================
                print("🖱️ 物理模拟点击 reCAPTCHA checkbox...")
                sb.hover('#recaptcha-anchor')
                time.sleep(random.uniform(0.5, 1.5))
                # 使用标准的 click 而不是 JS，触发浏览器的真实 Trusted Event
                sb.click('#recaptcha-anchor')
                time.sleep(random.uniform(4, 7))

                checked = sb.get_attribute('#recaptcha-anchor', 'aria-checked')
                sb.switch_to_default_content()

                if checked == 'true':
                    print("✅ reCAPTCHA 已自动验证通过！")
                    solved_captcha = True
                else:
                    print("🎲 需要手动破解音频验证码...")
                    bframe_xpath = '//iframe[contains(@src, "recaptcha/api2/bframe")]'
                    if sb.is_element_visible(bframe_xpath):
                        sb.switch_to_frame(bframe_xpath)
                        solver = RecaptchaAudioSolver(sb)
                        if solver.solve():
                            solved_captcha = True
                        sb.switch_to_default_content()
            else:
                print("⚠️ 未发现 reCAPTCHA iframe")

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
                msg = "❌ 无法通过 reCAPTCHA"

    except Exception as e:
        msg = f"💥 运行异常: {str(e)[:200]}"
        print(msg)
    finally:
        vdisplay.stop()
        return success, msg

if __name__ == "__main__":
    renew_url = os.getenv("RENEW_URL")
    tg_token = os.getenv("TG_TOKEN")
    tg_chat_id = os.getenv("TG_CHAT_ID")
    proxy_url = "http://127.0.0.1:10808"

    if not renew_url:
        print("❌ 缺少 RENEW_URL")
        sys.exit(1)

    is_success, result_message = renew_host2play(renew_url, proxy_url)
    send_tg_message(tg_token, tg_chat_id, result_message)
    if not is_success: sys.exit(1)
