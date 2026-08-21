<template>
  <main class="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8 lg:py-12">
    <div class="lg:grid lg:grid-cols-[220px_minmax(0,1fr)] lg:gap-12">
      <aside class="hidden lg:block">
        <nav aria-label="隐私政策目录" class="sticky top-24 border-l border-slate-200 pl-4">
          <p class="mb-3 text-xs font-semibold text-slate-900">本页目录</p>
          <a v-for="item in sections" :key="item.id" :href="`#${item.id}`" class="block py-1.5 text-xs text-slate-500 no-underline transition-colors hover:text-primary-700">
            {{ item.label }}
          </a>
        </nav>
      </aside>

      <article class="min-w-0 max-w-3xl">
        <header class="border-b border-slate-200 pb-6">
          <p class="mb-2 text-xs font-medium text-primary-700">川流课栈规则中心</p>
          <h1 class="text-2xl font-semibold text-slate-950 sm:text-3xl">隐私政策</h1>
          <div class="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-xs text-slate-500">
            <span>版本：v2.0</span>
            <span>生效日期：2026 年 8 月 22 日</span>
          </div>
        </header>

        <section class="my-6 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950">
          <div class="flex gap-3">
            <AppIcon name="ShieldCheck" :size="20" class="mt-0.5 shrink-0 text-amber-600" />
            <div>
              <h2 class="font-semibold">先看这几件事</h2>
              <ul class="mt-2 list-disc space-y-1 pl-5 text-xs leading-5 text-amber-900">
                <li>川流课栈是学生自发维护的公益平台，不是四川大学官方网站或下属机构。</li>
                <li>注册时会一次性使用川大账号和学校密码核验身份；学校密码不保存。</li>
                <li>学号和绑定邮箱加密保存，课栈密码仅保存加盐哈希。</li>
                <li>上传内容、评论、心愿和部分贡献者信息会向其他用户公开。</li>
                <li>我们不出售个人信息，也不用于商业广告或跨站画像。</li>
              </ul>
            </div>
          </div>
        </section>

        <div class="space-y-8 text-sm leading-7 text-slate-700">
          <section id="scope" class="scroll-mt-24">
            <h2 class="text-lg font-semibold text-slate-900">一、适用范围与平台身份</h2>
            <p class="mt-3">本政策适用于川流课栈网站（scustack.com）提供的课程浏览、资料搜索与预览、账号、上传、互动、反馈和版权投诉等服务。川流课栈由四川大学学生社区志愿者维护，以下简称“平台”或“我们”。</p>
            <p class="mt-3">第三方网站或外部资料链接由相应服务方独立运营，其信息处理规则不适用本政策。离开本站前，请查看对应服务的隐私说明。</p>
          </section>

          <section id="collection" class="scroll-mt-24">
            <h2 class="text-lg font-semibold text-slate-900">二、我们处理的信息</h2>
            <h3 class="mt-4 font-semibold text-slate-800">2.1 浏览、搜索与安全日志</h3>
            <p class="mt-2">您访问平台时，服务器可能接收 IP 地址、请求时间、访问路径、浏览器与操作系统信息、User-Agent、请求结果及安全事件信息，用于提供页面、限制异常请求、排查故障和保障系统安全。审计日志中的 IP 会进行哈希处理；部分限流或安全组件会在处理期间使用原始 IP。</p>
            <p class="mt-2">您主动提交的搜索词会用于返回搜索结果。热门搜索在缓存中按词汇聚合，通常保留 7 天；无结果搜索可能写入运营日志，帮助补齐课程和资料。请勿在搜索框输入姓名、学号、联系方式等个人信息。</p>

            <h3 class="mt-4 font-semibold text-slate-800">2.2 注册、登录与账户</h3>
            <ul class="mt-2 list-disc space-y-1 pl-5">
              <li><strong>学号：</strong>用于确认四川大学学生身份和登录。数据库保存 AES-256-GCM 加密值及用于唯一性校验的不可逆盲索引。</li>
              <li><strong>川大统一认证密码：</strong>仅在注册核验时传递给身份校验程序，完成后即丢弃，不写入数据库、缓存或业务日志。</li>
              <li><strong>课栈密码：</strong>用于后续登录，仅保存 bcrypt 加盐哈希，不保存明文。</li>
              <li><strong>账户资料：</strong>包括昵称、头像、角色、账户状态、信任分、认证时间，以及您可选绑定的邮箱。邮箱加密保存并建立不可逆盲索引。</li>
              <li><strong>会话信息：</strong>包括登录时间、最近使用时间、IP、浏览器信息及刷新令牌哈希，用于保持登录、展示和撤销登录设备。</li>
            </ul>

            <h3 class="mt-4 font-semibold text-slate-800">2.3 您提交的内容与操作</h3>
            <p class="mt-2">当您使用相应功能时，我们处理您上传的文件或外部链接、标题、简介、课程、学期、教师、分类与标签，以及评论、评分、心愿、举报、收藏、关注、下载和审核记录。文件可能被病毒扫描、提取文本、生成缩略图或转换为在线预览格式。</p>
            <p class="mt-2">资料、评论、心愿、昵称、头像、徽章和信任标识可能在公开页面展示。请勿上传身份证件、成绩单原件、未脱敏名单，或含有他人姓名、学号、联系方式的内容；确有必要时，应先取得合法授权并完成脱敏。</p>

            <h3 class="mt-4 font-semibold text-slate-800">2.4 反馈、举报与版权投诉</h3>
            <p class="mt-2">反馈功能可能收集您填写的邮箱、反馈内容、IP 和浏览器信息。版权投诉会收集投诉人或机构名称、联系邮箱、可选电话、被投诉链接、事实说明、声明、IP 及处理结果。这些信息仅用于核实、沟通、处理争议和留存必要证据。</p>

            <h3 class="mt-4 font-semibold text-slate-800">2.5 浏览器本地信息</h3>
            <p class="mt-2">为方便继续浏览和填写，本站使用浏览器 localStorage 保存最近浏览（最多 20 条）、搜索历史、未提交的上传草稿和公告关闭状态。这些数据默认仅保存在当前浏览器，不随账户同步；您可通过清空搜索历史、提交或清除草稿、清理站点数据将其删除。</p>
          </section>

          <section id="purpose" class="scroll-mt-24">
            <h2 class="text-lg font-semibold text-slate-900">三、处理目的</h2>
            <ul class="mt-3 list-disc space-y-1 pl-5">
              <li>核验学生身份，创建和维护账户及登录会话；</li>
              <li>提供课程检索、资料上传、审核、预览、下载和互动功能；</li>
              <li>进行内容治理、版权处理、反滥用、限流、安全审计和故障排查；</li>
              <li>基于下载量、评分、更新时间、维护者标记等非画像因素生成公开排序和推荐；</li>
              <li>汇总匿名或聚合统计，了解课程与资料需求并改进服务；</li>
              <li>履行法律法规要求，响应有权机关依法提出的请求。</li>
            </ul>
            <p class="mt-3">我们不会出售个人信息，不使用广告 Cookie，不基于个人敏感信息进行商业营销、跨站追踪或差别定价。</p>
          </section>

          <section id="cookies" class="scroll-mt-24">
            <h2 class="text-lg font-semibold text-slate-900">四、Cookie 与同类技术</h2>
            <div class="mt-3 overflow-x-auto rounded-lg border border-slate-200">
              <table class="w-full min-w-[560px] text-left text-xs">
                <thead class="bg-slate-50 text-slate-600"><tr><th class="px-3 py-2 font-semibold">名称</th><th class="px-3 py-2 font-semibold">用途</th><th class="px-3 py-2 font-semibold">通常期限</th></tr></thead>
                <tbody class="divide-y divide-slate-200">
                  <tr><td class="px-3 py-2 font-mono">access_token</td><td class="px-3 py-2">验证登录身份，HttpOnly</td><td class="px-3 py-2">15 分钟</td></tr>
                  <tr><td class="px-3 py-2 font-mono">refresh_token</td><td class="px-3 py-2">续期与管理登录会话，HttpOnly</td><td class="px-3 py-2">7 天</td></tr>
                  <tr><td class="px-3 py-2 font-mono">csrf_token</td><td class="px-3 py-2">防止跨站请求伪造</td><td class="px-3 py-2">当前站点会话</td></tr>
                </tbody>
              </table>
            </div>
            <p class="mt-3">禁用必要 Cookie 后，登录、上传和账户设置等功能可能无法使用。</p>
          </section>

          <section id="sharing" class="scroll-mt-24">
            <h2 class="text-lg font-semibold text-slate-900">五、服务提供方、共享与跨境</h2>
            <p class="mt-3">平台会根据实际部署配置使用以下服务。我们仅传递完成相应功能所必需的信息：</p>
            <ul class="mt-2 list-disc space-y-1 pl-5">
              <li><strong>四川大学统一身份认证：</strong>一次性核验您主动提交的学校账号凭据；川流课栈不保存学校密码或学校会话。</li>
              <li><strong>文件存储服务：</strong>当前默认使用平台配置的 LFS 文件服务，也可按部署配置使用阿里云 OSS，用于保存和分发上传文件、缩略图及预览文件。</li>
              <li><strong>Sentry（配置启用时）：</strong>接收前端或后端错误、页面与设备环境、性能追踪及抽样会话回放信息，用于定位故障。此服务可能由境外主体提供。</li>
              <li><strong>GitHub：</strong>仅在您主动跳转并提交 Issue 时处理您提供的 GitHub 账户和 Issue 内容，适用 GitHub 自身规则。</li>
            </ul>
            <p class="mt-3">除获得您的单独同意、完成受托处理、保护重大合法权益或法律法规另有规定外，我们不会向其他主体提供个人信息。如服务商或存储地点变化涉及个人信息跨境，我们将依法告知并履行必要程序。</p>
          </section>

          <section id="retention" class="scroll-mt-24">
            <h2 class="text-lg font-semibold text-slate-900">六、保存、删除与账户注销</h2>
            <ul class="mt-3 list-disc space-y-1 pl-5">
              <li>账户信息在账户存续期间保存；登录刷新令牌通常不超过 7 天，撤销或轮换后失效。</li>
              <li>公开内容和源文件在内容存续期间保存；下架、删除或版权处理后，缓存、备份和冗余副本会按存储系统周期清理。</li>
              <li>浏览器本地信息保存至您清理站点数据，或由对应功能主动清除。</li>
              <li>反馈、投诉、审核和安全日志按处理争议、保障安全及法定义务所需的最短期限保存。</li>
            </ul>
            <div class="mt-4 border-l-4 border-primary-500 bg-primary-50 px-4 py-3 text-xs text-primary-950">
              当前“隐私设置”中的注销功能会立即停用账户、撤销有效会话，并清除学号、邮箱、学校认证状态和第三方账号标识。为保持资料版本、评论上下文和安全审计的完整性，内部账户编号、已发布内容及必要日志可能继续保留；公开贡献会与已停用账户关联或以匿名方式呈现。注销前请先删除您不希望继续公开的内容，或联系我们协助处理。
            </div>
          </section>

          <section id="security" class="scroll-mt-24">
            <h2 class="text-lg font-semibold text-slate-900">七、安全保护</h2>
            <p class="mt-3">我们采取 HTTPS 传输、敏感字段加密、密码哈希、最小权限、会话撤销、CSRF 防护、安全响应头、速率限制、恶意文件检测和操作审计等措施。互联网服务无法保证绝对安全；请为课栈设置独立密码，不要在资料、评论、反馈或 Issue 中公开个人敏感信息。</p>
            <p class="mt-3">发生或可能发生个人信息泄露、篡改或丢失时，我们将依法采取补救措施，并在法律要求的范围内向有关部门和受影响用户告知。</p>
          </section>

          <section id="rights" class="scroll-mt-24">
            <h2 class="text-lg font-semibold text-slate-900">八、您的权利</h2>
            <p class="mt-3">您可以在个人中心查看和修改昵称、头像、邮箱及公开贡献显示设置，管理收藏、关注、评论和上传内容，并在隐私设置中注销账户。您也可以联系我们，请求查阅、复制、更正、补充或删除个人信息，解释处理规则，或撤回基于同意开展的处理。</p>
            <p class="mt-3">为防止冒用，我们可能先核验您的账户身份。我们通常在 15 个工作日内答复；法律规定不允许删除、请求会损害他人合法权益或无法核实身份时，我们会说明原因。</p>
          </section>

          <section id="minors" class="scroll-mt-24">
            <h2 class="text-lg font-semibold text-slate-900">九、未成年人保护</h2>
            <p class="mt-3">平台主要面向四川大学学生。未满十八周岁的用户应在监护人指导下阅读本政策和用户协议；不满十四周岁的儿童不应注册或提交个人信息。如监护人发现儿童未经同意向平台提供了信息，请立即联系我们，我们核实后将依法处理。</p>
          </section>

          <section id="updates" class="scroll-mt-24">
            <h2 class="text-lg font-semibold text-slate-900">十、政策更新</h2>
            <p class="mt-3">服务功能、信息类型、处理目的或服务提供方发生变化时，我们会更新本页。重大变化会通过站内公告、登录提示或其他合理方式通知；依法需要重新取得同意的，我们会在相关处理前征得同意。</p>
          </section>

          <section id="contact" class="scroll-mt-24 border-t border-slate-200 pt-8">
            <h2 class="text-lg font-semibold text-slate-900">十一、联系我们</h2>
            <p class="mt-3">隐私咨询、权利请求、投诉或安全问题可通过以下渠道提交：</p>
            <ul class="mt-2 list-disc space-y-1 pl-5">
              <li>邮箱：<a href="mailto:admin@scustack.com" class="text-primary-700 hover:text-primary-800">admin@scustack.com</a></li>
              <li>GitHub：<a href="https://github.com/yeyixiang2007/scustack/issues" target="_blank" rel="noopener noreferrer" class="text-primary-700 hover:text-primary-800">yeyixiang2007/scustack/issues</a>（请勿公开提交个人敏感信息）</li>
            </ul>
            <p class="mt-3">如您认为我们的处理损害了您的合法权益，也可以向履行个人信息保护职责的部门投诉或依法向有管辖权的人民法院提起诉讼。</p>
          </section>
        </div>
      </article>
    </div>
  </main>
</template>

<script setup lang="ts">
const sections = [
  { id: 'scope', label: '适用范围' },
  { id: 'collection', label: '处理的信息' },
  { id: 'purpose', label: '处理目的' },
  { id: 'cookies', label: 'Cookie' },
  { id: 'sharing', label: '服务提供方' },
  { id: 'retention', label: '保存与注销' },
  { id: 'security', label: '安全保护' },
  { id: 'rights', label: '您的权利' },
  { id: 'minors', label: '未成年人' },
  { id: 'updates', label: '政策更新' },
  { id: 'contact', label: '联系我们' },
]

useSeoMeta({
  title: '隐私政策 - 川流课栈',
  description: '了解川流课栈如何处理和保护账号、上传内容、日志及浏览器本地信息。',
})
</script>
