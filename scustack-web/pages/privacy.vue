<template>
  <div class="max-w-3xl mx-auto px-4 sm:px-6 py-8">
    <h1 class="text-xl font-semibold text-slate-900 mb-2">隐私政策</h1>
    <p class="text-sm text-slate-400 mb-2">生效日期：2026年6月17日</p>
    <p class="text-sm text-slate-400 mb-8">版本：v1.1</p>

    <div class="text-sm text-slate-700 leading-relaxed space-y-4">
      <div class="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
        <p class="text-amber-800 font-medium text-xs mb-1">重要提示</p>
        <p class="text-amber-700 text-xs leading-relaxed">
          川流课栈是由<strong>四川大学在校学生自发组织并维护的公益资料共享平台</strong>，<strong>并非四川大学的官方网站或下属机构</strong>。请您在使用本平台前仔细阅读本隐私政策，特别是以<strong>加粗</strong>或<strong>加粗下划线</strong>标注的条款。如您不同意本政策的任何内容，请立即停止使用本平台。
        </p>
      </div>

      <p>川流课栈（以下简称"本平台"或"我们"）是由四川大学在校学生社区维护的公益资料共享平台。我们深知个人信息对您的重要性，并承诺依据《中华人民共和国个人信息保护法》（以下简称"《个保法》"）、《中华人民共和国网络安全法》、《中华人民共和国数据安全法》、《网络数据安全管理条例》及 GB/T 44588-2024《数据安全技术 互联网平台及产品服务个人信息处理规则》等法律法规和国家标准，采取合理必要的措施保护您的个人信息安全。</p>
      <p>本隐私政策旨在向您说明我们如何收集、使用、存储、委托处理、共享、转移、公开披露和保护您的个人信息，以及您享有的相关权利和行使方式。本政策适用于本平台提供的所有产品和服务。</p>
      <p>请您注意：<strong>本平台为公益性质，不进行商业化运营，不会将您的个人信息用于商业营销、广告推送或用户画像。</strong></p>

      <h2 class="text-base font-semibold text-slate-800 mt-8 mb-3">一、定义</h2>
      <p>在本政策中，下列术语具有以下含义：</p>
      <ul class="list-disc pl-5 space-y-1">
        <li><strong>个人信息</strong>：指以电子或其他方式记录的与已识别或可识别的自然人有关的各种信息，不包括匿名化处理后的信息。本政策中提及的个人信息种类见附录。</li>
        <li><strong>敏感个人信息</strong>：指一旦泄露或者非法使用，容易导致自然人的人格尊严受到侵害或者人身、财产安全受到危害的个人信息，包括手机号码、学号、行踪轨迹、生物识别信息等。</li>
        <li><strong>匿名化</strong>：指个人信息经过处理无法识别特定自然人且不能复原的过程。经匿名化处理的信息不再属于个人信息。</li>
        <li><strong>去标识化</strong>：指个人信息经过处理，使其在不借助额外信息的情况下无法识别特定自然人的过程。</li>
        <li><strong>用户</strong>：指注册、登录或使用本平台的任何自然人。</li>
        <li><strong>儿童</strong>：指不满十四周岁的未成年人。</li>
      </ul>

      <h2 class="text-base font-semibold text-slate-800 mt-8 mb-3">二、我们如何收集您的个人信息</h2>
      <p>本平台遵循<strong>最小必要原则</strong>，仅收集实现服务功能所必需的个人信息，并在收集前告知您收集的目的、方式和范围。如您拒绝提供必要信息，将无法使用对应的服务功能，但不影响您浏览公开内容。</p>
      <p>以下按功能场景分别说明我们收集的个人信息类型：</p>

      <h3 class="text-sm font-semibold text-slate-700 mt-4 mb-2">2.1 账号注册与登录（必要）</h3>
      <ul class="list-disc pl-5 space-y-1">
        <li><strong>手机号码</strong>（敏感个人信息）：用于发送短信验证码以验证您的身份。手机号码是您登录本平台的唯一凭证。我们采用 AES-256-GCM 算法对手机号码进行加密存储，不以明文形式保存在数据库中。手机号码的掩码形式（如 138****1234）可能在您选择非匿名展示时在部分页面公开显示。</li>
        <li><strong>短信验证码</strong>：用于验证手机号码的真实性，使用 HMAC-SHA256 加盐后暂存于 Redis，有效期 3 至 5 分钟。</li>
        <li><strong>登录密码</strong>（如您选择密码登录）：使用 bcrypt 加盐哈希存储，明文密码在任何环节均不落盘。</li>
      </ul>

      <h3 class="text-sm font-semibold text-slate-700 mt-4 mb-2">2.2 身份验证（可选）</h3>
      <ul class="list-disc pl-5 space-y-1">
        <li><strong>学号</strong>（敏感个人信息）：您可以选择提供学号以验证四川大学在校生身份。学号采用 AES-256-GCM 算法加密存储。我们不强制要求提供学号，您可以在不提供学号的情况下正常使用平台的大部分功能。</li>
        <li><strong>电子邮箱</strong>（可选）：您可以选择绑定电子邮箱，用于账户恢复、接收重要安全通知和版权投诉通知。电子邮箱地址采用加密存储。</li>
      </ul>

      <h3 class="text-sm font-semibold text-slate-700 mt-4 mb-2">2.3 用户生成内容（使用平台功能时自动收集）</h3>
      <ul class="list-disc pl-5 space-y-1">
        <li>当您上传资料、发布心愿、提交评论或进行其他互动操作时，您主动提供的内容（包括资料标题、描述、分类、标签、评论内容等）将被收集并在平台上公开展示。</li>
        <li>上传的资料文件本身将存储在阿里云 OSS 上，并在平台上供其他用户浏览和下载。</li>
        <li>您上传的资料中如包含他人的个人信息，您应事先取得该个人的同意或进行脱敏处理。</li>
      </ul>

      <h3 class="text-sm font-semibold text-slate-700 mt-4 mb-2">2.4 联系与投诉（使用投诉功能时收集）</h3>
      <p>当您通过版权投诉页面、举报功能或联系邮箱与我们沟通时，您提供的姓名（或昵称）、联系方式、投诉或举报内容、相关证明材料等信息将被收集，用于处理您的诉求。</p>

      <h3 class="text-sm font-semibold text-slate-700 mt-4 mb-2">2.5 自动收集的技术信息</h3>
      <ul class="list-decimal pl-5 space-y-2">
        <li>
          <strong>设备与网络信息</strong>：包括设备类型、操作系统名称及版本、浏览器类型及版本、IP 地址、网络类型（Wi-Fi / 移动网络）。用于适配页面展示、安全防护和滥用检测。IP 地址在审计日志中以 SHA-256 哈希形式存储，仅保留最近 90 天的记录。
        </li>
        <li>
          <strong>操作日志</strong>：包括访问时间戳、浏览页面路径、点击行为、搜索关键词、上传及下载操作记录等，用于安全审计和平台运营分析。操作日志中的敏感个人信息（手机号、邮箱）自动进行掩码处理。
        </li>
        <li>
          <strong>Session Token 与 Cookie 数据</strong>：详见本政策第五条。
        </li>
      </ul>

      <h3 class="text-sm font-semibold text-slate-700 mt-4 mb-2">2.6 我们不会收集的信息</h3>
      <p>为保护您的隐私，我们明确承诺<strong>不会</strong>主动收集以下信息：</p>
      <ul class="list-disc pl-5 space-y-1">
        <li>精确地理位置信息（GPS 坐标等）</li>
        <li>通讯录、相册、短信、剪贴板等终端本地数据</li>
        <li>生物识别信息（人脸、指纹、声纹等）</li>
        <li>金融账户信息（银行卡号、支付密码等）</li>
        <li>行踪轨迹信息</li>
        <li>任何形式的用户画像或跨站行为追踪数据</li>
      </ul>

      <h2 class="text-base font-semibold text-slate-800 mt-8 mb-3">三、我们如何使用您的个人信息</h2>
      <p>我们仅在以下明确的目的范围内使用您的个人信息。如超出以下目的使用，我们将重新取得您的同意：</p>
      <ul class="list-decimal pl-5 space-y-2">
        <li><strong>提供核心服务</strong>：完成注册登录、维护用户会话、展示资料列表、提供搜索和下载功能、匹配课程分类、维护资料版本历史。</li>
        <li><strong>安全防护</strong>：检测和防御爬虫抓取、DDoS 攻击、API 异常调用、恶意文件上传、欺诈注册等安全威胁；对异常登录行为进行风险评估。</li>
        <li><strong>内容审核</strong>：审核用户上传的资料、评论和举报，确保内容符合平台规范和法律法规。</li>
        <li><strong>服务通知</strong>：发送账户安全提醒（包括但不限于异地登录告警、密码修改确认）、版权投诉处理结果、账户注销进度、平台重大规则变更等与服务相关的重要通知。此类通知<strong>不属于商业营销信息</strong>，即使您选择不接收其他类型的通知，此类服务通知仍会发送。</li>
        <li><strong>匿名统计</strong>：基于匿名化或聚合后的数据（无法识别特定个人），分析平台使用趋势、热门资料类型和用户需求，以优化平台功能和改善用户体验。此类统计分析不涉及对个人的识别或画像。</li>
        <li><strong>法律合规</strong>：响应政府部门、司法机关依据法定程序提出的合法请求；依据法律法规要求留存必要的操作记录。</li>
      </ul>
      <div class="bg-blue-50 border border-blue-200 rounded-lg p-3 mt-2">
        <p class="text-blue-800 text-xs"><strong>我们明确承诺：</strong></p>
        <ul class="list-disc pl-5 space-y-0.5 text-xs text-blue-700">
          <li>不会将您的个人信息用于商业营销或广告推送。</li>
          <li>不会基于您的个人信息构建用户画像或进行自动化决策（详见第十条）。</li>
          <li>不会将您的个人信息出售给任何第三方。</li>
          <li>不会将您的个人信息用于与上述目的无关的用途。</li>
        </ul>
      </div>

      <h2 class="text-base font-semibold text-slate-800 mt-8 mb-3">四、我们如何存储和保护您的个人信息</h2>

      <h3 class="text-sm font-semibold text-slate-700 mt-4 mb-2">4.1 存储地点</h3>
      <p>您的个人信息全部存储于<strong>中华人民共和国境内</strong>（阿里云服务器，位于华东地域）。我们不会将您的个人信息转移或传输至境外。如因业务需要确需向境外传输，我们将按照《个保法》第三十八条的要求，通过国家网信部门的安全评估或取得您的单独同意，并告知您境外接收方的名称、联系方式、处理目的和方式。</p>

      <h3 class="text-sm font-semibold text-slate-700 mt-4 mb-2">4.2 存储期限</h3>
      <p>我们仅在实现处理目的所必需的最短期限内保留您的个人信息，超出期限后将进行删除或匿名化处理。具体存储期限如下：</p>
      <ul class="list-disc pl-5 space-y-1">
        <li><strong>账户信息</strong>（手机号、学号、邮箱等）：在账户存续期间保留。账户注销后，我们将在<strong>15 个工作日内</strong>完成个人信息删除，法律法规另有规定的除外。</li>
        <li><strong>用户上传的资料及文件</strong>：在资料存续期间保留。资料被删除后，关联的 OSS 文件在<strong>30 天宽限期</strong>后被垃圾回收清理。</li>
        <li><strong>审计日志</strong>（含 IP 哈希及操作记录）：保留<strong>90 天</strong>，期满后自动清理。</li>
        <li><strong>短信验证码及临时缓存数据</strong>：保留<strong>3 至 5 分钟</strong>后自动失效。</li>
        <li><strong>版权投诉记录</strong>：依法保留至投诉处理完毕后<strong>6 个月</strong>，期满后删除。</li>
      </ul>
      <p class="text-slate-500 italic mt-1">上述存储期限届满后，我们将对个人信息进行删除或匿名化处理。法律法规另有强制性保留要求的，从其规定。</p>

      <h3 class="text-sm font-semibold text-slate-700 mt-4 mb-2">4.3 安全措施</h3>
      <p>我们采取以下技术和管理措施保护您的个人信息安全：</p>
      <ul class="list-decimal pl-5 space-y-1">
        <li><strong>传输加密</strong>：全站启用 HTTPS/TLS 1.2+ 加密传输，对所有 API 请求强制使用 HTTPS。</li>
        <li><strong>存储加密</strong>：手机号、学号等敏感个人信息使用 AES-256-GCM 算法加密存储于数据库。密码使用 bcrypt 加盐哈希存储（cost factor ≥ 12）。验证码使用 HMAC-SHA256 加盐后暂存于 Redis。</li>
        <li><strong>访问控制</strong>：数据库和服务器实行最小权限访问策略，按需授权。敏感数据的访问操作均记录审计日志。生产环境数据库仅限应用服务器内网访问。</li>
        <li><strong>安全中间件</strong>：部署了安全头中间件（Content-Security-Policy、X-Frame-Options: DENY、X-Content-Type-Options: nosniff、Strict-Transport-Security 等）、API 反代防护中间件、速率限制中间件和 DDoS 防护中间件。</li>
        <li><strong>数据备份</strong>：数据库每日定时加密备份，备份文件存储于独立的阿里云 OSS Bucket，备份保留周期为 30 天。</li>
        <li><strong>漏洞管理</strong>：CI 流程中集成依赖漏洞扫描（pip-audit、npm audit），高危漏洞阻断部署。定期进行安全依赖更新。</li>
        <li><strong>日志与监控</strong>：关键操作记录审计日志，异常行为触发告警。审计日志中不记录明文敏感信息。</li>
      </ul>

      <h3 class="text-sm font-semibold text-slate-700 mt-4 mb-2">4.4 个人信息安全事件的处置</h3>
      <p>在发生或者可能发生个人信息泄露、篡改、丢失的安全事件时，我们将：</p>
      <ul class="list-decimal pl-5 space-y-1">
        <li>立即启动应急预案，采取补救措施防止危害扩大；</li>
        <li><strong>在 72 小时内</strong>按照法律法规的要求，通过站内消息、短信或邮件等有效方式及时告知您事件的基本情况、可能的影响、我们已采取或将要采取的处置措施、您可以采取的防范和降低风险的建议；</li>
        <li>按照《个保法》第五十七条的规定，向履行个人信息保护职责的部门报告；</li>
        <li>对事件原因进行调查并记录，采取措施防止类似事件再次发生。</li>
      </ul>
      <p class="text-slate-500 italic mt-2">尽管我们采取了上述合理的安全措施，需要提醒您：互联网环境并非绝对安全，没有任何安全措施是完美无缺的。您应妥善保管您的账号密码和验证码，不要将其提供给任何第三方。</p>

      <h2 class="text-base font-semibold text-slate-800 mt-8 mb-3">五、Cookie、Token 与同类技术</h2>
      <p>为保障平台基本功能的正常运行，我们使用以下必要的 Cookie 和 Token 技术：</p>
      <ul class="list-disc pl-5 space-y-2">
        <li><strong>access_token</strong>（HttpOnly, Secure, SameSite=Lax, 有效期 15 分钟）：JSON Web Token (JWT)，存储于 HttpOnly Cookie 中，用于验证您的登录状态和身份。JavaScript 无法读取此 Cookie，降低了 XSS 攻击下的令牌泄露风险。</li>
        <li><strong>refresh_token</strong>（HttpOnly, Secure, SameSite=Strict, 有效期 7 天）：用于在 access_token 过期后自动续期，避免您频繁重新登录。SameSite=Strict 设置可有效防止 CSRF 攻击。</li>
      </ul>
      <p>我们<strong>不使用</strong>以下技术：</p>
      <ul class="list-disc pl-5 space-y-1">
        <li>第三方分析 Cookie（如 Google Analytics、百度统计等）；</li>
        <li>广告 Cookie 或广告标识符；</li>
        <li>跨站追踪 Cookie 或浏览器指纹技术；</li>
        <li>Flash Cookie、ETag 追踪等隐蔽追踪技术。</li>
      </ul>
      <p>您可以通过浏览器设置管理和删除 Cookie。但请注意，禁用必要的 Cookie 将导致您无法登录或使用需要身份验证的功能。大多数浏览器允许您针对特定网站设置 Cookie 例外。</p>

      <h2 class="text-base font-semibold text-slate-800 mt-8 mb-3">六、我们如何委托处理、共享、转移和公开披露您的个人信息</h2>

      <h3 class="text-sm font-semibold text-slate-700 mt-4 mb-2">6.1 委托处理</h3>
      <p>本平台的部分功能依赖以下第三方服务提供商（受托处理者）提供的基础设施服务：</p>
      <ul class="list-disc pl-5 space-y-2">
        <li><strong>阿里云计算有限公司</strong>：提供云服务器（ECS，华东地域）、对象存储（OSS）、短信服务（SMS）、云数据库（RDS for PostgreSQL 16）、缓存服务（Redis 7）、搜索服务（Elasticsearch 8）等基础设施。在短信发送过程中，您的手机号码会传输至阿里云短信服务。</li>
        <li><strong>GitHub, Inc.</strong>：托管项目开源代码和用户反馈（Issue）。用户在 GitHub Issues 中提交的内容受 GitHub 隐私政策约束。</li>
      </ul>
      <p>我们与上述服务商签订了数据处理协议，要求其按照我们的指示及法律法规要求处理个人信息，采取适当的安全措施，不得将个人信息用于其他目的。我们会定期评估服务商的安全能力和合规表现。</p>

      <h3 class="text-sm font-semibold text-slate-700 mt-4 mb-2">6.2 共享</h3>
      <p>我们<strong>不会</strong>主动向任何第三方共享您的个人信息，但以下情形除外：</p>
      <ul class="list-disc pl-5 space-y-1">
        <li>在取得您的<strong>单独同意</strong>后，在授权范围内共享。</li>
        <li>依据法律法规规定，或依据政府主管部门、司法机关的强制性要求（如法院传票、调查令等），在核实法律文书的真实性和合法性后提供。</li>
        <li>与上述 6.1 条所述的受托处理者共享，且仅限于实现本政策所述服务功能所必需的范围。</li>
      </ul>

      <h3 class="text-sm font-semibold text-slate-700 mt-4 mb-2">6.3 转移</h3>
      <p>我们不会将您的个人信息转让给任何第三方。如本平台因运营主体变更、合并、分立、解散等原因需要转移个人信息，我们会：</p>
      <ul class="list-decimal pl-5 space-y-1">
        <li>向您告知接收方的名称（或姓名）和联系方式；</li>
        <li>要求接收方继续履行本隐私政策的义务；</li>
        <li>如接收方变更处理目的或方式，要求其重新取得您的同意。</li>
      </ul>

      <h3 class="text-sm font-semibold text-slate-700 mt-4 mb-2">6.4 公开披露</h3>
      <p>我们仅在以下情形公开披露您的个人信息：</p>
      <ul class="list-disc pl-5 space-y-1">
        <li>在取得您的<strong>单独同意</strong>后。</li>
        <li>根据法律法规、诉讼程序或政府主管部门的强制性要求。</li>
      </ul>
      <p>在任何情况下，我们不会公开披露您的手机号码、学号、邮箱等敏感个人信息。</p>

      <h2 class="text-base font-semibold text-slate-800 mt-8 mb-3">七、您的权利</h2>
      <p>根据《个保法》第四章及相关法律法规，您对您的个人信息享有以下权利。我们将通过以下方式保障您的权利行使：</p>

      <h3 class="text-sm font-semibold text-slate-700 mt-4 mb-2">7.1 查阅权</h3>
      <p>您可以在登录后通过「个人中心」页面查阅您已提供的个人信息（包括昵称、手机号码掩码、绑定的邮箱、已上传的资料列表、评论记录等）。如需查阅完整的个人信息清单，可通过第十二条所述方式联系我们，我们将在核实身份后提供。</p>

      <h3 class="text-sm font-semibold text-slate-700 mt-4 mb-2">7.2 复制权与可携带权</h3>
      <p>您有权获取您提供的个人信息的副本。如需导出您在平台上的个人信息副本（包括上传的资料、评论内容等），可通过第十二条所述方式联系我们。我们将在核实身份后<strong>15 个工作日内</strong>以结构化、通用的电子格式（JSON 或 PDF）向您提供。</p>

      <h3 class="text-sm font-semibold text-slate-700 mt-4 mb-2">7.3 更正、补充权</h3>
      <p>如您发现您的个人信息不准确或不完整，可以在「个人设置」页面自行更正昵称、绑定或更换邮箱。部分信息的更正（如手机号更换）可能需要进行短信验证以确认身份。</p>

      <h3 class="text-sm font-semibold text-slate-700 mt-4 mb-2">7.4 删除权</h3>
      <p>在以下情形下，您可以要求我们删除您的个人信息：</p>
      <ul class="list-disc pl-5 space-y-1">
        <li>处理目的已实现、无法实现或者为实现处理目的不再必要；</li>
        <li>我们停止提供产品或者服务，或者存储期限已届满；</li>
        <li>您撤回同意；</li>
        <li>我们违反法律、行政法规或者违反约定处理您的个人信息；</li>
        <li>法律、行政法规规定的其他情形。</li>
      </ul>
      <p>您可以通过「个人设置」中的「注销账户」功能或联系我们行使删除权。法律、行政法规规定的保存期限未届满，或者删除个人信息从技术上难以实现的，我们将停止除存储和采取必要的安全保护措施之外的处理。</p>

      <h3 class="text-sm font-semibold text-slate-700 mt-4 mb-2">7.5 注销账户权</h3>
      <p>您可以通过以下方式注销账户：</p>
      <ul class="list-decimal pl-5 space-y-1">
        <li>登录后进入「个人设置」→「隐私设置」，选择「注销账户」；</li>
        <li>提交注销申请后，账户将进入<strong>30 天冷静期</strong>，期间您可以撤销注销申请；</li>
        <li>冷静期届满后，我们将在<strong>15 个工作日内</strong>永久删除您的手机号、学号、邮箱、密码等个人信息；</li>
        <li>您上传的资料可选择<strong>匿名化保留</strong>（贡献者显示为「已注销用户」）或<strong>一并删除</strong>；</li>
        <li>审核记录、版权投诉记录等依法需要保留的信息，将在法定保留期限后删除；</li>
        <li>注销账户时，我们<strong>不会要求您额外提供</strong>超出注册时已收集范围的信息（如人脸识别、手持身份证照片等）。</li>
      </ul>

      <h3 class="text-sm font-semibold text-slate-700 mt-4 mb-2">7.6 撤回同意权</h3>
      <p>您可以通过注销账户撤回对个人信息处理的同意。对于可选的个人信息收集（如学号验证），您可在「个人设置」中撤回此前授予的同意。撤回同意不影响撤回前基于同意已进行的个人信息处理活动的合法性。</p>

      <h3 class="text-sm font-semibold text-slate-700 mt-4 mb-2">7.7 解释说明权</h3>
      <p>您有权要求我们对个人信息处理规则进行解释说明。如您对本隐私政策的任何条款有疑问，可通过第十二条所述方式联系我们，我们将予以解释。</p>

      <h3 class="text-sm font-semibold text-slate-700 mt-4 mb-2">7.8 死者近亲属权利</h3>
      <p>在符合法律法规规定的情形下，死者近亲属可对死者的相关个人信息行使查阅、复制、更正、删除等权利。行使该等权利时，近亲属需提供身份证明和亲属关系证明。</p>

      <h3 class="text-sm font-semibold text-slate-700 mt-4 mb-2">7.9 响应机制</h3>
      <p>您可以通过本政策第十二条所述的联系方式行使上述权利。为保障安全，我们可能会要求您提供身份验证信息。我们将在收到您的请求后<strong>15 个工作日内</strong>完成处理并回复。对于合理请求，我们不收取费用，但对多次重复、超出合理限度的请求，我们可能酌情收取成本费用。对于无正当理由重复、需要过多技术手段（如需要开发新系统或从根本上改变现行惯例）、给他人合法权益带来风险或非常不切实际的请求，我们可能予以拒绝，但将向您说明理由。</p>

      <h2 class="text-base font-semibold text-slate-800 mt-8 mb-3">八、未成年人保护</h2>

      <h3 class="text-sm font-semibold text-slate-700 mt-4 mb-2">8.1 一般规定</h3>
      <p>本平台主要面向四川大学在校学生（一般为年满 18 周岁的成年人）。我们高度重视未成年人的个人信息保护。如果您是未成年人，请在您的监护人的陪同下阅读本隐私政策，并在征得监护人同意的前提下使用本平台。</p>

      <h3 class="text-sm font-semibold text-slate-700 mt-4 mb-2">8.2 儿童（不满十四周岁）个人信息保护</h3>
      <p>根据《儿童个人信息网络保护规定》，我们对不满十四周岁的儿童的个人信息实施更严格的保护：</p>
      <ul class="list-disc pl-5 space-y-2">
        <li>我们<strong>不会主动</strong>向儿童提供平台服务或收集儿童的个人信息。</li>
        <li>如儿童需要使用本平台，必须由其<strong>监护人仔细阅读并明确同意</strong>本隐私政策。我们仅在取得监护人明确同意的情况下，收集该儿童提供服务所必需的个人信息。</li>
        <li>监护人同意应以可验证的方式作出（如通过监护人手机号码进行验证）。</li>
        <li>如监护人不同意本隐私政策，该儿童不得注册或使用本平台。</li>
        <li>如我们发现无意中收集了儿童的个人信息且未经其监护人同意，我们将在核实后<strong>立即删除</strong>该信息。</li>
        <li>监护人如发现被监护人在未经同意的情况下向我们提供了个人信息，或希望查阅、更正、删除被监护人的个人信息，可立即通过第十二条所述方式联系我们。</li>
        <li>我们不会将儿童的个人信息用于任何商业目的或进行用户画像。</li>
      </ul>

      <h3 class="text-sm font-semibold text-slate-700 mt-4 mb-2">8.3 十四至十八周岁的未成年人</h3>
      <p>对于年满十四周岁但未满十八周岁的未成年人，建议在监护人指导下使用本平台，并在注册和使用前仔细阅读本隐私政策。</p>

      <h2 class="text-base font-semibold text-slate-800 mt-8 mb-3">九、免责声明</h2>
      <ul class="list-disc pl-5 space-y-2">
        <li><strong>不可抗力</strong>：因自然灾害、战争、政府行为、法律法规变更、计算机病毒大规模爆发、黑客攻击、电信部门技术调整等不可抗力事件导致的服务中断或信息泄露，我们在法律允许的范围内不承担责任，但将尽力减少您的损失，并在事件发生后按照第 4.4 条的规定及时通知您。</li>
        <li><strong>用户自身原因</strong>：因您保管不当导致账号密码、验证码泄露，或将账号出借、出租给他人使用所造成的信息泄露和损失，由您自行承担责任。我们建议您启用设备锁屏密码、不在公共设备上保存登录状态、定期更换密码。</li>
        <li><strong>第三方服务</strong>：本平台可能包含指向第三方网站或服务的链接。此类第三方网站的隐私政策和数据处理行为不在本平台的控制范围内。我们会在用户点击外部链接前弹出离开确认提示，但不对第三方网站的内容、隐私保护措施或数据处理行为承担责任。建议您在访问第三方网站前仔细阅读其隐私政策。</li>
        <li><strong>学生社区运维</strong>：本平台由学生志愿者利用课余时间维护，无法提供 7×24 小时专业运维保障。服务可能出现临时中断，我们将尽力及时恢复，并通过站内公告等方式通知用户。计划内的维护将尽量安排在访问量较低的时段并提前公告。</li>
      </ul>

      <h2 class="text-base font-semibold text-slate-800 mt-8 mb-3">十、自动化决策</h2>
      <p>根据《个保法》第二十四条，我们将自动化决策相关情况说明如下：</p>
      <ul class="list-disc pl-5 space-y-2">
        <li>本平台<strong>不进行</strong>任何形式的自动化决策。平台不通过计算机程序自动分析、评估个人的行为习惯、兴趣爱好或者经济、健康、信用状况等，也不进行自动化决策以决定是否向您推送特定内容。</li>
        <li>平台的资料推荐和排序<strong>不基于用户个人画像</strong>，而是基于资料的公开属性（如上传时间、下载次数、评分、维护者精选标记等）和用户主动输入的搜索条件。</li>
        <li>搜索结果和资料列表的排序规则对所有用户一视同仁，不会因用户的身份、历史行为等因素进行差异化呈现。</li>
        <li>如未来平台功能调整涉及自动化决策，我们将按照法律法规要求进行个人信息保护影响评估，并在功能上线前更新本隐私政策以告知您决策的基本原理、处理目的和方式，同时提供拒绝自动化决策的选项。</li>
      </ul>

      <h2 class="text-base font-semibold text-slate-800 mt-8 mb-3">十一、本政策的更新</h2>
      <p>我们可能根据法律法规变化、平台功能调整或运营需要不时更新本隐私政策。更新方式如下：</p>
      <ul class="list-disc pl-5 space-y-2">
        <li>更新后，我们将在平台上公布最新版本并更新生效日期和版本号。</li>
        <li>对于<strong>重大变更</strong>，我们还将通过站内消息、短信或邮件等合理方式向您发送通知，并在必要时<strong>重新征得您的同意</strong>。</li>
        <li>重大变更包括但不限于：
          <ul class="list-circle pl-5 space-y-0.5 mt-1">
            <li>我们的服务模式发生重大变化，如处理个人信息的目的、类型、方式发生实质性变化；</li>
            <li>我们在所有权结构、组织架构方面发生重大变化；</li>
            <li>个人信息共享、转移或公开披露的主要对象发生变化；</li>
            <li>您参与个人信息处理方面的权利及其行使方式发生重大变化；</li>
            <li>个人信息存储期限发生重大变化；</li>
            <li>我们负责个人信息安全的责任部门、联络方式及投诉渠道发生变化。</li>
          </ul>
        </li>
      </ul>
      <p><strong>如您不同意更新后的隐私政策，您应当停止使用本平台。在重大变更生效后继续使用本平台，即表示您同意更新后的隐私政策。</strong>如更新涉及需要重新征得同意的内容，我们将在取得您的同意后方按新的政策处理您的个人信息。</p>

      <h2 class="text-base font-semibold text-slate-800 mt-8 mb-3">十二、联系我们</h2>
      <p>如您对本隐私政策有任何疑问、意见、建议或投诉，或希望行使您的个人信息权利，请通过以下方式联系我们：</p>
      <ul class="list-disc pl-5 space-y-1">
        <li><strong>电子邮箱</strong>：<a href="mailto:admin@scustack.com" class="text-primary-600 hover:text-primary-700">admin@scustack.com</a>（推荐，响应最快）</li>
        <li><strong>GitHub Issues</strong>：<a href="https://github.com/yeyixiang2007/scustack/issues" target="_blank" rel="noopener" class="text-primary-600 hover:text-primary-700">yeyixiang2007/scustack/issues</a></li>
        <li><strong>通信地址</strong>：四川省成都市双流区川大路 四川大学江安校区</li>
      </ul>
      <p>我们将在收到您的请求后 <strong>15 个工作日内</strong>予以回复。如果您对我们的回复不满意，或认为我们的个人信息处理行为损害了您的合法权益，您可以向<strong>国家互联网信息办公室</strong>（举报平台：www.12377.cn）或其他履行个人信息保护职责的部门进行投诉或举报，或向有管辖权的人民法院提起诉讼。</p>
    </div>
  </div>
</template>
