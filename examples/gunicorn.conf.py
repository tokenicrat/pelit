import multiprocessing

bind = "0.0.0.0:8000"
backlog = 2048

workers: int = multiprocessing.cpu_count() * 2 + 1
worker_class: str = "sync"
worker_connections: int = 1000
timeout: int = 30
keepalive: int = 2

max_requests: int = 1000
max_requests_jitter: int = 500

loglevel = 'warn'

proc_name = 'pelit_gunicorn'
pidfile = '/tmp/pelit.pid'
tmp_upload_dir = '/tmp'

limit_request_line: int = 4094
limit_request_fields: int = 100
limit_request_field_size: int = 8190

preload_app: bool = True
worker_tmp_dir: str = "/dev/shm"

graceful_timeout: int = 30
