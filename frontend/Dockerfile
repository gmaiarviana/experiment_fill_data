# Use Node.js 18 Alpine as base image
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files first to leverage Docker cache
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Expose port 3001
EXPOSE 3001

# Development mode with hot reload
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3001"] 