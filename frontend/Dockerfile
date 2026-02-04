# Frontend Dockerfile
# Build stage
FROM node:20-alpine as build

WORKDIR /app

COPY package*.json ./

# Fix npm network issues
RUN npm config set registry https://registry.npmmirror.com && \
    npm install

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
