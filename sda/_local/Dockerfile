FROM ubuntu:20.04

# ==============================================
# COMMON INSTALLS
# ==============================================
RUN apt update
RUN apt install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update
RUN apt update
RUN apt install -y python3.8 python3.8-venv  python-is-python3 python3-pip nginx curl wget \
    python3-distutils python3-apt git python3-wheel python3-dev
RUN python --version
RUN python -m pip --version
RUN apt-get install -y gettext

# TEMP
# ==============================================
# VISUALISER
# ==============================================
RUN wget -qO - https://www.mongodb.org/static/pgp/server-5.0.asc | apt-key add -
RUN echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/5.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-5.0.list
RUN apt-get update
RUN apt-get install -y mongodb-org

# Use NodeJS 16.x - Ubuntu default is 12.x
RUN curl -sL https://deb.nodesource.com/setup_16.x | bash -
RUN apt-get install -y nodejs gnupg

# Install PhantomJS prebuilt - required when building visualizer (module dependency)
RUN npm install phantomjs-prebuilt -g

# Install ArangoDB for visualizer annotations
RUN echo 'deb https://download.arangodb.com/arangodb34/DEBIAN/ /' | tee /etc/apt/sources.list.d/arangodb.list
RUN wget -q https://download.arangodb.com/arangodb34/DEBIAN/Release.key -O- | apt-key add -
RUN apt update
RUN apt -y install apt-transport-https
RUN echo arangodb3 arangodb3/password password root | debconf-set-selections
RUN echo arangodb3 arangodb3/password_again password root | debconf-set-selections
RUN echo arangodb3 arangodb3/upgrade boolean true | debconf-set-selections
RUN echo arangodb3 arangodb3/storage_engine	select auto | debconf-set-selections
RUN echo arangodb3 arangodb3/backup	boolean false | debconf-set-selections
RUN apt -y install arangodb3

RUN git config --global http.sslVerify false
RUN git clone -b visualizer_v3_explore_dev_guidanceUI https://gitlab-ci-token:glpat-r_RJRyskgStudyhrhaUB@gitlab.know-center.tugraz.at/visualizer/visualizer.git /visualizer

RUN echo npm -v

#RUN chmod +x  /visualizer/startApplications.sh
# install node packages
WORKDIR /visualizer/
RUN npm install
RUN npm run build

COPY ./visualizer/_local/entrypoint.sh /visualizer/entrypoint.sh

# ==============================================
# DISCO
# ==============================================
RUN python -m venv /venv/sdisco_env
COPY  ./sdisco/requirements.txt  /sdisco/requirements.txt
RUN /venv/sdisco_env/bin/pip install -r /sdisco/requirements.txt

# ==============================================
# COPY ALL FILES
# ==============================================
COPY ./sdisco /sdisco

# ==============================================
# NGINX
# ==============================================
COPY ./_local/nginx.conf /etc/nginx/nginx.conf
COPY ./_local/default.conf.template /nginx/default.conf.template
# /etc/nginx/conf.d/default.conf
# COPY ./_prod/default.conf /etc/nginx/conf.d/default.conf

# # ==============================================
# # BUILD SCRIPTS
# # ==============================================
# RUN bash sdisco/build.sh


# ==============================================
# ENTRYPOINTS
# ==============================================
COPY ./_local/run.sh ./run.sh
ENTRYPOINT bash ./run.sh
