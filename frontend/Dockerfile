# Build stage
FROM node:24-alpine AS builder

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy source
COPY frontend/ ./

# Build
RUN npm run build

# Runtime stage - serve with nginx
FROM nginx:alpine AS runtime

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Create non-root user
RUN addgroup -g 1001 -S appuser && \
    adduser -S -D -H -u 1001 -h /usr/share/nginx/html -s /sbin/nologin -G appuser appuser && \
    chown -R appuser:appuser /usr/share/nginx/html /var/cache/nginx /var/log/nginx /etc/nginx/conf.d

USER appuser

EXPOSE 5173

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5173 || exit 1

CMD ["nginx", "-g", "daemon off;"]