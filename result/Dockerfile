# Use the official Node.js 18 slim image
FROM node:18-slim

# Install curl and tini for healthcheck and process management
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl tini && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /usr/local/app

# Install nodemon globally for development (file watching) purposes
RUN npm install -g nodemon

# Copy package files first to leverage Docker layer caching for dependencies
COPY package*.json ./

# Install production dependencies using npm ci for a clean install
RUN npm ci --only=production && \
    npm cache clean --force

# Move node_modules to root to avoid issues with symlinks during development
RUN mv /usr/local/app/node_modules /node_modules

# Copy the entire application code to the container
COPY . .

# Set environment variables
ENV NODE_ENV production
ENV PORT 80

# Expose port 80 for the application
EXPOSE 80

# Use tini as the entrypoint for better signal handling in containers
ENTRYPOINT ["/usr/bin/tini", "--"]

# Run the application
CMD ["node", "server.js"]
