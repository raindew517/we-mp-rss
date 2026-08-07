"""微信读书 Cookie 自动刷新。

设计为「消息任务运行时的前置步骤」：在 jobs/mps.add_job() 同步文章之前无头调用，
复用数据卷中已登录的持久化 profile 自动刷新 Cookie 写回 wx.lic，使随后同步使用最新
凭据；若登录态过期（无头拿不到有效 Cookie），则沿用已有 Cookie 同步，由同步日志的
-2012 提示用户去本机重新扫码。

流程：
1. 用 Playwright Chromium 打开配置的公众号主页 URL（reader 页，形如
   https://weread.qq.com/web/mp/reader/xxxx，**不要配成带 bookId 的 /web/mp/articles
   接口地址**——接口地址会被重定向且不是给人看的页面）；
2. 主页内部会发出 /web/mp/articles 请求，从该请求头提取最新 Cookie（回退
   context.cookies 拼接）；
3. 写回 wx.lic 的 weread_data，并记录 cookie_refresh_last_ts（冷却用）；
4. 若 headless_only=False 且取不到有效 Cookie，弹可见窗口提示扫码登录，等待后更新。

注意：
- 直接读写 wx.lic（WEREAD_LIC_PATH 指定，默认 ./data/wx.lic）。
- 持久化 profile 目录由 WEREAD_PROFILE_DIR 指定，默认 ~/.cache/we-mp-rss/weread-chrome-profile；
  容器内部署应指向数据卷（与宿主扫码脚本共用同一物理目录），首次扫码后登录态持久化。
- 容器内调用传 headless_only=True + force_bundled=True（无 GUI 且用自带 Chromium）。
"""
import os
import json
import time

import yaml

DEFAULT_LIC_PATH = os.environ.get("WEREAD_LIC_PATH", "./data/wx.lic")
DEFAULT_PROFILE_DIR = os.environ.get(
    "WEREAD_PROFILE_DIR",
    os.path.expanduser("~/.cache/we-mp-rss/weread-chrome-profile"),
)


