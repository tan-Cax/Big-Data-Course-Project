# NCS 充电桩数据分析平台

基于 PySpark + Flask + Vue3 的充电桩数据清洗、分析与可视化大屏项目。

## 技术栈

| 组件 | 版本 |
|------|------|
| Python | 3.12 |
| PySpark | 3.5.9 |
| Hadoop | 3.2.1 |
| Flask | 3.x |
| MySQL | 8.0 |
| Node.js | 24+ |
| Vue | 3.x |
| ECharts | 5.x |

## 项目结构

```
├── backend/                  # 后端
│   ├── config.py            # 数据库连接配置
│   ├── db.py                # 数据库查询封装
│   ├── app.py               # Flask API 入口（13个路由）
│   ├── init_db.sql          # MySQL 建表脚本（12张ADS表）
│   ├── requirements.txt     # Python 依赖
│   └── spark_jobs/
│       └── run_analysis.py  # PySpark 数据清洗与分析
├── web/                      # 前端
│   └── src/
│       ├── App.vue           # 根组件（标题栏+数据轮询）
│       ├── views/
│       │   └── DashboardView.vue  # 大屏布局
│       ├── composables/
│       │   └── useApi.js     # HTTP 请求封装（替代原 WebSocket）
│       ├── components/       # 11个图表组件
│       └── assets/styles.css # 深色科技风主题
├── 04.数据集最终版/           # 原始数据（不修改）
├── setup.sh                  # 环境一键安装脚本
└── 01_ods_create.hql        # Hive ODS 层建表脚本
```

## 各部分功能

### 数据来源

3个CSV文件，描述郑州市电动汽车充电桩运营数据：

| 文件 | 内容 | 记录数 |
|------|------|--------|
| `dsv13r2.csv` | 充电过程实时监测数据（SOC、电压、电流、温度等快照） | 1,594 |
| `nvv2t.csv` | 充电订单交易数据（充电量、费用、时段、用户、站点等） | 3,395 |
| `nvv2t_md_end.csv` | 充电站/充电桩元数据（站名、地址、设备数等） | 105 |

### PySpark 数据清洗（run_analysis.py）

对原始CSV进行内存级清洗，不修改原文件：

- 去除UTF-8 BOM头
- 去除Windows CRLF换行符
- 修正异常年份（`0014` → `2014`）
- 丢弃无效的 `record_time` 字段
- 字符串字段类型转换为数值类型
- 映射设施类型编码为中文名称

### 12个分析维度

| # | 维度 | 图表类型 | MySQL表 |
|---|------|---------|---------|
| 1 | 总览指标 | 数字卡片 | ads_overview |
| 2 | 每日趋势 | 面积折线图 | ads_daily_trend |
| 3 | 站点排名 | 横向柱状图 | ads_station_analysis |
| 4 | 时段分布 | 柱状图+折线图 | ads_hourly_distribution |
| 5 | 星期分布 | 分组柱状图 | ads_weekday_distribution |
| 6 | 设施类型 | 环形图 | ads_facility_analysis |
| 7 | 用户行为 | 气泡图 | ads_user_behavior |
| 8 | 平台分布 | 环形图 | ads_platform_analysis |
| 9 | 充电效率 | 雷达图 | ads_efficiency_analysis |
| 10 | 站点利用率 | 横向柱状图 | ads_station_utilization |
| 11 | 时段×站点 | 热力图 | ads_hourly_station_cross |
| 12 | 星期×设施 | 堆叠柱状图 | ads_weekday_facility_cross |

### Flask API（app.py）

提供13个REST接口，一图一接口：

```
GET  /api/overview                     总览指标
GET  /api/trend/daily                  每日趋势
GET  /api/station/ranking              站点排名
GET  /api/station/utilization          站点利用率
GET  /api/distribution/hourly          时段分布
GET  /api/distribution/weekday         星期分布
GET  /api/facility/type                设施类型
GET  /api/user/behavior                用户行为
GET  /api/platform/distribution        平台分布
GET  /api/efficiency/radar             充电效率
GET  /api/comparison/hourly-station    时段×站点交叉
GET  /api/comparison/weekday-facility  星期×设施交叉
POST /api/reload                       触发重新分析
```

### Vue3 前端大屏

深色科技风格，Grid布局，10秒自动轮询刷新。

## 快速启动

```bash
# 1. 安装环境（首次运行）
bash setup.sh

# 2. 启动 Flask 后端
cd backend && python3.12 app.py &

# 3. 启动前端开发服务器
cd web && npx vite --host 0.0.0.0 --port 3000

# 4. 浏览器访问
# http://localhost:3000
```

## 重新分析数据

```bash
curl -X POST http://127.0.0.1:5000/api/reload
```

或手动运行：

```bash
cd backend
export PYTHONPATH=$SPARK_HOME/python:$SPARK_HOME/python/lib/py4j-0.10.9.7-src.zip
python3.12 spark_jobs/run_analysis.py
```
