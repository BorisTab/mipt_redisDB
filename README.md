# Redis
Поднимем контейнер с базой:
``` yaml
version: '3.9'

services:
  redis:
    image: redis:6.2-alpine
    ports:
      - 6379:6379
    command: redis-server --save 60 1 --requirepass MDNcVb924a --loglevel warning
```  

Зайдем в контейнер и запустим `redis-cli`, авторизуемся и проверим работу:
``` 
127.0.0.1:6379> auth MDNcVb924a
OK
127.0.0.1:6379> ping
PONG
```

С помощью сайта https://json-generator.com/ сгенерируем большой json файл, который будем использовать для тестов.

Так как будем работать с большим объемом данных, то удобнее взаимодействовать с базой через python. `test.py` – скрипт, который добавляет json в базу в виде строки, hsert, zset и list и извлекает из базы эти же данные. Измеряет скорость каждой операции. Результат работы:
``` 
add string: 0.6134171485900879
add hset  : 0.6102712154388428
add zset  : 0.6649940013885498
add list  : 0.588385820388794 

get string: 0.5429692268371582
get hset  : 0.5182600021362305
get zset  : 0.46428608894348145
get list  : 0.4228858947753906
```

## Redis cluster
Теперь сделаем кластер one master two slaves. Нам понадобиться поднять контейнеры:
``` yaml
version: '3.9'
services:
  redis-master:
      image: 'redis:6.2-alpine'
      command: redis-server /usr/local/etc/redis/redis.conf
      ports:
        - '6370:6370'
      volumes:
        - ./redis_master.conf:/usr/local/etc/redis/redis.conf
      networks:
        app_subnet:
          ipv4_address: 172.20.0.31
  redis-slave-1:
      image: 'redis:6.2-alpine'
      command: redis-server /usr/local/etc/redis/redis.conf
      ports:
        - '6371:6371'
      volumes:
        - ./redis_slave_1.conf:/usr/local/etc/redis/redis.conf
      networks:
        app_subnet:
          ipv4_address: 172.20.0.32
  redis-slave-2:
      image: 'redis:6.2-alpine'
      command: redis-server /usr/local/etc/redis/redis.conf
      ports:
        - '6372:6372'
      volumes:
        - ./redis_slave_2.conf:/usr/local/etc/redis/redis.conf
      networks:
        app_subnet:
          ipv4_address: 172.20.0.33

networks:
  app_subnet:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/24
```

Конфигурация мастера:
```
port 6370
requirepass password
slave-read-only yes
appendonly yes
```

Конфигурации slave'ов:  
Первый:
```
port 6371
slaveof 172.20.0.31 6370
slave-read-only yes
appendonly yes
masterauth password
requirepass password
```
Второй:
```
port 6372
slaveof 172.20.0.31 6370
slave-read-only yes
appendonly yes
masterauth password
requirepass password
```

`port` – порт на котором поднята текущая нода  
`requirepass` – пароль требуемый для авторизации на ноде  
`slave-read-only` – slave'ы принимают запросы только на read, на мастере роли не играет  
`appendonly yes` – записывем все действия в журнал для восстановления при отказе  
`slaveof` – указываем хост и порт мастера  
`masterauth` – пароль для доступа к мастеру  

### Проверим, что кластер верно настроен
Зайдем на мастер ноду и выполним:
``` 
redis-cli -p 6370 -a password info replication
```
Вывод:
```
role:master
connected_slaves:2
slave0:ip=172.20.0.32,port=6371,state=online,offset=182,lag=0
slave1:ip=172.20.0.33,port=6372,state=online,offset=182,lag=1
master_failover_state:no-failover
master_replid:b75e33989409b694849d0fbfa5185fb4ad488b1d
master_replid2:0000000000000000000000000000000000000000
master_repl_offset:182
second_repl_offset:-1
repl_backlog_active:1
repl_backlog_size:1048576
repl_backlog_first_byte_offset:1
repl_backlog_histlen:182
```
Видим, что у текущего мастера два слейва, как и планироовали. Также можем проверить информацию на слейвах (аналогичной командой, только поставить соответсвующий порт):
```
role:slave
master_host:172.20.0.31
master_port:6370
master_link_status:up
master_last_io_seconds_ago:10
master_sync_in_progress:0
slave_read_repl_offset:308
slave_repl_offset:308
slave_priority:100
slave_read_only:1
replica_announced:1
connected_slaves:0
master_failover_state:no-failover
master_replid:b75e33989409b694849d0fbfa5185fb4ad488b1d
master_replid2:0000000000000000000000000000000000000000
master_repl_offset:308
second_repl_offset:-1
repl_backlog_active:1
repl_backlog_size:1048576
repl_backlog_first_byte_offset:1
repl_backlog_histlen:308
```

### Проверка
Запустим наш скрипт на кластере:
```
add string: 0.6852641105651855
add hset  : 0.820723295211792
add zset  : 0.8010580539703369
add list  : 1.251603364944458 

get string: 0.9233100414276123
get hset  : 0.7934479713439941
get zset  : 0.4673421382904053
get list  : 0.4844949245452881
```

Видим, что на кластере время работы запросов возросло, но увеличилась и надежность системы
