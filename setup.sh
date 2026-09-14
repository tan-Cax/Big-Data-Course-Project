#!/bin/bash
# =============================================================================
# NCS 充电桩数据分析平台 - 环境一键安装脚本
# 适用于: Ubuntu 22.04 | Python 3.12 | Hadoop 3.2.1 | Spark | MySQL
# =============================================================================
set -e

export CI=true DEBIAN_FRONTEND=noninteractive
PW='123456'

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
step() { echo -e "\n${CYAN}========== $1 ==========${NC}"; }

HADOOP_HOME=/opt/hadoop
SPARK_HOME=/opt/spark
JAVA_HOME=/opt/jdk8
PYTHON=python3.12
DATA_DIR=/home/bit/data/04.数据集最终版
PROJECT_DIR=/home/bit/data

# =============================================================================
# 1. 系统依赖 + 修复 Python 3.12 pip
# =============================================================================
step "Step 1/7: 安装系统依赖 & 修复 Python pip"

echo "$PW" | sudo -S apt-get update -qq
echo "$PW" | sudo -S apt-get install -y -qq \
    python3.12 python3.12-venv python3.12-dev \
    build-essential wget curl net-tools \
    > /dev/null 2>&1

$PYTHON -m ensurepip --upgrade 2>/dev/null || true
$PYTHON -m pip install --break-system-packages --upgrade pip setuptools wheel 2>&1 | tail -1

log "系统依赖安装完成: $($PYTHON --version 2>&1)"

# =============================================================================
# 2. 安装 MySQL
# =============================================================================
step "Step 2/7: 安装 MySQL"

if command -v mysql &>/dev/null; then
    log "MySQL 已安装"
else
    echo "$PW" | sudo -S bash -c \
        'echo "mysql-server mysql-server/root_password password root123" | debconf-set-selections;
         echo "mysql-server mysql-server/root_password_again password root123" | debconf-set-selections;
         apt-get install -y -qq mysql-server mysql-client' > /dev/null 2>&1
    log "MySQL 安装完成"
fi

echo "$PW" | sudo -S systemctl start mysql 2>/dev/null || \
echo "$PW" | sudo -S service mysql start 2>/dev/null || true
sleep 3

echo "$PW" | sudo -S mysql -u root -proot123 -e "CREATE DATABASE IF NOT EXISTS ncs_dashboard DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null

echo "$PW" | sudo -S mysql -u root -proot123 ncs_dashboard < "$PROJECT_DIR/backend/init_db.sql" 2>/dev/null

log "数据库 ncs_dashboard + 11 张分析表创建完成"

# =============================================================================
# 3. 安装 Python 依赖
# =============================================================================
step "Step 3/7: 安装 Python 依赖"

$PYTHON -m pip install --break-system-packages -i https://pypi.tuna.tsinghua.edu.cn/simple \
    flask flask-cors pymysql pandas 2>&1 | tail -3

if $PYTHON -c "import pyspark" 2>/dev/null; then
    log "PySpark 已可用"
else
    $PYTHON -m pip install --break-system-packages -i https://pypi.tuna.tsinghua.edu.cn/simple pyspark 2>&1 | tail -3
fi

$PYTHON -c "import flask, pymysql, pyspark; print('flask:', flask.__version__, '| pyspark:', pyspark.__version__)"
log "Python 依赖安装完成"

# =============================================================================
# 4. 配置环境变量
# =============================================================================
step "Step 4/7: 配置环境变量"

export JAVA_HOME=/opt/jdk8
export HADOOP_HOME=/opt/hadoop
export SPARK_HOME=/opt/spark
export PATH=$JAVA_HOME/bin:$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$SPARK_HOME/bin:$PATH

cat > /tmp/ncs_env.sh << 'ENVEOF'
export JAVA_HOME=/opt/jdk8
export HADOOP_HOME=/opt/hadoop
export SPARK_HOME=/opt/spark
export PATH=$JAVA_HOME/bin:$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$SPARK_HOME/bin:$PATH
ENVEOF

if ! grep -q "ncs_env.sh" ~/.bashrc 2>/dev/null; then
    echo "source /tmp/ncs_env.sh" >> ~/.bashrc
fi

log "环境变量配置完成"

# =============================================================================
# 5. 启动 HDFS 并上传数据
# =============================================================================
step "Step 5/7: 启动 HDFS 并上传数据"

export JAVA_HOME=/opt/jdk8

$HADOOP_HOME/bin/hdfs namenode -format 2>/dev/null || true

$HADOOP_HOME/sbin/start-dfs.sh 2>/dev/null || true
sleep 5

if $HADOOP_HOME/bin/hdfs dfsadmin -report &>/dev/null; then
    log "HDFS 启动成功"
    $HADOOP_HOME/bin/hdfs dfs -mkdir -p /ncs/data 2>/dev/null || true
    $HADOOP_HOME/bin/hdfs dfs -put -f "$DATA_DIR/dsv13r2.csv" /ncs/data/ 2>/dev/null || true
    $HADOOP_HOME/bin/hdfs dfs -put -f "$DATA_DIR/nvv2t.csv" /ncs/data/ 2>/dev/null || true
    $HADOOP_HOME/bin/hdfs dfs -put -f "$DATA_DIR/nvv2t_md_end.csv" /ncs/data/ 2>/dev/null || true
    log "数据上传到 HDFS /ncs/data/"
    $HADOOP_HOME/bin/hdfs dfs -ls /ncs/data/
else
    warn "HDFS 启动失败，后续使用本地文件模式"
fi

# =============================================================================
# 6. 创建后端目录
# =============================================================================
step "Step 6/7: 创建后端项目结构"

mkdir -p "$PROJECT_DIR/backend/spark_jobs"
log "后端目录: $PROJECT_DIR/backend/"

# =============================================================================
# 7. 前端环境
# =============================================================================
step "Step 7/7: 检查前端环境"

if [ -d "$PROJECT_DIR/web/node_modules" ]; then
    log "前端 node_modules 已存在"
else
    cd "$PROJECT_DIR/web" && npm install 2>/dev/null
    log "前端依赖安装完成"
fi

# =============================================================================
# 汇总
# =============================================================================
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  环境安装完成!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "  Python:     $($PYTHON --version 2>&1)"
echo -e "  MySQL:      $(echo "$PW" | sudo -S mysql --version 2>&1 | head -1)"
echo -e "  Hadoop:     $(hadoop version 2>&1 | head -1)"
echo -e "  Spark:      已安装 at $SPARK_HOME"
echo -e "  Node.js:    $(node --version)"
echo ""
echo -e "  ${CYAN}数据库:${NC}   ncs_dashboard (root / root123)"
echo -e "  ${CYAN}HDFS 数据:${NC} /ncs/data/"
echo -e "  ${CYAN}后端目录:${NC} $PROJECT_DIR/backend/"
echo ""
echo -e "  ${YELLOW}下一步:${NC}"
echo "    1. PySpark 分析: $PROJECT_DIR/backend/spark_jobs/"
echo "    2. Flask API:    $PROJECT_DIR/backend/app.py"
echo "    3. 前端大屏:     $PROJECT_DIR/web/src/"
echo ""
