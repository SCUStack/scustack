<template>
  <main class="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8 lg:py-12">
    <div class="lg:grid lg:grid-cols-[220px_minmax(0,1fr)] lg:gap-12">
      <aside class="hidden lg:block">
        <nav aria-label="用户协议目录" class="sticky top-24 border-l border-slate-200 pl-4">
          <p class="mb-3 text-xs font-semibold text-slate-900">本页目录</p>
          <a v-for="item in sections" :key="item.id" :href="`#${item.id}`" class="block py-1.5 text-xs text-slate-500 no-underline transition-colors hover:text-primary-700">
            {{ item.label }}
          </a>
        </nav>
      </aside>

      <article class="min-w-0 max-w-3xl">
        <header class="border-b border-slate-200 pb-6">
          <p class="mb-2 text-xs font-medium text-primary-700">川流课栈规则中心</p>
          <h1 class="text-2xl font-semibold text-slate-950 sm:text-3xl">用户协议</h1>
          <div class="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-xs text-slate-500">
            <span>版本：v2.0</span>
            <span>生效日期：2026 年 8 月 22 日</span>
          </div>
        </header>

        <section class="my-6 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950">
          <div class="flex gap-3">
            <AppIcon name="Info" :size="20" class="mt-0.5 shrink-0 text-amber-600" />
            <div>
              <h2 class="font-semibold">使用前请确认</h2>
              <ul class="mt-2 list-disc space-y-1 pl-5 text-xs leading-5 text-amber-900">
                <li>川流课栈是学生志愿者维护的公益资料共享平台，不代表四川大学。</li>
                <li>注册需要通过四川大学统一身份认证核验在校身份。</li>
                <li>您只能上传有权分享、已完成必要脱敏且符合法律规定的内容。</li>
                <li>资料来自用户贡献，请在用于学习、考试或其他决定前自行核对。</li>
                <li>浏览和下载不等于取得资料的著作权或商业使用许可。</li>
              </ul>
            </div>
          </div>
        </section>

        <div class="space-y-8 text-sm leading-7 text-slate-700">
          <section id="acceptance" class="scroll-mt-24">
            <h2 class="text-lg font-semibold text-slate-900">一、协议成立与适用范围</h2>
            <p class="mt-3">本协议是您与川流课栈运营团队之间关于使用 scustack.com 及相关服务的约定。点击同意、完成注册或继续使用平台，表示您已阅读并同意本协议及<a href="/privacy" class="text-primary-700 hover:text-primary-800">《隐私政策》</a>。如不同意，请不要注册或使用需要同意本协议的功能。</p>
            <p class="mt-3">平台包括课程和学院浏览、资料搜索、预览与下载、资料上传、评论与评分、心愿、收藏与关注、反馈、举报和版权投诉等当前实际提供的功能。具体功能以页面和接口当时可用状态为准。</p>
          </section>

          <section id="nature" class="scroll-mt-24">
            <h2 class="text-lg font-semibold text-slate-900">二、平台性质</h2>
            <ul class="mt-3 list-disc space-y-1 pl-5">
              <li>川流课栈由四川大学学生社区志愿者独立维护，当前以公益、非商业方式向用户提供服务。</li>
              <li>平台不是四川大学官方网站、下属机构或附属组织，未获得学校的官方授权、认可或赞助，不代表学校立场。</li>
              <li>课程、教师、校历和资料信息仅供参考；教务安排、考试要求和校方通知应以四川大学官方渠道为准。</li>
              <li>项目源代码依仓库中的 MIT License 开源；开源许可不涵盖生产数据、用户账户、用户上传资料、商标或运营数据。</li>
            </ul>
          </section>

          <section id="account" class="scroll-mt-24">
            <h2 class="text-lg font-semibold text-slate-900">三、注册与账户</h2>
            <h3 class="mt-4 font-semibold text-slate-800">3.1 注册资格</h3>
            <p class="mt-2">当前注册流程要求使用有效的四川大学学号和统一认证凭据完成一次身份核验，同一学号只能对应一个课栈账户。您应具有与使用行为相适应的民事行为能力；未满十八周岁的用户应在监护人指导下使用，不满十四周岁的儿童不应注册。</p>
            <h3 class="mt-4 font-semibold text-slate-800">3.2 账户安全</h3>
            <ul class="mt-2 list-disc space-y-1 pl-5">
              <li>请为课栈设置独立密码，不要复用川大统一认证密码，也不要出租、出借、出售或转让账户。</li>
              <li>通过您账户进行的上传、评论、评分、举报等操作视为您的操作，除非您能证明账户被未经授权使用。</li>
              <li>发现异常登录或凭据泄露时，请及时修改密码、撤销其他会话并联系我们。</li>
              <li>平台可对异常注册、自动化访问、共享账户或危及系统安全的账户采取验证、限流、暂停或停用措施。</li>
            </ul>
            <h3 class="mt-4 font-semibold text-slate-800">3.3 注销</h3>
            <p class="mt-2">您可在“个人中心 → 隐私设置”注销账户。当前注销会立即停用账户、撤销会话并清除学号、邮箱和第三方账号标识；已发布资料、评论以及必要的审核和安全记录可能为保持内容上下文、处理争议或履行法定义务而保留。具体处理见《隐私政策》“保存、删除与账户注销”。</p>
          </section>

          <section id="content" class="scroll-mt-24">
            <h2 class="text-lg font-semibold text-slate-900">四、上传与公开内容</h2>
            <h3 class="mt-4 font-semibold text-slate-800">4.1 您的保证</h3>
            <p class="mt-2">上传文件、外部链接、评论或其他内容前，您应确认：</p>
            <ul class="mt-2 list-disc space-y-1 pl-5">
              <li>您是内容权利人，或已取得足以在本平台分享、展示、预览和下载的授权；</li>
              <li>内容不侵犯著作权、商标权、名誉权、隐私权、个人信息权益或其他合法权益；</li>
              <li>已删除或遮盖无必要公开的姓名、学号、成绩、联系方式、签名及其他个人信息；</li>
              <li>内容真实对应所选课程、分类、学期和描述，不以误导标题、重复文件或无效链接干扰检索；</li>
              <li>内容不含违法信息、恶意代码、病毒、破解工具、账号凭据、考试作弊材料或其他危害网络和校园秩序的内容。</li>
            </ul>
            <h3 class="mt-4 font-semibold text-slate-800">4.2 内容许可</h3>
            <p class="mt-2">您保留依法享有的内容权利。为运行平台，您在内容存续期间授予平台一项免费的、非独占的许可，允许平台存储、复制、扫描、提取文本、生成缩略图或预览版本、展示、通过网络传播，并向用户提供浏览和下载。该许可仅用于提供、维护和保护川流课栈服务，不授权平台将资料对外出售。</p>
            <p class="mt-2">删除或下架后，许可对面向普通用户的继续提供终止；为备份、安全审计、争议处理或履行法定义务保留的副本，可在必要范围和期限内继续保存。</p>
            <h3 class="mt-4 font-semibold text-slate-800">4.3 公开展示</h3>
            <p class="mt-2">审核通过的资料、评论和心愿可被互联网用户访问，搜索引擎也可能建立索引。昵称、头像、徽章和信任标识可能随贡献展示。请将公开区域视为公开场合，不要提交不希望公开的信息。</p>
          </section>

          <section id="conduct" class="scroll-mt-24">
            <h2 class="text-lg font-semibold text-slate-900">五、使用规范</h2>
            <p class="mt-3">使用平台时，您不得：</p>
            <ul class="mt-2 list-disc space-y-1 pl-5">
              <li>批量注册、冒用他人身份、操纵下载量或评分、刷评论、恶意举报；</li>
              <li>绕过访问控制、速率限制、下载网关、反爬机制或其他安全措施；</li>
              <li>未经书面授权使用爬虫、脚本或自动化工具批量抓取、下载、镜像或建立数据集；</li>
              <li>攻击、探测或干扰平台、存储服务、账户或其他用户设备；</li>
              <li>将平台资料批量转售、用于商业培训引流，或在评论和资料描述中发布商业广告；</li>
              <li>利用平台实施作弊、诈骗、骚扰、侵权或其他违反法律法规和公序良俗的行为。</li>
            </ul>
            <p class="mt-3">正常浏览、为个人学习下载合理数量的资料，以及依 MIT License 使用开源代码，不受上述自动化抓取和商业利用限制条款的不当扩大解释。</p>
          </section>

          <section id="moderation" class="scroll-mt-24">
            <h2 class="text-lg font-semibold text-slate-900">六、审核与违规处理</h2>
            <p class="mt-3">上传资料通常进入审核队列，审核可能结合自动检测和维护者判断。平台可以更正分类、标记重复或可疑内容，并对违法、侵权、不安全、不相关或违反本协议的内容拒绝发布、下架、断开链接或删除。</p>
            <p class="mt-3">根据违规性质和影响，平台可采取警告、限制上传或互动、撤销信任标识、暂停账户、永久停用账户、保全证据或依法报告等措施。紧急安全或法律风险下可以先处置后通知；其他情形会尽量说明理由。您可通过本协议末尾渠道申诉。</p>
          </section>

          <section id="copyright" class="scroll-mt-24">
            <h2 class="text-lg font-semibold text-slate-900">七、知识产权与投诉</h2>
            <p class="mt-3">下载、预览或分享链接不代表平台或上传者向您转让著作权。您应遵守原作者、权利人标注的许可及法律规定，仅在被授权或合理使用范围内使用资料。</p>
            <p class="mt-3">权利人认为内容侵权时，可通过<a href="/copyright" class="text-primary-700 hover:text-primary-800">版权投诉页面</a>提交姓名或机构名称、联系方式、内容链接、权属和侵权说明及真实性声明。我们会核验通知，并在合理时间内采取限制访问、下架或删除等措施；必要时会联系上传者核实或接受反通知。</p>
          </section>

          <section id="third-party" class="scroll-mt-24">
            <h2 class="text-lg font-semibold text-slate-900">八、外部链接与第三方服务</h2>
            <p class="mt-3">用户可能提交由第三方托管的外部资料链接。第三方服务的可用性、内容、安全性、收费和信息处理由相应运营者负责。访问前请核实域名和规则，不要在来源不明的页面输入川大账号或课栈密码。发现失效、跳转异常或恶意链接时，请使用举报或反馈功能。</p>
          </section>

          <section id="availability" class="scroll-mt-24">
            <h2 class="text-lg font-semibold text-slate-900">九、服务可用性与责任边界</h2>
            <ul class="mt-3 list-disc space-y-1 pl-5">
              <li>平台资料主要由用户提供，我们不保证其准确、完整、及时、适用于特定课程或没有权利瑕疵。</li>
              <li>“维护者精选”“社区验证”等标识仅表示有限审核或社区反馈，不是对内容正确性、合法性或考试结果的保证。</li>
              <li>学生志愿者维护的服务可能因维护、故障、网络、存储服务、学校认证系统或不可抗力中断、延迟或丢失部分功能。</li>
              <li>在法律允许的范围内，用户应自行备份重要内容并承担基于资料作出学习、考试或其他决定的风险。</li>
            </ul>
            <p class="mt-3 font-medium text-slate-800">本条不排除因平台故意或重大过失造成损害的责任，也不排除法律明确不得限制或免除的责任。</p>
          </section>

          <section id="changes" class="scroll-mt-24">
            <h2 class="text-lg font-semibold text-slate-900">十、服务与协议变更</h2>
            <p class="mt-3">我们可以基于安全、合规、运营能力或社区需求调整功能。协议发生重大变化时，会通过本页、站内公告或登录提示通知；依法需要重新同意的，我们会在继续提供相关功能前取得您的同意。停止运营时，我们会在合理可行范围内提前公告，并说明账户和内容处理安排。</p>
          </section>

          <section id="law" class="scroll-mt-24">
            <h2 class="text-lg font-semibold text-slate-900">十一、法律适用与争议解决</h2>
            <p class="mt-3">本协议的订立、履行和解释适用中华人民共和国大陆地区法律。发生争议时，请先通过联系渠道与我们协商；协商不成的，任何一方可依法向有管辖权的人民法院提起诉讼。法律另有强制性规定的，从其规定。</p>
          </section>

          <section id="contact" class="scroll-mt-24 border-t border-slate-200 pt-8">
            <h2 class="text-lg font-semibold text-slate-900">十二、联系我们</h2>
            <ul class="mt-3 list-disc space-y-1 pl-5">
              <li>一般咨询、申诉和安全问题：<a href="mailto:admin@scustack.com" class="text-primary-700 hover:text-primary-800">admin@scustack.com</a></li>
              <li>版权问题：使用<a href="/copyright" class="text-primary-700 hover:text-primary-800">版权投诉页面</a></li>
              <li>公开技术问题：<a href="https://github.com/yeyixiang2007/scustack/issues" target="_blank" rel="noopener noreferrer" class="text-primary-700 hover:text-primary-800">GitHub Issues</a>（请勿提交账号、密码、学号等敏感信息）</li>
            </ul>
          </section>
        </div>
      </article>
    </div>
  </main>
</template>

<script setup lang="ts">
const sections = [
  { id: 'acceptance', label: '协议与服务' },
  { id: 'nature', label: '平台性质' },
  { id: 'account', label: '注册与账户' },
  { id: 'content', label: '上传与公开内容' },
  { id: 'conduct', label: '使用规范' },
  { id: 'moderation', label: '审核与违规' },
  { id: 'copyright', label: '知识产权' },
  { id: 'third-party', label: '第三方服务' },
  { id: 'availability', label: '责任边界' },
  { id: 'changes', label: '协议变更' },
  { id: 'law', label: '法律与争议' },
  { id: 'contact', label: '联系我们' },
]

useSeoMeta({
  title: '用户协议 - 川流课栈',
  description: '川流课栈的账户、内容上传、使用规范、知识产权和争议处理规则。',
})
</script>
