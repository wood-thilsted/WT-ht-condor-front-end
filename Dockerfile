
FROM python:3.7

COPY register.py /usr/bin
COPY registry run_local.sh requirements.txt /opt/registry/

RUN pip install -r /opt/registry/requirements.txt

ENV CONFIG_DIR=/srv
ENTRYPOINT ["/opt/registry/run_local.sh"]
CMD ["--host=0.0.0.0"]
