import os
import sys
import time
import random
import requests
from DrissionPage import ChromiumPage, ChromiumOptions
from xvfbwrapper import Xvfb

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
# 模拟人类行为辅助函数
# ==============================================================================
def human_type(element, text):
    """模拟人类点击输入框并逐字输入文字"""
    element.click()
    time.sleep(random.uniform(0.1, 0.3))
    element.clear()
    
    for char in text:
        element.input(char, clear=False)
        time.sleep(random.uniform(0.05, 0.2))
    
    time.sleep(random.uniform(0.3, 0.8))

def human_move_and_click(page, element):
    """模拟人类移动鼠标轨迹并点击"""
    try:
        page.actions.move_to(element, duration=random.uniform(0.5, 1.0))
        time.sleep(random.uniform(0.1, 0.3))
        element.click()
    except:
        element.click()

# ==============================================================================
# 语音验证码破解模块
# ==============================================================================
class RecaptchaAudioSolver:
    def __init__(self, page):
        self.page = page
        self.log_func = print

    def log(self, msg):
        self.log_func(f"[Solver] {msg}")

    def solve(self, iframe_ele):
        self.log("🎧 启动过盾流程...")
        try:
            # 尝试定位音频按钮
            audio_btn = iframe_ele.ele('css:#recaptcha-audio-button', timeout=5)
            if not audio_btn:
                self.log("❌ 未找到验证按钮，可能被 Google 屏蔽")
                return False
            
            audio_btn.click()
            time.sleep(random.uniform(3, 5))
            
            # 循环尝试获取音频源（增加重试次数）
            for attempt in range(3):
                src = self.get_audio_source(iframe_ele)
                if src:
                    break
                self.log(f"⚠️ 第 {attempt+1} 次获取TOKEN失败，尝试点击刷新...")
                reload_btn = iframe_ele.ele('css:#recaptcha-reload-button')
                if reload_btn:
                    reload_btn.click()
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
            input_box = iframe_ele.ele('css:#audio-response')
            if input_box:
                for char in key_text:
                    input_box.input(char, clear=False)
                    time.sleep(random.uniform(0.1, 0.2))
                
                time.sleep(1)
                iframe_ele.ele('css:#recaptcha-verify-button').click()
                self.log("🚀 提交验证...")
                time.sleep(3)
                return True
        except Exception as e:
            self.log(f"💥 异常: {e}")
            return False
        finally:
            for f in ["audio.mp3", "audio.wav"]:
                if os.path.exists(f): os.remove(f)

    def get_audio_source(self, iframe_ele):
        try:
            download_link = iframe_ele.ele('css:.rc-audiochallenge-ndownload-link') or \
                            iframe_ele.ele('xpath://a[contains(@href, ".mp3")]')
            return download_link.attr('href') if download_link else None
        except: return None

