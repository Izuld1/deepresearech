FROM node:20-alpine

WORKDIR /app

# 1. 拷贝依赖声明
COPY package.json package-lock.json* ./

# 2. 安装依赖
RUN npm install

# 3. 拷贝源代码
COPY . .

# 4. Vite 开发服务器
EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
