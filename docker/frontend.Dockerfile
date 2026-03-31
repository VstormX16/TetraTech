FROM node:20-alpine AS build

WORKDIR /app/frontend

ARG VITE_API_BASE_URL=/api
ARG VITE_SIM_BASE_URL=/sim
ARG VITE_USER_MODEL_BASE_URL=/user-models

ENV VITE_API_BASE_URL=${VITE_API_BASE_URL} \
    VITE_SIM_BASE_URL=${VITE_SIM_BASE_URL} \
    VITE_USER_MODEL_BASE_URL=${VITE_USER_MODEL_BASE_URL}

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

FROM nginx:1.27-alpine

COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/frontend/dist /usr/share/nginx/html

RUN mkdir -p /usr/share/nginx/html/user-models

EXPOSE 80
