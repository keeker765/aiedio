# AI 内容工厂 (AI Video Generation Pipeline) - UX 调研与角色画像文档

## 1. 调研问题清单（访谈大纲）
在构建功能与假设之前，为了获取真实洞察，我们设计了以下半结构化访谈提纲（Semi-structured interview script）：

- **Current Workflow (现状)**: "请描述您目前的视频制作流程。从创意到发布需要多久？" (Walk us through your current video production process. How long does it take from idea to post?)
- **Pain Points (痛点)**: "在整个流程中，最昂贵或最耗时的是哪一部分？" (What is the single most expensive or time-consuming part of your process?)
- **AI Experience (AI经验)**: "您之前用过生成式AI视频工具吗？如果有，是什么原因让您停止使用或感到犹豫？" (Have you used Gen-AI video tools before? If so, what was the 'deal-breaker' that made you stop or hesitate?)
- **Desired Outcome (理想诉求)**: "如果你有魔法棒，你最想把哪一个重复性任务自动化？" (If you had a magic wand, what one repetitive task would you automate today?)

## 2. 详细用户画像 (Detailed UX Personas)
通过整合访谈反馈以及百科标准的 Persona 定义方法，我们扩展并确立了三个核心使用者画像。加入了引言、人口统计学指标和无障碍需求，确保设计团队和架构开发有清晰的锚点。

### Persona 1: 追求效率的故事讲述者 —— 阿杰 (Ah Jie)
- **引言 (Quote)**: *"我的主页是按天算流量的，不更新就会被遗忘。可现在的AI视频像抽盲盒，我没法把一个连贯的故事讲完。"*
- **人口统计学 (Demographics)**: 本名张杰 / 28岁 / 男 / 一线城市（广州）/ 独立全职博主 / 本科毕业（新媒体专业）
- **个人经历 (Bio)**: 阿杰是一名真正的“数字原住民”（digital native），靠社交平台的内容循环谋生。他需要每天高频地产出视频，但是每天亲自出镜、换装、打光的物理极限成为了他工作室最大的瓶颈。
- **科技使用偏好 (Tech Literacy)**: 高级。深谙网络梗，熟悉 Midjourney 的使用，能熟练运用 CapCut (剪映) 与 Premiere。
- **无障碍与特殊需求 (Accessibility Needs)**: 高强度深夜剪辑引发了严重的“视频眼疲劳”。系统后台必须提供纯正的**暗黑模式 (Dark Mode)**；且经常在公众场合审核导出成片，对 UI 上的字幕可视化提示依赖很大。
- **核心痛点 (Frustrations)**:
  - **“抽盲盒”效应 (The Lottery Effect)**：角色特征（头发、脸型、服装）在每 5 秒的视频切片之间随机发生变化，无法拼接为整体。
  - **缺乏灵魂 (Lack of Soul)**：AI 视频常常追求“完美质感”，从而失去了他的粉丝最喜欢的随性、幽默和人类特有的人情味。
- **核心需求 (Key Requirement)**: **基于 Seed 的统一性连贯 (Seed-based consistency)**。允许上传一到两张参考大头贴，让系统基于这张脸在不同的机位和场景下"扮演角色"。

### Persona 2: 务实的电商创业者 —— 丽姐 (Li Jie)
- **引言 (Quote)**: *"视频对我来说就是卖货的工具。给摄影师多花一块钱，我的利润就少一块钱；如果买家收到觉得货不对板，我就得面临退货大灾难。"*
- **人口统计学 (Demographics)**: 李丽 / 35岁 / 女 / 电商产业带（义乌）/ 已婚育有一子 / 手工饰品网店老板
- **个人经历 (Bio)**: 丽姐经营着一家利润极薄的作坊式店铺。她的运作方式非常务实（lean operation）。对她而言，视频不是拿来审美的，只是用作销售转化的手段。
- **科技使用偏好 (Tech Literacy)**: 中等。熟练使用淘宝千牛、剪映等应用，但对复杂的英文 Prompt (咒语) 感到恐惧。
- **无障碍与特殊需求 (Accessibility Needs)**: 在仓库理货或带孩子时常常需要**单手触控/盲操**，要求后台的控制界面布局需遵循“大拇指操作区”，按钮必须粗大。不需要花哨转场，需要高对比度界面避免认知过载。
- **核心痛点 (Frustrations)**:
  - **系统幻觉 (Visual Hallucinations)**：AI 总是在视频生成中给出多余的手指，或是由于动作导致本来圆形的饰品变形（这会误导消费者被投诉）。
  - **喧宾夺主 (Distracting Backgrounds)**：AI 自作主张生成的奇幻背景不仅很假，还会把注意力从商品本身剥离。
- **核心需求 (Key Requirement)**: **以产品为中心的控制域 (Product-Centric Control)**。比如一种“极度稳定的背景替换”或“图转动效”功能，让她的商品图维持100%的物理真实，仅仅是让背景水波纹动起来或光影发生推移。

### Persona 3: 数据驱动的战略操盘手 —— 王总 (Mr. Wang)
- **引言 (Quote)**: *"周一早上广告发满全网，下午出 ROI 数据。如果效果不好，周二早上必须上新素材！传统广告公司根本跑不赢这个速度。"*
- **人口统计学 (Demographics)**: 王强 / 42岁 / 男 / 北京 / 已婚 / 大型教育科技企业 (EdTech) 营销总监
- **个人经历 (Bio)**: 王总手中掌握着百万级的投放预算，但也扛着极其沉重的转化压力。他将视频广告视为可随时替换跑量的“可变变量”，完全以点击率 (CTR) 决定素材去留。
- **科技使用偏好 (Tech Literacy)**: 偏管理和战略级。非常在意工作流系统 (Workflow) 的兼容性。他不屑于具体修某个按钮，只看仪表盘和终审数据。
- **无障碍与特殊需求 (Accessibility Needs)**: 轻度色弱（红绿色盲），由于经常需要一目了然看“审批通过/审批驳回”以及“数据涨/跌”，因此 UI 必须避免使用纯色块表达状态，而应配有强视觉差的“对勾/叉号”与文字说明。另外要求系统支持全局快捷键快速同意/打回。
- **核心痛点 (Frustrations)**:
  - **内部合规摩擦 (Workflow Friction)**：由于 AI 生成内容的随机性很大，常常偏离了公司严格的品牌标准（指南），导致常常被法务部卡住无法出街。
  - **迭代太慢 (Slow Iteration)**：即使是自家的设计师或外包团队，也很难跟上他“按天调整”的要求。
- **核心需求 (Key Requirement)**: **企业级品牌模板 (Enterprise Templates)**。一个可以将其公司“Logo防伪水印限制”、“专属十六进制色彩库 (Hex Colors)”、“固定打光风格”进行硬编码锁定的大型层级系统，基层员工怎么发散也不会越过合规红线。

