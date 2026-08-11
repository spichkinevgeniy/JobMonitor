FROM node:22-alpine AS build

WORKDIR /frontend

COPY package.json package-lock.json ./
COPY apps/shell/package.json ./apps/shell/package.json
COPY apps/dashboard/package.json ./apps/dashboard/package.json
COPY packages/telegram/package.json ./packages/telegram/package.json
COPY packages/ui/package.json ./packages/ui/package.json

RUN npm ci

COPY apps ./apps
COPY packages ./packages

RUN npm run build:shell && npm run build:dashboard

FROM nginx:1.28-alpine AS runtime

COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /frontend/apps/shell/dist /usr/share/nginx/html/miniapp/react
COPY --from=build /frontend/apps/dashboard/dist /usr/share/nginx/html/miniapp/dashboard

EXPOSE 80
