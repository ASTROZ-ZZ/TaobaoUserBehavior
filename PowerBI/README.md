# UserBehavior Power BI 作品集项目

入口：`UserBehavior.pbip`。这是可编辑PBIP项目，包含PBIR报表与TMSL语义模型。当前生成环境为Mac，尚未在Power BI Desktop内打开、刷新或渲染验收，不能视为已通过Desktop兼容验证。

## 打开与验收

1. 在Windows Power BI Desktop中启用当前版本所需的项目/PBIR支持，解压并保持Report与SemanticModel的相对位置。
2. 打开UserBehavior.pbip，执行刷新。模型内置完整快照的Power Query M字面量，无需修改CSV路径，也不连接外部服务；data/下CSV供审计和替换源使用。
3. 核对六页报表是否有缺失视觉对象、字段错误或刷新错误。全期PV=89,660,688，UV=987,991，购买占比68.06%；浏览/加购/收藏24h率分别1.19%/3.96%/3.45%。
4. 确认商品页切片器只过滤展示池，不能将展示池行数或浏览人数之和称为全平台规模。按象限筛选时检查散点与明细同步响应。
5. Cohort矩阵留空不可观察格子。全期卡片与同批留存卡片有意固定范围，不随不相关的日期/人群筛选变化；标题已标明作用范围。
6. 在Desktop保存为PBIX并导出实际截图，替换作品集设计预览后，可用于正式现场演示。当前交付不包含已验证的PBIX或云端发布链接。

## 模型设计与边界

采用多个独立粒度的汇总事实表；没有虚构关联，也不允许跨不同粒度直接拼分母。Period为全期快照，Daily为用户日聚合，Hours为用户小时聚合，Conversion为独立行为起点，Cohort为起始日×偏移日，Products为展示池。基于预聚合数据无法实现任意日期窗口下的全期去重UV重算。

所有率用DAX分子/分母相除，不平均各组转化率。跨行为总计和跨留存偏移的无意义率返回BLANK。Products仅展示固定样本和候选，Scope保留全量商品规模。

## 内容

六页：经营总览、转化诊断、时段运营、用户运营、留存复购、商品机会。包含原生图表、指标卡、表格和切片器；measures.dax可直接阅读。theme同时保存在报表资源内。

作品集中的PNG为同数据生成的设计预览，非Power BI Desktop真实截图。JSON Schema验证、字段绑定与数据核对不能代替Desktop引擎验收。

官方参考：
- https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview
- https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report
- https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset
- https://github.com/microsoft/json-schemas