# ==============================================================================
# 核心续期业务逻辑 (纯物理点击 + 错误自愈版)
# ==============================================================================
def renew_host2play(url, proxy_url=None):
    print("启动 Xvfb 虚拟桌面...")
    vdisplay = Xvfb(width=1280, height=720, colordepth=24)
    vdisplay.start()
    
    page = None
    success = False
    msg = ""
    
    try:
        co = ChromiumOptions()
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-gpu')
        co.set_argument('--disable-dev-shm-usage')
        co.set_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
        if proxy_url:
            co.set_proxy(proxy_url)
        
        page = ChromiumPage(co)
        page.run_js('Object.defineProperty(navigator, "webdriver", {get: () => undefined})')
        
        print(f"🌐 访问续期目标网址: {url}")
        page.get(url)
        
        # ================= 触发续期弹窗循环 (加入自愈机制) =================
        checkbox_frame = None
        for attempt in range(3):
            print(f"\n⚡ 第 {attempt+1} 次尝试获取验证码弹窗...")
            print("⏳ 等待页面加载...")
            time.sleep(3) 
            
            print("📜 向下滚动页面...")
            page.scroll.down(500)
            time.sleep(1)

            print("🔍 寻找精确的 'Renew server' 按钮...")
            first_renew_btn = page.ele('xpath://button[normalize-space(text())="Renew server"]', timeout=15)
            
            if not first_renew_btn:
                msg = "❌ 未找到初始的 'Renew server' 按钮 (button 标签)"
                print(msg)
                # 应对极端情况：如果一开始就显示了报错页面，尝试点刷新
                refresh_btn = page.ele('text:Refresh page', timeout=2)
                if refresh_btn:
                    print("🔄 发现 'Refresh page' 按钮，正在点击重置页面状态...")
                    human_move_and_click(page, refresh_btn)
                    time.sleep(5)
                    continue
                else:
                    page.get_screenshot(path='.', name=f'error_no_first_btn_{attempt}.png')
                    break # 真的找不到，跳出循环
                
            # 将找出的按钮强制滚动到屏幕视口正中间
            try:
                first_renew_btn.scroll.to_see(center=True)
                time.sleep(1)
            except Exception as e:
                print(f"⚠️ 滚动居中时出现小警告(不影响后续): {e}")
                
            print(f"🖱️ 尝试物理点击初始 'Renew server' 按钮...")
            human_move_and_click(page, first_renew_btn)
            time.sleep(5) # 给弹窗或者报错提示加载的时间
            
            # --- 新增的错误自愈检测机制 ---
            # 检测是否出现了 500 Internal Server Error 导致的 Refresh page 按钮
            refresh_btn = page.ele('text:Refresh page', timeout=3)
            if refresh_btn:
                print("💥 检测到服务器内部错误 (Internal server error)！")
                print("🔄 正在点击 'Refresh page' 按钮进行自愈重试...")
                human_move_and_click(page, refresh_btn)
                time.sleep(5)
                continue # 刷新后，直接进入下一次循环重试
            
            print("🔍 寻找验证码弹窗...")
            checkbox_frame = page.get_frame('@src*:recaptcha/api2/anchor', timeout=6)
            
            if checkbox_frame:
                print("✅ 成功加载出 reCAPTCHA 验证码框！")
                break
            else:
                print("⚠️ 未加载出验证码弹窗。尝试按 ESC 清除可能的遮罩层...")
                page.actions.key_down('ESCAPE').key_up('ESCAPE')
                time.sleep(2)
        # ========================================================

        if checkbox_frame:
            checkbox = checkbox_frame.ele('#recaptcha-anchor', timeout=10)
            if checkbox:
                print("🖱️ 物理点击验证码复选框...")
                human_move_and_click(page, checkbox)
                time.sleep(4)
                
                if checkbox.attr('aria-checked') != 'true':
                    print("🎲 触发验证挑战，调用破解器...")
                    challenge_frame = page.get_frame('@src*:recaptcha/api2/bframe', timeout=10)
                    if challenge_frame:
                        solver = RecaptchaAudioSolver(page)
                        if not solver.solve(challenge_frame):
                            msg = "❌ 破解未能通过"
                            print(msg)
                            page.get_screenshot(path='.', name='error_solver_fail.png')
                            return False, msg
                else:
                    print("✨ 验证秒过！")
                
                print("🚀 验证完成，点击弹窗中最终的 Renew 按钮...")
                final_renew_btn = page.ele('xpath://button[normalize-space(text())="Renew"]', timeout=10) 
                
                if final_renew_btn:
                    human_move_and_click(page, final_renew_btn)
                    print("⏳ 等待续期请求处理...")
                    time.sleep(8) 
                    
                    msg = "🎉 恭喜！服务器续期操作成功执行，时间已延长。"
                    print(msg)
                    success = True
                    page.get_screenshot(path='.', name='success_renew.png')
                else:
                    msg = "❌ 找不到弹窗中的最终 Renew (紫色) 按钮"
                    print(msg)
            else:
                msg = "❌ iframe 中未能找到 reCAPTCHA checkbox"
                print(msg)
        else:
            msg = "❌ 3次尝试均未能找到 reCAPTCHA iframe，放弃操作。"
            print(msg)
            page.get_screenshot(path='.', name='error_no_iframe_final.png')

    except Exception as e:
        msg = f"💥 执行过程中出现异常: {e}"
        print(f"\n{msg}")
        if page:
            try:
                page.get_screenshot(path='.', name='error_final.png')
            except:
                pass
    finally:
        if page:
            page.quit()
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
