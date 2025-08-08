<template>
  <a-layout class="app-container">
    <!-- 头部 -->
    <a-layout-header class="app-header" v-if="route.path !== '/login'">
      <div class="header-left">
        <div class="logo">
          <img  :src="logo" alt="avatar" :width="60" style="margin-right:1rem;">
          <router-link to="/">{{appTitle}}</router-link>
          <a-tooltip  v-if="hasLogined" content="点我扫码授权" position="bottom">
            <icon-scan  @click="showAuthQrcode()"  style="margin-left: 10px; cursor: pointer;color: #000;" />
          </a-tooltip>
        </div>
         <a-tooltip  v-if="hasLogined" content="Switch Language" position="bottom">
          <a-dropdown  trigger="click" position="br">
            <icon-translate size="24" style="cursor: pointer;"/>
          <template #content>
            <a-doption :selected="currentLanguage === 'english'" @click="() => handleLanguageChange('english')">
              英文
            </a-doption>
            <a-doption :selected="currentLanguage === 'chinese_simplified'" @click="() => handleLanguageChange('chinese_simplified')">
              中文
            </a-doption>
          </template>
        </a-dropdown>
      </a-tooltip>
      </div>
      <div class="header-right" v-if="hasLogined">
        <a-link href="/api/docs" target="_blank" style="margin-right: 20px;">Docs</a-link>
        <a-link href="https://gitee.com/rachel_os/we-mp-rss" target="_blank" style="margin-right: 20px;">Gitee</a-link>
        <a-link href="https://github.com/rachelos/we-mp-rss" target="_blank" style="margin-right: 20px;">GitHub</a-link>
        <a-tooltip content="GitHub或者Google账户注册登录，获得首月5美元奖励。注册180+天的GitHub账户还可以解锁每月5美元的额度赠送。" position="bottom">
        <a-link href="https://console.run.claw.cloud/signin?link=FJ0VXS42W2P9" target="_blank" style="margin-right: 20px;">ClawCloud</a-link>
        </a-tooltip>
        <a-tooltip content="如果您需要部署此项目，建议采用腾讯云服务器，您懂得" position="bottom">
          <a-link href="https://cloud.tencent.com/act/cps/redirect?redirect=2446&cps_key=f8ce741e7b24cd68141ab2115122ea94&from=console" target="_blank" style="margin-right: 20px;">云部署</a-link>
        </a-tooltip>
        <a-tooltip content="您的支持是作者的最大动力，来一杯咖啡吧" position="bottom">
          <a-link @click="showSponsorModal" style="margin-right: 20px; cursor: pointer;" type="text">支持</a-link>
        </a-tooltip>
        <a-link href="https://www.paypal.com/ncp/payment/PUA72WYLAV5KW" target="_blank" style="margin-right: 20px;">赞助</a-link>
        
     

        <a-dropdown position="br" trigger="click">
          <div class="user-info">
            <a-avatar :size="36">
              <img v-if="userInfo.avatar" :src="userInfo.avatar" alt="avatar">
              <icon-user v-else />
            </a-avatar>
            <span class="username">{{ userInfo.username }}</span>
          </div>
          <template #content>
            <a-doption @click="goToEditUser">
              <template #icon><icon-user /></template>
              个人中心
            </a-doption>
            <a-doption @click="goToChangePassword">
              <template #icon><icon-lock /></template>
              修改密码
            </a-doption>
            <a-doption @click="showAuthQrcode">
              <template #icon><icon-scan /></template>
              扫码授权
            </a-doption>
            <a-doption @click="handleLogout">
              <template #icon><icon-user /></template>
              退出登录
            </a-doption>
          </template>
        </a-dropdown>
        <WechatAuthQrcode ref="qrcodeRef" />
        <a-modal v-model:visible="sponsorVisible" title="感谢支持" :footer="false" :style="{zIndex: 1000}" unmount-on-close>
          <div style="text-align: center;">
            <p>如果您觉得这个项目对您有帮助,请给Rachel来一杯Coffee吧~ </p>
            <img src="@/assets/images/sponsor.jpg" alt="赞赏码" style="max-width: 300px; margin-top: 20px;">
          </div>
        </a-modal>
      </div>
    </a-layout-header>

    <a-layout>

      <!-- 主内容区 -->
      <a-layout>
        <a-layout-content class="app-content">
          <router-view />
        </a-layout-content>
      </a-layout>
    </a-layout>
  </a-layout>
