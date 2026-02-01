# Frontend Dockerfile for Policy RAG UI
# Multi-stage build for production

# Stage 1: Build the React app
FROM node:20-slim AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Remove package-lock.json and reinstall to fix platform-specific dependencies
RUN rm -f package-lock.json && npm install

# Copy source code
COPY . .

# Build for production (API calls go to /api, proxied by nginx)
ENV VITE_API_BASE_URL=""
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost:80/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
