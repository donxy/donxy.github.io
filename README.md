# donxy · 个人知识站

主页：[https://donxy.github.io/](https://donxy.github.io/)

本仓库负责个人知识门户与 [科研配图拆解](https://donxy.github.io/figure-teardown/)。
另外两条内容线独立构建和部署：

- [RGB-T 论文笔记](https://donxy.github.io/rgbt-notes/) — `donxy/rgbt-notes`（Quartz 4）。
- [无人驾驶技能树](https://donxy.github.io/autonomous-driving-notes/) — `donxy/autonomous-driving-notes`（Quartz 4）。

论文目录与统计来源为 `donxy/awesome-RGBT-ObjectDetection`。
主站使用 `tools/index.template.html`、`tools/build_homepage.py` 与 `tools/build_site_metadata.py` 生成首页、分享图片及跨站 JSON 元数据。

维护入口：

- [工程架构及数据同步](docs/ARCHITECTURE.md)
- [统一设计规范](docs/DESIGN_SYSTEM.md)
- [跨站共享 CSS](design/shared.css)
- [定时同步工作流](.github/workflows/sync-portal.yml)

各专题仓库独立发布，主站不复制子站文章正文。
