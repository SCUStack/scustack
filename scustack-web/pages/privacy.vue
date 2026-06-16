<template>
  <div class="max-w-3xl mx-auto px-4 sm:px-6 py-8">
    <h1 class="text-xl font-semibold text-slate-900 mb-2">隐私政策</h1>
    <p class="text-sm text-slate-400 mb-8">生效日期：2026年6月16日 · 川大课栈</p>

    <div class="text-sm text-slate-700 leading-relaxed space-y-4">
      <p>川大课栈（以下简称"本平台"或"我们"）深知个人信息对您的重要性。我们依据《中华人民共和国个人信息保护法》（PIPL）及相关法律法规，制定本隐私政策，以帮助您了解我们如何收集、使用和保护您的个人信息。</p>

      <h2 class="text-base font-semibold text-slate-800 mt-8 mb-3">一、我们收集的信息</h2>
      <p>本平台为公益性质，仅收集服务所必需的最少信息：</p>
      <ul class="list-decimal pl-5 space-y-2">
        <li>
          <strong>账户信息</strong>：手机号（用于注册、登录验证及安全通知）。手机号采用 AES-256-GCM 加密存储，不以明文形式保存。
        </li>
        <li>
          <strong>身份信息（选填）</strong>：学号，仅用于验证四川大学在校生身份。学号同样采用加密存储。
        </li>
        <li>
          <strong>联系信息（选填）</strong>：电子邮箱，用于账户恢复及重要通知。
        </li>
        <li>
          <strong>设备与日志信息</strong>：IP 地址、浏览器类型、操作系统版本、访问时间及操作记录。此类信息用于安全防护、滥用检测及平台运营分析。IP 地址在审计日志中以哈希形式存储。
        </li>
        <li>
          <strong>用户生成内容</strong>：您上传的资料标题、描述、分类等信息。这些信息由您主动提供，用于平台展示和检索。
        </li>
      </ul>

      <h2 class="text-base font-semibold text-slate-800 mt-8 mb-3">二、我们如何使用信息</h2>
      <ul class="list-decimal pl-5 space-y-2">
        <li>提供、维护和改进资料共享服务</li>
        <li>验证用户身份，防止虚假注册</li>
        <li>检测和防御安全威胁（爬虫、DDoS、恶意上传等）</li>
        <li>发送服务相关通知（账户安全提醒、版权投诉处理结果等）</li>
        <li>生成匿名统计数据以优化平台运营</li>
        <li>遵守法律法规要求，响应政府部门合法请求</li>
      </ul>
      <p class="text-slate-500 italic mt-2">我们不会将您的个人信息用于商业营销目的，不会基于个人信息进行自动化决策分析，不会向任何第三方出售或共享您的个人信息。</p>

      <h2 class="text-base font-semibold text-slate-800 mt-8 mb-3">三、信息的存储与保护</h2>
      <ul class="list-disc pl-5 space-y-2">
        <li><strong>存储位置</strong>：所有数据存储于中华人民共和国境内（阿里云）。</li>
        <li><strong>加密措施</strong>：手机号、学号等敏感个人信息使用 AES-256-GCM 算法加密存储；数据传输全程使用 HTTPS/TLS 加密。</li>
        <li><strong>访问控制</strong>：敏感数据仅限授权维护人员访问，所有访问操作记录审计日志。</li>
        <li><strong>备份策略</strong>：数据库每日加密备份，备份文件存储于独立的云存储空间。</li>
        <li><strong>保留期限</strong>：个人信息保留至账户注销后 30 天，期满后永久删除。审计日志保留 90 天。</li>
      </ul>

      <h2 class="text-base font-semibold text-slate-800 mt-8 mb-3">四、Cookie 与同类技术</h2>
      <p>我们使用以下必要的 Cookie：</p>
      <ul class="list-disc pl-5 space-y-2">
        <li><strong>access_token / refresh_token</strong>（HttpOnly）：用于维持您的登录状态，关闭浏览器后失效或按设定时间过期。</li>
      </ul>
      <p>我们不使用追踪类 Cookie 或第三方分析工具。</p>

      <h2 class="text-base font-semibold text-slate-800 mt-8 mb-3">五、您的权利</h2>
      <p>根据 PIPL，您享有以下权利：</p>
      <ul class="list-disc pl-5 space-y-2">
        <li><strong>查阅权</strong>：您可以在「账户设置」中查看您的个人信息。</li>
        <li><strong>更正权</strong>：您可以随时修改昵称、邮箱等个人信息。</li>
        <li><strong>删除权</strong>：您可以申请注销账户（30 天冷静期后可撤销），届时您的手机号、学号、邮箱等个人信息将被永久删除。您上传的资料可选择匿名化保留或一并删除。</li>
        <li><strong>撤回同意权</strong>：您可以通过注销账户撤回对个人信息处理的同意。</li>
        <li><strong>投诉权</strong>：如您认为我们的处理违反法律法规，可向监管部门投诉。</li>
      </ul>

      <h2 class="text-base font-semibold text-slate-800 mt-8 mb-3">六、未成年人保护</h2>
      <p>本平台主要面向四川大学在校学生（年满 18 周岁）。不满 14 周岁的未成年人使用本平台须由其监护人阅读并同意本隐私政策，并在监护人指导下使用。</p>
      <p>我们不会主动收集未成年人的个人信息。如发现误收集，我们将立即删除。</p>

      <h2 class="text-base font-semibold text-slate-800 mt-8 mb-3">七、免责声明</h2>
      <p>本平台是学生社区维护的公益项目。尽管我们采取合理措施保护您的信息，但无法保证互联网传输的绝对安全。在不可抗力、黑客攻击、系统故障等极端情况下发生的信息泄露，我们将在法律允许的范围内承担相应责任，并及时通知您。</p>

      <h2 class="text-base font-semibold text-slate-800 mt-8 mb-3">八、政策更新</h2>
      <p>我们可能不时更新本隐私政策。重大变更将通过站内通知或邮件告知。继续使用本平台即表示您同意更新后的条款。</p>

      <h2 class="text-base font-semibold text-slate-800 mt-8 mb-3">九、联系我们</h2>
      <p>如对本隐私政策有任何疑问、意见或投诉，请通过以下方式联系我们：</p>
      <ul class="list-disc pl-5 space-y-1">
        <li>电子邮箱：<a href="mailto:admin@scustack.com" class="text-primary-600 hover:text-primary-700">admin@scustack.com</a></li>
        <li>GitHub：<a href="https://github.com/yeyixiang2007/scustack" target="_blank" rel="noopener" class="text-primary-600 hover:text-primary-700">yeyixiang2007/scustack</a></li>
        <li>通信地址：四川省成都市一环路南一段 24 号四川大学</li>
      </ul>
      <p class="text-slate-400 mt-2">我们将在收到您的请求后 15 个工作日内予以回复。</p>
    </div>
  </div>
</template>
