# Abacus Chat Proxy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Ffuwei99%2Fabacus_chat_proxy.git)

## 部署方式

### 本地部署
1. 克隆仓库
2. 运行 `start.bat`（Windows）或 `start.sh`（Linux/Mac）
3. 访问 `http://localhost:9876/v1`

### Vercel 部署
1. 点击上方的 "Deploy with Vercel" 按钮
2. 在 Vercel 的环境变量中设置以下值：
   - `COOKIES`: 你的 Abacus cookies
   - `CONVERSATION_ID`: 你的对话 ID

#### 配置环境变量详细步骤
1. 部署完成后，进入 Vercel 项目控制面板
2. 点击顶部的 "Settings"
3. 在左侧菜单中选择 "Environment Variables"
4. 点击 "Add New" 添加以下环境变量：
   - 名称：`COOKIES`
     值：你的 Abacus cookies（从浏览器开发者工具中获取）
   - 名称：`CONVERSATION_ID`
     值：你的对话 ID
5. 添加完成后点击 "Save"
6. 返回 "Deployments" 页面，点击 "Redeploy" 重新部署项目

注意：cookies 可以从浏览器开发者工具的 Network 标签页中，访问 abacus.ai 时的请求头中获取。
