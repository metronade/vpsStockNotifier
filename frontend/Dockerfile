# ===== Base: install deps once =====
FROM node:20-alpine AS base
WORKDIR /app
COPY package*.json ./
# Switch to 'npm ci' once package-lock.json is committed.
RUN npm install

# ===== Development: Vite dev server with HMR =====
FROM base AS development
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# ===== Builder: produce static bundle =====
FROM base AS builder
COPY . .
RUN npm run build

# ===== Production: nginx SPA =====
FROM nginx:alpine AS production
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
