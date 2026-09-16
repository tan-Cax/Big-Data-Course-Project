import os

MYSQL_CONFIG = {
    'host': os.environ.get('NCS_DB_HOST', '127.0.0.1'),
    'port': int(os.environ.get('NCS_DB_PORT', 3306)),
    'user': os.environ.get('NCS_DB_USER', 'root'),
    'password': os.environ.get('NCS_DB_PASS', 'root123'),
    'database': os.environ.get('NCS_DB_NAME', 'ncs_dashboard'),
    'charset': 'utf8mb4',
}

DATA_SOURCE = os.environ.get('NCS_DATA_SOURCE', 'local')

HDFS_PATH = os.environ.get('NCS_HDFS_PATH', 'hdfs://localhost:9000/ncs/data')
LOCAL_PATH = '/home/bit/data/04.数据集最终版'

SPARK_APP_HOME = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'spark_jobs')