</template>

<script setup lang="ts">
import translate from 'i18n-jsautotranslate'
import { ref, computed, onMounted, watch, provide } from 'vue'
import { Modal } from '@arco-design/web-vue/es/modal'

const currentLanguage = ref(localStorage.getItem('language') || 'chinese_simplified');

const handleLanguageChange = (language: string) => {
  translate.changeLanguage(language);
  localStorage.setItem('language', language);
  currentLanguage.value = language;
};

const sponsorVisible = ref(false)
const showSponsorModal = (e: Event) => {
  e.preventDefault()
  sponsorVisible.value = true
  console.log('Sponsor modal triggered') // 添加调试日志
}
import { useRouter, useRoute } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { getCurrentUser } from '@/api/auth'
import { logout } from '@/api/auth'
import WechatAuthQrcode from '@/components/WechatAuthQrcode.vue'

const qrcodeRef = ref()
const showAuthQrcode = () => {
  qrcodeRef.value?.startAuth()
}
provide('showAuthQrcode', showAuthQrcode)
const appTitle = computed(() => import.meta.env.VITE_APP_TITLE || '微信公众号订阅助手')
const logo=ref("/static/logo.svg")
const router = useRouter()
const route = useRoute()
const collapsed = ref(false)
const userInfo = ref({
  username: '',
  avatar: ''
})
const hasLogined=ref(false)
const isAuthenticated = computed(() => {
    hasLogined.value = !!localStorage.getItem('token')
  return hasLogined.value
})

const fetchUserInfo = async () => {
  try {
    const res = await getCurrentUser()
    userInfo.value = res
  } catch (error) {
    console.error('获取用户信息失败', error)
  }
}

const handleCollapse = (val: boolean) => {
  collapsed.value = val
}

const handleMenuClick = (key: string) => {
  router.push({ name: key })
}

const goToEditUser = () => {
  router.push({ name: 'EditUser' })
}

const goToChangePassword = () => {
  router.push({ name: 'ChangePassword' })
}

const handleLogout = async () => {
  try {
    await logout()
    localStorage.removeItem('token')
    router.push('/login')
  } catch (error) {
    Message.error('退出登录失败')
  }
}

onMounted(() => {
  if (isAuthenticated.value) {
    fetchUserInfo()
  }
})
  // 根据本地存储的语言设置自动切换语言
onMounted(() => {
    const savedLanguage = localStorage.getItem('language')||"english";
    if (savedLanguage) {
      setTimeout(() => {
        translate.changeLanguage(savedLanguage);
      }, 1000); // 延时1000毫秒后执行语言切换
      currentLanguage.value = savedLanguage;
    }
});
watch(
  () => route.path,
  () => {
    hasLogined.value = !!localStorage.getItem('token')
    if (hasLogined.value) {
      fetchUserInfo()
    }
  }
)

</script>

<style scoped>
.app-container {
  min-height: 100vh;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  height: 64px;
  background: var(--color-bg-2);
  border-bottom: 1px solid var(--color-border);
}

.header-left {
  display: flex;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 500;
}

.logo svg {
  margin-right: 10px;
  font-size: 24px;
  color: var(--primary-color);
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.username {
  margin-left: 10px;
}

.app-content {
  /* padding: 20px; */
  background: var(--color-bg-1);
  min-height: calc(100vh - 64px);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
@media (max-width: 720px) {
  .app-header .header-right {
    display:none !important;
  }
}
</style>