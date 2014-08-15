web: gunicorn dareyoo.wsgi
worker: celery -A dareyoo worker -Q celery -B -l info -n default
waserver: env WA_INIT_CLIENTS=1 celery -A dareyoo worker -Q wamsg -l info -P eventlet -c 16 -n wa