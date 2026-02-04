FROM node:22-slim AS build

WORKDIR /frontend

COPY package*.json .
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /frontend/dist /usr/share/nginx/html
EXPOSE 80
