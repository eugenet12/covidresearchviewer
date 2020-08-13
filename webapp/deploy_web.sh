# kill current webserver and deploy new one
cd /home/ubuntu/capstone_corona_search/webapp
kill $(ps aux | grep '[r]eact-scripts' | awk '{print $2}')
kill $(ps aux | grep '[a]pi.py' | awk '{print $2}')
rm flask.logs
rm react.logs
nohup yarn start-api > flask.logs &
nohup yarn start > react.logs &
