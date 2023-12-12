printf "
================================================
BOOT: Visualiser
================================================"
cd /visualizer

/usr/bin/mongod --config /etc/mongod.conf &
arangod --server.endpoint tcp://0.0.0.0:8529 &
sleep 5

npm run start