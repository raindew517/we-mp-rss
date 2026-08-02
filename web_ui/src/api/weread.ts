import http from './http'

/** 获取微信读书配置状态 */
export async function getWereadStatus() {
    return http.get('weread')
}

/** 保存微信读书 Cookie */
export async function saveWereadCookie(cookie?: string, vid?: string, name?: string, ticket?: string) {
    return http.post('weread/cookie', { cookie, vid, name, ticket })
}

/** 测试连接 */
export async function testWereadConnection() {
    return http.post('weread/test')
}

/** 测试微信读书公众号列表凭据 */
export async function testWereadMpConnection(mpId?: string) {
    return http.post('weread/mp/test', { mp_id: mpId || '' })
}

/** 获取书架列表 */
export async function getWereadBookshelf() {
    return http.post('weread/bookshelf')
}

/** 手动采集笔记 */
export async function collectWereadNotes(params: {
    mp_id: string
    mp_name?: string
    faker_id?: string
    max_page?: number
    gather_content?: boolean
}) {
    return http.post('weread/collect', params)
}

/** 清除 Cookie */
export async function clearWereadCookie() {
    return http.delete('weread/cookie')
}
