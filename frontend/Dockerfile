FROM node:20-alpine

WORKDIR /app

# Copy package management files
COPY package.json package-lock.json* ./

# Install all dependencies inside the image
RUN npm install

# Copy all source files
COPY . .

# Build the Next.js production bundle
RUN npm run build

# Start the stable Next.js production server (no Turbopack, no hot-reload issues)
CMD ["npm", "start"]
