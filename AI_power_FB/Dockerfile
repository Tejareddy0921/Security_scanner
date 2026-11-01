FROM node:24-alpine AS build

WORKDIR /app

COPY ["AI-Powered Scam Detection System/package.json", "AI-Powered Scam Detection System/package-lock.json", "./"]
RUN npm ci

COPY ["AI-Powered Scam Detection System/", "./"]

# Vite embeds this public API origin into the browser bundle at build time.
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build

FROM nginxinc/nginx-unprivileged:stable-alpine AS runtime

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080
