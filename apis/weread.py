"""
微信读书(Weread)管理 API

提供 Cookie 配置、连接测试、手动采集等功能
"""

import json
import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from .base import success_response, error_response
from core.auth import get_current_user_or_ak, get_current_user
from core.config import Config
from driver.weread_qr import WereadQRLogin

router = APIRouter(prefix="/weread", tags=["微信读书"])


class WereadCookieRequest(BaseModel):
    cookie: str
    vid: Optional[str] = ""
    name: Optional[str] = ""


class WereadCollectRequest(BaseModel):
    mp_id: str
    mp_name: Optional[str] = ""
    faker_id: Optional[str] = ""  # 书籍 bookId，为空则采集全部书架
    max_page: int = 1
    gather_content: bool = True


def _get_weread_config() -> Config:
    """获取微信读书配置文件"""
    lic_path = "./data/wx.lic"
    os.makedirs(os.path.dirname(lic_path), exist_ok=True)
    if not os.path.exists(lic_path):
        with open(lic_path, "w") as f:
            f.write("{}")
    return Config(lic_path)


def _load_weread_data() -> dict:
    """加载微信读书数据"""
    cfg = _get_weread_config()
    data = cfg.get("weread_data", {})
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            data = {}
    return data


def _save_weread_data(data: dict):
    """保存微信读书数据"""
    cfg = _get_weread_config()
    cfg.set("weread_data", data)
    cfg.save_config()
    cfg.reload()


@router.get("", summary="获取微信读书配置状态")
async def get_weread_status(current_user=Depends(get_current_user_or_ak)):
    """获取当前微信读书 Cookie 的配置状态"""
    data = _load_weread_data()
    cookie = data.get("cookie", "")
    vid = data.get("vid", "")
    name = data.get("name", "")

    # 判断是否已配置
    has_cookie = bool(cookie and vid)

    return success_response({
        "configured": has_cookie,
        "cookie_masked": cookie[:20] + "..." if cookie else "",
        "has_cookie": bool(cookie),
        "vid": vid,
        "name": name,
    })


@router.post("/cookie", summary="保存微信读书 Cookie")
async def save_weread_cookie(
    req: WereadCookieRequest,
    current_user=Depends(get_current_user_or_ak),
):
    """
    保存微信读书 Cookie
    
    所需 Cookie: wr_vid, wr_skey, wr_gid, wr_fp 等
    可以从浏览器 weread.qq.com 的请求中获取
    """
    if not req.cookie or not req.cookie.strip():
        return error_response(400, "Cookie 不能为空")

    cookie_str = req.cookie.strip()

    # 提取 vid
    vid = req.vid.strip()
    if not vid:
        for item in cookie_str.split(";"):
            item = item.strip()
            if item.startswith("wr_vid="):
                vid = item.replace("wr_vid=", "").strip()
                break

    if not vid:
        return error_response(400, "Cookie 中未找到 wr_vid，请检查 Cookie 格式")

    data = _load_weread_data()
    data["cookie"] = cookie_str
    data["vid"] = vid
    data["name"] = req.name.strip() or data.get("name", "")

    _save_weread_data(data)

    return success_response({
        "vid": vid,
        "name": data.get("name", ""),
    }, "Cookie 保存成功")


@router.post("/test", summary="测试微信读书连接")
async def test_weread_connection(current_user=Depends(get_current_user_or_ak)):
    """
    测试微信读书 Cookie 是否有效
    会尝试获取书架数据来验证
    """
    from core.wx.model.weread import MpsWeread

    wx = MpsWeread()
    result = wx.test_auth()

    if result["ok"]:
        return success_response(result, f"连接成功，书架共 {result['book_count']} 本书")
    else:
        return error_response(400, result.get("error", "连接失败"), result)


@router.post("/bookshelf", summary="获取书架书籍列表")
async def get_bookshelf(current_user=Depends(get_current_user_or_ak)):
    """
    获取微信读书书架上的所有书籍
    用于选择要采集哪本书的笔记
    """
    from core.wx.model.weread import MpsWeread

    wx = MpsWeread()
    wx._load_weread_auth()

    if not wx._weread_cookies:
        return error_response(400, "请先配置微信读书 Cookie")

    if not wx._weread_vid:
        return error_response(400, "无法从 Cookie 提取 vid")

    books = wx._get_shelf_books()
    if books is None:
        return error_response(500, "获取书架失败，Cookie 可能已过期")

    return success_response({
        "total": len(books),
        "books": books,
    })


