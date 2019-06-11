#! bin/sh

source venv/bin/activate
exec hypercorn -b 0.0.0.0:8080 app/app:app