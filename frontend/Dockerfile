FROM node:22-slim AS build

ARG VITE_MANAGEMENT_API_URL
ARG VITE_AZURE_CLIENT_ID
ARG VITE_AZURE_TENANT_ID

WORKDIR /frontend

COPY package*.json .
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /frontend/dist /usr/share/nginx/html
EXPOSE 80
