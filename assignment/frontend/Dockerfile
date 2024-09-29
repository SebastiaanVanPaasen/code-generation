FROM node:20.9.0-slim
WORKDIR /app
ENV PATH /node_modules/.bin:$PATH
COPY package.json ./
COPY package-lock.json ./
RUN npm i
COPY . ./
CMD ["npm", "run", "dev", "--", "--host"]