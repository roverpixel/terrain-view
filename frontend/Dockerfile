FROM public.ecr.aws/docker/library/node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy all frontend files
COPY . .

# Expose internal Vite dev server port
EXPOSE 7000

# Start the development server
CMD ["npm", "run", "dev","--","--host"]
