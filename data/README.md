# 数据目录

| 子目录 | 内容 | 使用方式 |
| --- | --- | --- |
| raw | 原始UserBehavior.csv，100,150,807条日志 | 原始输入，分析脚本只读 |
| processed | 清洗明细、用户/商品/品类汇总、用户日/商品日、购买间隔与analysis.sqlite | 数据分析与SQL查询使用 |
| intermediate | 分块聚合的SQLite中间数据与绘图运行缓存 | 由脚本生成，通常无需手动打开 |

统计结果表与图表在[results](../results/README.md)，招聘展示材料在[reports](../reports/README.md)。

processed中的压缩CSV建议分块读取；SQL入口为 `analysis.sqlite`。原始数据与大型处理明细保留在本地项目，不纳入Git仓库。下载原始数据并放在 `data/raw/UserBehavior.csv` 后，可按[代码说明](../Scripts/代码说明.md)运行分析。
