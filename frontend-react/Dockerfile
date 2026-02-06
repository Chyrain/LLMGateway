# 构建阶段
FROM node:20-alpine as build

WORKDIR /app

# 复制 package 文件
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制源代码
COPY . .

# 构建（带版本号）
ARG BUILD_TIMESTAMP
ENV VITE_BUILD_TIME=$BUILD_TIMESTAMP
RUN echo "Build timestamp: $BUILD_TIMESTAMP" && \
    sed -i "s/%%BUILD_TIMESTAMP%%/$BUILD_TIMESTAMP/g" index.html && \
    npm run build

# 生产阶段
FROM nginx:alpine

# 复制构建产物
COPY --from=build /app/dist /usr/share/nginx/html

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