def _read_lic(lic_path: str = DEFAULT_LIC_PATH) -> dict:
    """直接读取 wx.lic（YAML），避免引入 core.config 的重依赖链。"""
    if not os.path.exists(lic_path):
        return {}
    with open(lic_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _write_lic(lic_path: str, doc: dict):
    with open(lic_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(doc, f, allow_unicode=True, sort_keys=False)


def _load_weread_data(lic_path: str = DEFAULT_LIC_PATH):
    """返回 (doc, data)，doc 为整个 YAML 文档，data 为 weread_data 字典。"""
    doc = _read_lic(lic_path)
    data = doc.get("weread_data", {})
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            data = {}
    return doc, data


def _save_cookie(cookie: str, name: str = "", lic_path: str = DEFAULT_LIC_PATH):
    """把最新 cookie 写回 wx.lic 的 weread_data（保留文档其他部分）。"""
    doc, data = _load_weread_data(lic_path)
    data["cookie"] = cookie
    if name:
        data["name"] = name
    data["cookie_refresh_last_ts"] = time.time()
    doc["weread_data"] = data
    _write_lic(lic_path, doc)


def extract_vid(cookie: str) -> str:
    """从 Cookie 字符串中提取 wr_vid。"""
    for item in (cookie or "").split(";"):
        item = item.strip()
        if item.startswith("wr_vid="):
            return item[len("wr_vid="):].strip()
    return ""


def _extract_cookie_from_page(page, context, url: str) -> str:
    """优先从 /web/mp/articles 请求头取 Cookie，回退 context.cookies 拼接。"""
    captured = {}

    def _on_request(request):
        if "web/mp/articles" in request.url:
            captured["cookie"] = request.headers.get("cookie", "")

    page.on("request", _on_request)
    try:
        page.goto(url, wait_until="networkidle", timeout=60000)
    except Exception as e:
        print(f"[refresh] 打开页面异常: {e}")
    # 优先使用 network 请求头中的 Cookie
    cookie = captured.get("cookie", "").strip()
    if cookie:
        return cookie
    # 回退：直接用 context 的 cookie jar 拼接
    try:
        cookies = context.cookies("https://weread.qq.com")
        return "; ".join(f"{c['name']}={c['value']}" for c in cookies)
    except Exception:
        return ""


def refresh_weread_cookie(verbose: bool = True, headless_only: bool = False,
                          force_bundled: bool = False, cooldown_hours: float = 6.0) -> bool:
    """执行一次 Cookie 自动刷新。成功更新（或确认仍新鲜）返回 True，否则 False。

    headless_only: True 时只做无头刷新，不在登录失效时弹窗扫码（容器内使用）。
    force_bundled: True 时忽略 browser_path，使用 Playwright 自带 Chromium
                   （容器内没有宿主机 Chrome 路径，且需与数据卷共享 profile）。
    cooldown_hours: 距离上次成功刷新不足该时长且已有 Cookie 时，视为仍有效，跳过刷新。
    """
    lic, data = _load_weread_data()
    url = (data.get("cookie_refresh_url") or "").strip()
    browser_path = (data.get("browser_path") or "").strip()
    browser_type = (data.get("browser_type") or "chrome").strip() or "chrome"

    if not url:
        if verbose:
            print("[refresh] 未配置 cookie_refresh_url，跳过自动刷新（请在微信读书配置页填写）")
        return False

    # 冷却：上次刷新成功且在冷却期内，且已有 Cookie，则视为仍有效，跳过
    if cooldown_hours and cooldown_hours > 0:
        last_ts = data.get("cookie_refresh_last_ts") or 0
        has_cookie = bool((data.get("cookie") or "").strip())
        if has_cookie and last_ts and (time.time() - float(last_ts)) < cooldown_hours * 3600:
            if verbose:
                print(f"[refresh] Cookie 在冷却期内（{cooldown_hours:g}h），跳过刷新")
            return True

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        if verbose:
            print("[refresh] 未安装 playwright，请执行: pip install playwright && playwright install chromium")
        return False

    profile_dir = DEFAULT_PROFILE_DIR
    os.makedirs(profile_dir, exist_ok=True)

    def _launch(p, headless: bool, force_bundled: bool = False):
        args = ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
        if force_bundled or not browser_path:
            return p.chromium.launch_persistent_context(profile_dir, headless=headless, args=args)
        return p.chromium.launch_persistent_context(
            profile_dir, headless=headless, executable_path=browser_path, args=args,
        )

    def _try(headless: bool, wait_login: bool = False, timeout_s: int = 300,
             force_bundled: bool = False) -> str:
        """打开页面并提取 Cookie；wait_login=True 时若未登录，保持窗口等待用户扫码。"""
        with sync_playwright() as p:
            context = _launch(p, headless=headless, force_bundled=force_bundled)
            page = context.new_page()
            try:
                cookie = _extract_cookie_from_page(page, context, url)
                if not cookie and wait_login:
                    # 保持可见窗口，轮询等待用户扫码登录（登录态持久化到 profile_dir）
                    deadline = time.time() + timeout_s
                    while time.time() < deadline:
                        try:
                            cookies = context.cookies("https://weread.qq.com")
                            ck = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
                        except Exception:
                            ck = ""
                        if "wr_vid=" in ck:
                            cookie = ck
                            break
                        time.sleep(2)
                return cookie
            finally:
                context.close()

    # 1) 常规无头刷新：登录态持久化，通常直接拿到有效 Cookie
    cookie = _try(headless=True, force_bundled=force_bundled)
    if cookie and "wr_vid=" in cookie:
        vid = extract_vid(cookie)
        _save_cookie(cookie, name=data.get("name", ""))
        if verbose:
            print(f"[refresh] Cookie 已自动更新 (vid={vid})")
        return True

    # 2) 未拿到有效 Cookie
    if headless_only:
        if verbose:
            print("[refresh] 无头刷新未获取到有效 Cookie（登录态可能已过期），将沿用已有 Cookie 进行同步")
        return False

    # 3) 弹可见窗口，提示扫码登录，等待登录后更新
    if verbose:
        print("[refresh] 未获取到有效 Cookie，已打开浏览器窗口，请扫码登录微信读书…")
        print("[refresh] 等待登录（最长 5 分钟），登录成功后自动保存 Cookie…")
    cookie = _try(headless=False, wait_login=True, timeout_s=300, force_bundled=force_bundled)
    if cookie and "wr_vid=" in cookie:
        vid = extract_vid(cookie)
        _save_cookie(cookie, name=data.get("name", ""))
        if verbose:
            print(f"[refresh] 扫码登录后 Cookie 已更新 (vid={vid})")
        return True

    if verbose:
        print("[refresh] 等待扫码超时或未获取到有效 Cookie，请检查微信读书登录状态")
    return False


if __name__ == "__main__":
    import sys

    ok = refresh_weread_cookie(verbose=True)
    sys.exit(0 if ok else 1)
