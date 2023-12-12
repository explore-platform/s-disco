
cd /sdisco
bash -c "source /venv/sdisco_env/bin/activate sdisco_env && bokeh serve /sdisco/sda.py --use-xheaders\
    --address=0.0.0.0 --allow-websocket-origin=* \
    --log-level=info --prefix=${PATH_PREFIX} --port=5006 &"


