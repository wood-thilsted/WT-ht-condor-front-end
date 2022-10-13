
ARG IMAGE_BASE_TAG=release

FROM opensciencegrid/software-base:3.6-el7-$IMAGE_BASE_TAG

LABEL maintainer OSG Software <support@opensciencegrid.org>

RUN \
    yum update -y && \
    (yum install -y git-core || yum install -y git) && \
    yum install -y --enablerepo=osg-upcoming condor && \
    yum install -y python3-pip httpd mod_auth_openidc mod_ssl python3-mod_wsgi && \
    yum clean all && rm -rf /var/cache/yum/*

RUN \
    pushd /tmp && \
    git clone https://github.com/opensciencegrid/osg-ca-generator.git && \
    pushd osg-ca-generator && \
    make install && \
    osg-ca-generator --host && \
    popd && \
    popd

COPY run_local.sh requirements.txt /opt/portal/
RUN pip3 install -U pip && pip3 install -r /opt/portal/requirements.txt

COPY portal  /opt/portal/

COPY register.py /usr/bin
COPY supervisor-apache.conf /etc/supervisord.d/40-apache.conf
COPY examples/apache.conf /etc/httpd/conf.d/

ENV CONFIG_DIR=/srv
#ENTRYPOINT ["/opt/portal/run_local.sh"]
#CMD ["--host=0.0.0.0"]
