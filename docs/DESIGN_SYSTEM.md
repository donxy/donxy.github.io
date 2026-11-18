# 个人知识站统一设计规范（v1）

此文件是三个站点共同遵守的视觉约定；代码基准为主站 `/design/shared.css`。**不统一各个主题站的品牌强调色**，避免科研、视觉、无人驾驶失去区分度。

## 核心原则

1. 内容优先：正文可读、来源可辨，装饰让位于阅读。
2. 共享基础：字体栈、行高、圆角、焦点提示、动效节奏统一。
3. 保留专题个性：主站森林绿，Quartz 子站原有青绿／暖橙，三条首页栏目各自保留识别色。
4. 可访问性：键盘焦点可见、支持减少动画、正文与证据文字符合对比度要求。
5. 性能优先：不引入外部字体、前端框架或追踪 SDK。

## CSS tokens

| 变量 | 当前值 | 用途 |
| --- | --- | --- |
| `--dn-font-display` | 本地中文衬线字体栈 | 标题、站名 |
| `--dn-font-body` | 系统中文无衬线字体栈 | 正文 |
| `--dn-font-mono` | 系统等宽字体栈 | 代码 |
| `--dn-body-line-height` | 1.78 | 长文阅读 |
| `--dn-body-tracking` | 0.012em | 中文字距 |
| `--dn-radius-small` | 8px | 次要容器 |
| `--dn-radius-card` | 12px | 普通卡片 |
| `--dn-radius-feature` | 14px | 首页重点卡片 |
| `--dn-focus-width` | 2px | 键盘聚焦描边 |
| `--dn-duration-fast` | 160ms | 轻量交互 |
| `--dn-reading-measure` | 760px | 单栏文章参考宽度 |

## 加载方式与发布顺序

主站直接引用 `/design/shared.css`；两个 Quartz 子站在 `quartz/styles/custom.scss` 中使用 CSS `@import url("https://donxy.github.io/design/shared.css")`。各处使用 `var(--dn-*, fallback)`，即使主站样式暂时不可访问，也能沿用原有独立样式。

**发布顺序**：先合并主站 PR，确认 CSS 文件在线，再合并两个子站 PR。每个子站须单独运行 `npx quartz build` 与移动端检查。

## 不共享的内容

- Quartz 的 `--light`、`--secondary` 等主题变量（由各站 `quartz.config.ts` 管理）。
- HTML 页面结构、各站独有卡片布局及文章目录。
- 原始论文图片、图表颜色与学术配图风格。
- 数据来源标记：语义标签建议共享名称，但证据可信度由文章内容决定，不能只靠颜色表达。

## 变更验收

375 / 768 / 1280 / 1440px 宽度；浅色、深色；键盘 Tab；系统减少动画；长表格滚动；子站离线预览。共享变量重命名必须兼容旧 fallback。
