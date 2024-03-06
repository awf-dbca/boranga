# Prepare the base environment.
FROM ubuntu:22.04 as builder_base_boranga
MAINTAINER asi@dbca.wa.gov.au
ENV DEBIAN_FRONTEND=noninteractive
ENV DEBUG=True
ENV TZ=Australia/Perth
ENV PRODUCTION_EMAIL=True
ENV SECRET_KEY="ThisisNotRealKey"
ENV SITE_PREFIX='qml-dev'
ENV SITE_DOMAIN='dbca.wa.gov.au'
ENV OSCAR_SHOP_NAME='Parks & Wildlife'
ENV BPAY_ALLOWED=False

# Use Australian Mirrors
RUN sed 's/archive.ubuntu.com/au.archive.ubuntu.com/g' /etc/apt/sources.list > /etc/apt/sourcesau.list
RUN mv /etc/apt/sourcesau.list /etc/apt/sources.list
# Use Australian Mirrors

RUN apt-get clean
RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install --no-install-recommends -y curl wget git libmagic-dev gcc binutils libproj-dev gdal-bin python3 python3-setuptools python3-dev python3-pip tzdata libreoffice cron 
RUN apt-get install --no-install-recommends -y libpq-dev patch
RUN apt-get install --no-install-recommends -y postgresql-client mtr systemd
RUN apt-get install --no-install-recommends -y sqlite3 vim postgresql-client ssh htop
RUN apt-get install --no-install-recommends -y rsyslog
RUN apt-get install --no-install-recommends -y bzip2
RUN apt-get install --no-install-recommends -y graphviz libgraphviz-dev pkg-config

# Install nodejs
RUN update-ca-certificates
# install node 16
RUN touch install_node.sh
RUN curl -fsSL https://deb.nodesource.com/setup_16.x -o install_node.sh
RUN chmod +x install_node.sh && ./install_node.sh
RUN apt-get install -y nodejs
# Install nodejs

RUN ln -s /usr/bin/python3 /usr/bin/python 
#RUN ln -s /usr/bin/pip3 /usr/bin/pip
RUN pip install --upgrade pip
RUN wget -O /tmp/GDAL-3.8.3-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl https://github.com/girder/large_image_wheels/raw/wheelhouse/GDAL-3.8.3-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl#sha256=e2fe6cfbab02d535bc52c77cdbe1e860304347f16d30a4708dc342a231412c57
RUN pip install /tmp/GDAL-3.8.3-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
# Install Python libs from requirements.txt.
FROM builder_base_boranga as python_libs_boranga
WORKDIR /app
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt \
  # Update the Django <1.11 bug in django/contrib/gis/geos/libgeos.py
  # Reference: https://stackoverflow.com/questions/18643998/geodjango-geosexception-error
  #&& sed -i -e "s/ver = geos_version().decode()/ver = geos_version().decode().split(' ')[0]/" /usr/local/lib/python3.6/dist-packages/django/contrib/gis/geos/libgeos.py \
  && rm -rf /var/lib/{apt,dpkg,cache,log}/ /tmp/* /var/tmp/*

# Install the project (ensure that frontend projects have been built prior to this step).
FROM python_libs_boranga
COPY timezone /etc/timezone
ENV TZ=Australia/Perth
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

#COPY libgeos.py.patch /app/
#RUN patch /usr/local/lib/python3.8/dist-packages/django/contrib/gis/geos/libgeos.py /app/libgeos.py.patch
#RUN rm /app/libgeos.py.patch
 
COPY cron /etc/cron.d/dockercron
COPY startup.sh /
#RUN service rsyslog start
RUN chmod 0644 /etc/cron.d/dockercron
RUN crontab /etc/cron.d/dockercron
RUN touch /var/log/cron.log
RUN service cron start
RUN chmod 755 /startup.sh
COPY gunicorn.ini manage.py ./
RUN touch /app/.env
COPY .git ./.git
COPY boranga ./boranga
#RUN mkdir /app/boranga/cache/
#RUN chmod 777 /app/boranga/cache/
RUN cd /app/boranga/frontend/boranga; npm install
RUN cd /app/boranga/frontend/boranga; npm run build
RUN python manage.py collectstatic --noinput
RUN apt-get install --no-install-recommends -y python3-pil
EXPOSE 8080
HEALTHCHECK --interval=1m --timeout=5s --start-period=10s --retries=3 CMD ["wget", "-q", "-O", "-", "http://localhost:8080/"]
CMD ["/startup.sh"]
#CMD ["gunicorn", "parkstay.wsgi", "--bind", ":8080", "--config", "gunicorn.ini"]

LABEL org.opencontainers.image.source="https://github.com/dbca-wa/boranga"

#patch /home/container/.local/lib/python3.10/site-packages/reversion/migrations/0001_squashed_0004_auto_20160611_1202.py 0001_squashed_0004_auto_20160611_1202.patch