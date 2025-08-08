// 处理弹出框确认事件的函数
function handleConfirmation() {
  // 调用 getSubscriptionInfo 获取订阅信息
  const subscriptionInfo = getSubscriptionInfo();

  // 将获取的信息回填到表单中
  if (subscriptionInfo) {
    Object.keys(subscriptionInfo).forEach(key => {
      const inputElement = document.querySelector(`[name="${key}"]`);
      if (inputElement) {
        inputElement.value = subscriptionInfo[key];
      }
    });
  }

  // 可以添加其他逻辑，例如表单验证或提交
  console.log('表单已回填:', subscriptionInfo);
}

// 示例：绑定弹出框确认按钮的点击事件
// document.getElementById('confirmButton').addEventListener('click', handleConfirmation);