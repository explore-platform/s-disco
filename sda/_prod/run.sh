printf "\
=======================================================\n\n\
[PROD] SDA DEMONSTRATOR STARTUP\n\n\
=======================================================\n\n"

# service mongod start
# systemctl start mongod
envsubst '${PATH_PREFIX}' < /nginx/default.conf.template > /etc/nginx/conf.d/default.conf

service nginx start

/usr/bin/mongod --config /etc/mongod.conf & 
sleep 2

bash /sdisco/entrypoint.sh &
bash /visualizer/entrypoint.sh &

tail -f /dev/null


