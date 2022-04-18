import redis
import time
import json

with open('./data/string.json') as f:
    string_json = f.read()

db = redis.StrictRedis(
    host='localhost',
    port=6370,
    password='password'
)

# string
start = time.time()
db.set('json_string', string_json)
end = time.time()

print("add string:", end - start)

# hset
start = time.time()
db.hset('json_hset', '1', string_json)
end = time.time()

print("add hset  :", end - start)

# zset 
zset_data = json.loads(string_json)
zset_data_str = {}
for i, item in enumerate(zset_data):
    zset_data_str[json.dumps(item)] = i

start = time.time()
zset_count = db.zadd('json_zset', zset_data_str)
end = time.time()

print("add zset  :", end - start)

# list
list_data = json.loads(string_json)
list_data_str = []
for item in list_data:
    list_data_str.append(json.dumps(item))

start = time.time()
list_count = db.lpush('json_list', *list_data_str)
end = time.time()

print("add list  :", end - start, '\n')


# read string
start = time.time()
read_json_string = db.get('json_string')
end = time.time()

print("get string:", end - start)

# read hset
start = time.time()
read_json_hset = db.hget('json_hset', '1')
end = time.time()

print("get hset  :", end - start)

# read zset
start = time.time()
read_json_zset = db.zrange('json_zset', 0, zset_count)
end = time.time()

print("get zset  :", end - start)

# read list
start = time.time()
read_json_list = db.lrange('json_list', 0, list_count)
end = time.time()

print("get list  :", end - start)

db.flushall()
