# UserBehavior：电商转化与商品运营分析

基于约1亿条淘宝行为日志，完成经营分析、顺序转化、用户分层、留存复购与商品运营分析。

## 快速找到文件

| 想查看的内容 | 直接打开 |
| --- | --- |
| 给招聘者演示项目 | [9页作品集](reports/UserBehavior_Portfolio.pdf) |
| 阅读融合后的完整分析与业务结论 | [综合分析报告 PDF](reports/综合分析报告.pdf)；[Markdown 原文](reports/综合分析报告.md) |
| 浏览融合看板 | [综合看板.html](reports/综合看板.html) |
| 编辑Power BI报表 | [UserBehavior.pbip](PowerBI/UserBehavior.pbip) |
| 了解原始数据与获取方式 | [数据说明](data/README.md) |
| 找清洗数据、用户/商品明细和SQLite | [data/processed](data/processed/) |
| 找分主题结果表和图表 | [results目录导航](results/README.md) |
| 找重点用户和商品清单 | [运营清单](results/10_operating_lists/README.md) |
| 看处理与分析代码 | [代码说明](Scripts/代码说明.md) |

## 目录职责

| 目录 | 存放内容 |
| --- | --- |
| data | 数据获取说明；processed保留可在GitHub存储的分析明细；本地raw与intermediate用于运行 |
| Scripts | 数据处理、分析、验证、报表生成代码与核心SQL |
| results | 按主题分类的结果表、图表、核验记录和运营清单 |
| reports | 招聘展示PDF、可编辑报告、HTML看板与详细分析底稿 |
| PowerBI | 独立完整的Power BI源项目、模型、DAX、Power Query与数据快照 |
| docs | 任务需求、指标字典、数据字典与目录调整记录 |

原始CSV（约3.4 GB）、清洗事件明细（约1.1 GB）与运行中间数据不提交到GitHub；这些文件保留在本地，下载原始数据后可按[代码说明](Scripts/代码说明.md)重建。其余代码、报告、Power BI项目、结果和体积低于GitHub单文件限制的处理数据纳入仓库。

## 运行入口

在UserBehavior目录执行 `python Scripts/run_pipeline.py` 可重建原始数据分析阶段。脚本导航与运行说明见[代码说明](Scripts/代码说明.md)。

SQL查询：`sqlite3 data/processed/analysis.sqlite < Scripts/core_queries.sql`。

分析与绘图依赖pandas、NumPy、Matplotlib；PDF排版依赖ReportLab、pypdf；Power BI结构验证依赖jsonschema。完整项目说明见各目录README与docs。
