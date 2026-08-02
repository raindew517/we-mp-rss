# 微信读书公众号采集

当公众号后台接口不可用时，可以把采集模式切换为微信读书 Web。该模式直接请求 `weread.qq.com`，不经过第三方中转，并继续使用现有的 `MP_WXS_*` Feed ID 和 RSS 地址。

## 配置

1. 登录 `https://weread.qq.com`，打开任意公众号页面。
2. 在浏览器开发者工具的 Network 面板找到 `/web/mp/articles` 请求。
3. 从 Request Headers 复制完整 `Cookie` 和 `x-wr-ticket`。
4. 在管理页的“微信读书公众号采集”中保存，或设置环境变量：

```env
GATHER.MODEL=weread_mp
WEREAD_COOKIE=wr_vid=...; wr_skey=...; wr_rt=...
WEREAD_TICKET=...
WEREAD_MP_MAX_PAGES=20
WEREAD_PAGE_INTERVAL=1
WEREAD_CONTENT_INTERVAL=2
```

需要在 RSS 中直接显示全文时，同时设置：

```env
GATHER.CONTENT=True
```

## 行为

- 文章列表来自 `GET https://weread.qq.com/web/mp/articles`。
- 全文来自 `GET https://weread.qq.com/web/mp/content`，并提取 `#js_content`。
- 开启全文采集后，正文请求失败的文章不会以空正文入库，Feed 也不会被标记为同步完成；下一轮会继续补抓。
- `-2041`、`-2012` 和 `-2010` 会明确报告为认证或风控错误，不立即重试。
- 只有完整列表请求成功后才更新 Feed 同步时间；失败不会跳过文章。
- 定时任务会从最新一页继续翻页，直到追到该 Feed 上次成功的文章时间；单轮扫描页数由 `WEREAD_MP_MAX_PAGES` 限制。
- 列表翻页和全文请求默认分别间隔 1 秒、2 秒，降低触发微信读书风控的概率。

## 限制

`x-wr-ticket` 可能过期。出现 `-2041` 时，应从浏览器的新 `/web/mp/articles` 请求重新复制 ticket。通过环境变量提供的凭据优先于管理页保存值，管理页会标记为部署配置托管。微信读书也有访问频率限制，不建议把上述请求间隔设为 0。
