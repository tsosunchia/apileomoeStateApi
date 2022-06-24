import json
import logging

import psutil
import pymysql

key = json.load(open('priv/key.json'))
threshold = json.load(open('priv/threshold.json'))
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# 查询今日新增用户
sqlUser = "select count(*) from users where date_format(create_time,'%Y-%m-%d') = date_format(now(),'%Y-%m-%d')"
# 查询过去1小时cache表增加行数
sqlRow = "select count(*) from cache where updatetime > (now() - interval 1 hour)"
query_list = ['cpu', 'mem', 'user', 'row', 'all']


def queryDB(sqls: list) -> list:
    db = pymysql.connect(host=key['host'], user=key['user'], passwd=key['passwd'], db=key['db'], port=key['port'],
                         charset='utf8')
    cursor = db.cursor()
    res = []
    try:
        for sql in sqls:
            logging.debug(f"sql:{sql}")
            cursor.execute(sql)
            res.append(cursor.fetchall()[0])
            logging.debug(f"res:{res}")
    except pymysql.err.ProgrammingError as errMsg:
        print(errMsg)
        res = []
    db.close()
    return res


def backendIf(cpu: bool = False, mem: bool = False, user: bool = False, row: bool = False) -> tuple:
    cpu_occupancy_rate = psutil.cpu_percent() if cpu else None
    mem_occupancy_rate = psutil.virtual_memory().percent if mem else None
    if user and row:
        _ = queryDB([sqlUser, sqlRow])
        user_count = _[0][0]
        row_count = _[1][0]
    else:
        user_count = queryDB([sqlUser])[0][0] if user else None
        row_count = queryDB([sqlRow])[0][0] if row else None
    return cpu_occupancy_rate, mem_occupancy_rate, user_count, row_count


def monitor() -> tuple:
    cpu_occupancy_rate, mem_occupancy_rate, user_count, row_count = backendIf(cpu=True, mem=True, user=True, row=True)
    msg = ""
    c = cpu_occupancy_rate > threshold['cpu']
    if c:
        msg += f"cpu占用率:{cpu_occupancy_rate}%超过阈值{threshold['cpu']}%\n"
    m = mem_occupancy_rate > threshold['mem']
    if m:
        msg += f"内存占用率:{mem_occupancy_rate}%超过阈值{threshold['mem']}%\n"
    u = user_count > threshold['user']
    if u:
        msg += f"今日新增用户数:{user_count}超过阈值{threshold['user']}\n"
    r = row_count > threshold['row']
    if r:
        msg += f"最近一小时请求次数:{row_count}超过阈值{threshold['row']}\n"
    if c or m or u or r:
        msg += f"cpu:{cpu_occupancy_rate} mem:{mem_occupancy_rate} user:{user_count} row:{row_count}"
        logging.warning(f"超出阈值,cpu:{cpu_occupancy_rate} mem:{mem_occupancy_rate} user:{user_count} row:{row_count}")
        return True, msg
    return False, msg
