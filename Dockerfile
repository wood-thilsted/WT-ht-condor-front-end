
ARG BASE_OSG_SERIES=23
ARG BASE_OS=el9
ARG BASE_YUM_REPO=release

FROM opensciencegrid/software-base:$BASE_OSG_SERIES-$BASE_OS-$BASE_YUM_REPO

LABEL maintainer OSG Software <help@osg-htc.org>

RUN \
    yum update -y && \
    yum install -y condor && \
    yum install -y python3-pip httpd mod_auth_openidc mod_ssl python3-mod_wsgi && \
    yum clean all && rm -rf /var/cache/yum/*

COPY portal run_local.sh requirements.txt /opt/portal/
RUN pip3 install -U pip && pip3 install -r /opt/portal/requirements.txt

COPY register.py /usr/bin
COPY supervisor-apache.conf /etc/supervisord.d/40-apache.conf
COPY examples/apache.conf /etc/httpd/conf.d/
COPY wsgi.py portal /srv/
COPY portal /srv/portal/
COPY documentation /srv/documentation/

ENV PYTHONUNBUFFERED=1
ENV CONFIG_PATH=/srv/config.py
#ENTRYPOINT ["/opt/portal/run_local.sh"]
#CMD ["--host=0.0.0.0"]
