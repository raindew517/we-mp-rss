#!/usr/bin/env python3
"""宿主机入口：微信读书 Cookie 自动刷新（仅用于首次 / 偶尔过期时的扫码）。

说明：
- 日常自动刷新已经改为「消息任务运行时的前置步骤」，由容器内的 jobs/mps.run()
  以无头方式调用 core.weread_cookie_refresh.refresh_weread_cookie()，复用数据卷中
  已登录的持久化 profile，无需人工干预。
- 本脚本只用于「首次建立登录态」或「登录态过期后重新扫码」：在本机终端前台运行，
  会弹出可见浏览器窗口，扫码登录一次后登录态持久化到数据卷共享 profile，容器之后
  即可无头复用。
- 通过 WEREAD_LIC_PATH 指向容器挂载的数据卷 wx.lic；通过 WEREAD_PROFILE_DIR 指向
  数据卷中的共享 profile 目录（与容器内刷新使用的是同一物理目录）。

用法：
    python scripts/refresh_weread_cookie.py
"""
import os
import sys

# 日志实时落盘（launchd 场景下 stdout 重定向为文件时避免全缓冲滞后）
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

# 让脚本能 import 项目的 core 包
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# 指向宿主机上容器挂载的数据卷 wx.lic（默认，可被环境变量覆盖）
os.environ.setdefault("WEREAD_LIC_PATH", "/Users/yangqing/wechat-rss-data/wx.lic")
# 与容器内刷新共用的持久化登录 profile 目录（同一物理数据卷），首次扫码后容器即可无头复用
os.environ.setdefault("WEREAD_PROFILE_DIR", "/Users/yangqing/wechat-rss-data/weread-chrome-profile")

from core.weread_cookie_refresh import refresh_weread_cookie  # noqa: E402


if __name__ == "__main__":
    ok = refresh_weread_cookie(verbose=True)
    sys.exit(0 if ok else 1)
