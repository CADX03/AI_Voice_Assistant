#### Build Stage
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
# Build the app with VITE_BACKEND_URL passed as an environment variable
ARG VITE_BACKEND_URL
ENV VITE_BACKEND_URL=$VITE_BACKEND_URL
RUN npm run build

#### Development Stage
FROM node:18-alpine AS development
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
# Use the VITE_BACKEND_URL from the environment
ARG VITE_BACKEND_URL
ENV VITE_BACKEND_URL=$VITE_BACKEND_URL
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]

# Production Stage
FROM nginx:1.26-alpine AS production
COPY --from=build /app/dist /usr/share/nginx/html
# Add custom Nginx configuration for WebSocket support
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]