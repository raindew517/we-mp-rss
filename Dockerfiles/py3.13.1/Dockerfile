FROM ghcr.io/rachelos/base:latest
ENV PIP_INDEX_URL=https://mirrors.huaweicloud.com/repository/pypi/simple
RUN apt update && apt install -y fonts-noto-cjk libreoffice\
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN ls
COPY  requirements.txt .
RUN pip3 install -r requirements.txt -i https://mirrors.huaweicloud.com/repository/pypi/simple

