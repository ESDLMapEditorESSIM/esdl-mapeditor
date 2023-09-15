FROM python:3.10-slim

# Install external dependencies.
RUN apt-get -y update && \
    apt-get install -y gcc libpcre3 libpcre3-dev zlib1g zlib1g-dev libssl-dev curl ca-certificates gnupg libgeos-dev

# Install Node.js and Yarn
ENV NODE_MAJOR=20
# We need to do this to prevent the build error ERR_OSSL_EVP_UNSUPPORTED. This is likely related to webpack. If we
# migrate to another build tool, this might not be necessary anymore.
ENV NODE_OPTIONS=--openssl-legacy-provider
RUN mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && apt-get install -y nodejs

# Install yarn.
RUN corepack enable
RUN yarn set version berry

# Prepare directory for the app.
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# Build frontend dependencies.
COPY yarn.lock package.json vue.config.js babel.config.js /usr/src/app/
RUN echo "nodeLinker: node-modules" > .yarnrc.yml
RUN yarn

# Python dependencies.
COPY requirements.txt /usr/src/app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Add everything in the image.
COPY . /usr/src/app
RUN ls
RUN yarn build-prod
ENV PYTHONPATH=.:/usr/src/ap

# Clean up.
RUN rm -rf node_modules

EXPOSE 8111

CMD cd /usr/src/app && uwsgi docker/uwsgi-long-polling.ini
