FROM node:20 as frontend
# This is to avoid the ERR_OSSL_EVP_UNSUPPORTED error from webpack.
# Can be removed when we upgrade webpack or move to another tool.
ENV NODE_OPTIONS=--openssl-legacy-provider

WORKDIR /src/js

# Move the necessary files into the image.
COPY yarn.lock .yarnrc.yml package.json vue.config.js babel.config.js .eslintrc.js .babelrc ./
COPY .yarn .yarn
COPY static static
COPY vue vue
RUN yarn

# Build for production. Result is stored in static/dist.
RUN yarn build-prod

FROM python:3.7-slim

RUN apt-get -y update && \
    apt-get install -y gcc libpcre3 libpcre3-dev zlib1g zlib1g-dev libssl-dev curl ca-certificates gnupg libgeos-dev

# Prepare directory for the app.
WORKDIR /usr/src/app

# Python dependencies.
COPY requirements.txt /usr/src/app/
RUN pip install -r requirements.txt

# Add everything in the image.
COPY . /usr/src/app

# Overwrite the built frontend with the one from the frontend image.
COPY --from=frontend /src/js/static/dist static/dist

# Install the TNO package.
RUN pip install -e src/
ENV PYTHONPATH=.:/usr/src/app

EXPOSE 8111

CMD python app.py
