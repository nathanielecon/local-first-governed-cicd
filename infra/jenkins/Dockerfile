FROM jenkins/jenkins:2.516.1-lts-jdk21
USER root
RUN apt-get update \
    && apt-get install --no-install-recommends -y ca-certificates curl docker.io jq make python3 python3-venv \
    && rm -rf /var/lib/apt/lists/*
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt
COPY casc.yaml /usr/share/jenkins/ref/casc.yaml
RUN ln -s /usr/share/jenkins/ref/casc.yaml /usr/share/jenkins/ref/casc.yaml.override || true
USER jenkins

