FROM node:22-slim

WORKDIR /frontend

COPY package*.json .
RUN npm ci

COPY . .

CMD ["npm", "run", "dev"]
