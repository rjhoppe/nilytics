# Build stage
FROM node:22-alpine AS builder
WORKDIR /app

RUN corepack enable && corepack prepare pnpm@9.15.0 --activate

COPY app/frontend/package.json app/frontend/pnpm-lock.yaml ./
COPY app/frontend .

RUN pnpm install --frozen-lockfile && pnpm build

# Run stage: serve static files with nginx
FROM nginx:alpine
COPY app/frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
