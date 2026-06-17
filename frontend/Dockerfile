FROM node:20-alpine

WORKDIR /app

# Copy package management files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy all files
COPY . .

# Start the Next.js development server
CMD ["npm", "run", "dev"]
