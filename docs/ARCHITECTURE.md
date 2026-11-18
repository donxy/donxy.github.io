# 个人笔记站工程架构

**站点入口**：https://donxy.github.io/。采用多仓库静态站点，不是一个单体前端应用。

## 仓库与职责

| 仓库 | 职责 | URL | 构建 |
|---|---|---|---|
| `donxy/donxy.github.io` | 个人门户及科研配图拆解 | `/`, `/figure-teardown/` | 原生 HTML + Python |
| `donxy/rgbt-notes` | RGB-T 论文精读、专题、数据集、对比 | `/rgbt-notes/` | Quartz 4 |
| `donxy/autonomous-driving-notes` | 《无人驾驶技能树》 | `/autonomous-driving-notes/` | Quartz 4 |
| `donxy/awesome-RGBT-ObjectDetection` | 结构化论文目录与数据源 | 无独立站点 | CSV → 笔记 |

## 单一数据来源

- RGB-T 篇数、核心/附录、全文精读：`awesome-RGBT-ObjectDetection/papers.csv`。
- RGB-T 数据集数量：`rgbt-notes/content/datasets/` 下的数据集页面，不含索引。
- 科研配图篇数、标题、链接：本仓库 `figure-teardown/issues.json`。
- 无人驾驶篇数、五组分类：`autonomous-driving-notes/content/`，排除 `index.md`。
- 最近更新：由 Git 各篇最后一次提交日期计算；**不是**文章内「信息截至」日期。

主站 `tools/build_homepage.py` 生成 `index.html` 和 `og.png`。
主站 `tools/build_site_metadata.py` 生成 `site-metadata.json`（版本 1，三站数量、分类、最近更新）。
禁止在首页模板手动改写派生统计值。

## 数据同步与部署

1. RGB-T、无人驾驶子站：各自向 `main` 推送后由 `deploy.yml` 使用 Quartz 构建、发布。
2. 主站：`.github/workflows/sync-portal.yml` 每天 02:17 UTC 定时运行，也可手动触发。它克隆三个**公开**源仓库，生成首页与 JSON，并仅在输出有变化时提交回主站 `main`。
3. **GitHub Pages 发布源**需保持与主站仓库现有 Pages 设置一致；这一工作流更新主站的静态文件，并不改变 Pages 设置。

### 在本地重建

```bash
export PAPERS_CSV=/path/to/awesome-RGBT-ObjectDetection/papers.csv
export ISSUES_JSON=/path/to/donxy.github.io/figure-teardown/issues.json
export AD_CONTENT=/path/to/autonomous-driving-notes/content
python tools/build_homepage.py --out .
python tools/build_site_metadata.py \
  --papers-csv "$PAPERS_CSV" \
  --issues-json "$ISSUES_JSON" \
  --ad-content "$AD_CONTENT" \
  --rgbt-content /path/to/rgbt-notes/content \
  --output site-metadata.json
```

生成封面 `og.png` 需要 Pillow 和 Noto CJK 字体。全站数据聚合只需要公开仓库，不依赖私有 token。

## 统一 UI

标准位于 `docs/DESIGN_SYSTEM.md`，共享变量由 `/design/shared.css` 发布；两个子站通过独立 CSS 链接加载，且使用变量 fallback。主站发布在先，子站在后。保持现有页面 URL 与 Quartz 导航结构不变。

## 维护注意

- 不把科研配图拆解误认为独立仓库；其页面就在主站仓库。
- 不在主站重复维护每篇论文全文，数据仍在相应专业仓库。
- 若未来改动源码目录，需同步修改构建脚本和这个文档，并重新核对三站数据。
- 文章页的「信息截至」代表资料核验时点，Git 最近提交不代表事实已重新核验。
