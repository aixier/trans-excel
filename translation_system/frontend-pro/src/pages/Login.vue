<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <TranslationOutlined class="login-icon" />
        <h1>Translation System Pro</h1>
        <p>专业的游戏本地化翻译管理平台</p>
      </div>

      <a-form
        :model="formState"
        @finish="onFinish"
        layout="vertical"
        class="login-form"
      >
        <a-form-item
          label="用户名"
          name="username"
          :rules="[{ required: true, message: '请输入用户名' }]"
        >
          <a-input
            v-model:value="formState.username"
            placeholder="请输入用户名"
            size="large"
          >
            <template #prefix>
              <UserOutlined />
            </template>
          </a-input>
        </a-form-item>

        <a-form-item
          label="密码"
          name="password"
          :rules="[{ required: true, message: '请输入密码' }]"
        >
          <a-input-password
            v-model:value="formState.password"
            placeholder="请输入密码"
            size="large"
          >
            <template #prefix>
              <LockOutlined />
            </template>
          </a-input-password>
        </a-form-item>

        <a-form-item>
          <a-checkbox v-model:checked="formState.remember">记住我</a-checkbox>
          <a class="login-form-forgot" href="">忘记密码?</a>
        </a-form-item>

        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            size="large"
            block
            :loading="loading"
          >
            登录
          </a-button>
        </a-form-item>
      </a-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  TranslationOutlined,
  UserOutlined,
  LockOutlined
} from '@ant-design/icons-vue'

const router = useRouter()
const loading = ref(false)

const formState = ref({
  username: 'admin',
  password: '',
  remember: true
})

const onFinish = async () => {
  loading.value = true
  
  // 模拟登录
  setTimeout(() => {
    loading.value = false
    message.success('登录成功')
    router.push('/dashboard')
  }, 1000)
}
</script>

<style scoped lang="scss">
.login-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

  .login-box {
    width: 400px;
    padding: 40px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);

    .login-header {
      text-align: center;
      margin-bottom: 32px;

      .login-icon {
        font-size: 48px;
        color: #667eea;
      }

      h1 {
        margin: 16px 0 8px;
        font-size: 24px;
        color: #333;
      }

      p {
        margin: 0;
        color: #666;
        font-size: 14px;
      }
    }

    .login-form-forgot {
      float: right;
    }
  }
}
</style>