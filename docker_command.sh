#!/bin/bash
echo "Starting postgres"
service postgresql start

echo "Starting zookeeper"
service zookeeper start

echo "Sleeping for 10 seconds"
sleep 2

echo "Starting kafka"
nohup ~/kafka/bin/kafka-server-start.sh ~/kafka/config/server.properties > ~/kafka/kafka.log 2>&1 &

echo "Sleeping for 2 seconds"
sleep 2
cat ~/kafka/kafka.log

echo "Starting redis"
redis-server /etc/redis/redis.conf

echo "Starting elasticsearch"
su - elasticsearch -c '/elasticsearch/bin/elasticsearch -d'

echo "Sleeping for 10 seconds"
sleep 10

echo "Activate virtual env"
cd ./GraphSpace && source venv/bin/activate 

echo "Migrate"
#python manage.py collectstatic --noinput --settings=graphspace.settings.local
python manage.py migrate --settings=graphspace.settings.local


echo "Start GraphSpace ... "
python manage.py runserver 0.0.0.0:8000 --settings=graphspace.settings.local