@router.post("/collect", summary="手动采集微信读书笔记")
async def collect_weread_notes(
    req: WereadCollectRequest,
    current_user=Depends(get_current_user_or_ak),
):
    """
    手动触发微信读书笔记采集

    如果指定了 faker_id (bookId)，则只采集该书的笔记
    如果未指定，则采集整个书架上所有书的笔记
    """
    if not req.mp_id:
        return error_response(400, "mp_id 不能为空")

    from core.wx.model.weread import MpsWeread
    from core.models import Article

    wx = MpsWeread()
    wx._load_weread_auth()

    if not wx._weread_cookies:
        return error_response(400, "请先配置微信读书 Cookie")

    articles = []

    def save_callback(data: dict) -> bool:
        """回调：将笔记存入数据库"""
        from core.db import DB
        from datetime import datetime

        try:
            art = {
                "id": data.get("id", ""),
                "mp_id": data.get("mp_id", ""),
                "title": data.get("title", ""),
                "url": data.get("url", data.get("link", "")),
                "pic_url": data.get("cover", data.get("pic_url", "")),
                "content": data.get("content", ""),
                "publish_time": data.get("update_time", 0),
            }
            # 直接使用 DB 添加文章
            DB.add_article(art, check_exist=True)
            articles.append(art)
            return True
        except Exception as e:
            from core.print import print_error
            print_error(f"保存笔记失败: {e}")
            return False

    wx.get_Articles(
        faker_id=req.faker_id or None,
        Mps_id=req.mp_id,
        Mps_title=req.mp_name or req.faker_id or "微信读书",
        CallBack=save_callback,
        MaxPage=1,
        interval=3,
        Gather_Content=req.gather_content,
    )

    return success_response({
        "collected": len(articles),
        "articles": articles[:20],  # 只返回前20条
    }, f"采集完成，共 {len(articles)} 条笔记")


@router.delete("/cookie", summary="清除微信读书 Cookie")
async def clear_weread_cookie(current_user=Depends(get_current_user_or_ak)):
    """清除已保存的微信读书 Cookie"""
    data = _load_weread_data()
    data["cookie"] = ""
    data["vid"] = ""
    # 保留 name
    _save_weread_data(data)

    return success_response(message="Cookie 已清除")


# ---- 微信读书扫码授权 API ----

def _weread_qr_callback(result: dict):
    """
    扫码成功后的回调：将 Cookie 保存到 data/wx.lic
    此函数由 driver/weread_qr.py 在登录成功时自动调用
    """
    pass  # 保存逻辑已在 WereadQRLogin._save_cookies_to_lic 中实现


@router.get("/qr/code", summary="获取微信读书登录二维码")
async def get_weread_qrcode(current_user=Depends(get_current_user)):
    """
    获取微信读书扫码登录二维码
    返回二维码图片 URL（本地静态路径或外部链接）
    """
    wr_qr = WereadQRLogin()

    def on_login_success(result: dict):
        """登录成功回调"""
        print("Weread QR 登录成功，Cookie 已自动保存")
        _weread_qr_callback(result)

    code_url = wr_qr.GetCode(CallBack=on_login_success)
    if not code_url:
        return error_response(500, "获取二维码失败，请稍后重试")

    # 如果是本地文件路径，转为前端可访问的 /static/ 路径
    if code_url.startswith("static/") or code_url.startswith("./static/"):
        code_url = "/" + code_url.lstrip("./")

    return success_response({"code": code_url, "uid": wr_qr._uid})


@router.get("/qr/image", summary="获取微信读书二维码图片状态")
async def weread_qr_image(current_user=Depends(get_current_user)):
    """检查二维码图片是否存在"""
    wr_qr = WereadQRLogin()
    return success_response(wr_qr.GetHasCode())


@router.get("/qr/status", summary="获取微信读书扫码状态")
async def weread_qr_status(current_user=Depends(get_current_user)):
    """
    轮询微信读书扫码登录状态

    返回:
    - login_status: bool - 是否登录成功
    - code_url: str - 二维码 URL
    - msg: str - 状态消息
    - data: dict - 登录数据（成功后包含 vid, accessToken, cookies 等）
    """
    wr_qr = WereadQRLogin()
    status = wr_qr.QrStatus()
    return success_response(status)


@router.get("/qr/over", summary="微信读书扫码完成")
async def weread_qr_over(current_user=Depends(get_current_user)):
    """
    扫码登录完成后调用，清理状态并返回登录结果
    """
    wr_qr = WereadQRLogin()
    result = await wr_qr.Close()
    return success_response(result)
