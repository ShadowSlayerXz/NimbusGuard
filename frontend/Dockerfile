FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json ./
RUN npm ci

# Copy application code
COPY . .

# Expose Next.js dev port
EXPOSE 3000

# Run Next.js dev server
CMD ["npm", "run", "dev"]
