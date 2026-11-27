# 分析结果导航

本目录只存分析结果和核验材料。原始与清洗数据在[data](../data/README.md)，报告在[reports](../reports/README.md)，代码在[Scripts](../Scripts/代码说明.md)。

| 目录 | 内容 | 常用文件 |
| --- | --- | --- |
| 01_data_quality | 数据质量、异常样例与重复敏感性 | quality.json、数据质量报告.md |
| 02_overview | 平台规模、日活与购买覆盖 | overview.csv、daily.csv |
| 03_conversion | 行为覆盖、顺序漏斗与时间窗转化 | conversion_24h.csv、branch_funnel.csv |
| 04_time | 小时、日期、工作日与周末分析 | hour_summary.csv、weekday_weekend.csv |
| 05_users | 留存、购买频次、用户分层与品类偏好 | segments.csv、segment_intents.csv |
| 06_items | 商品与品类榜单、象限、样本门槛与候选 | item_id_high_traffic_low_conversion.csv |
| 07_decision_support | 业务贡献、资源效率与招聘报告衍生指标 | business_findings.json、business_product_quadrants.csv |
| 08_validation | 跨表核对、独立核验、环境信息及运行日志 | validation.csv、independent_validation.csv；日志在logs |
| 09_report_charts | 招聘报告与六页面板使用的图片 | biz_开头的决策图、panel_01至panel_06 |
| 10_operating_lists | 可操作的用户与商品明细 | 重点未购加购用户、单日买家、100个重点商品 |

01至06按分析主题保留CSV以及对应PNG/SVG，便于将结果表与图表对照查看。
