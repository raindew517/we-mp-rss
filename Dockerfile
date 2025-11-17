
FROM  ghcr.io/rachelos/base-mini:latest as werss-base
#

ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
# ENV PIP_INDEX_URL=https://mirrors.huaweicloud.com/repository/pypi/simple

# 复制Python依赖文件
COPY requirements.txt .
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt 
RUN playwright install firefox --with-deps

FROM werss-base
# 安装系统依赖
WORKDIR /app
# 复制后端代码
COPY ./config.example.yaml  ./config.yaml
COPY . .
RUN chmod +x ./start.sh
# 暴露端口
EXPOSE 8001
CMD ["./start.sh"]