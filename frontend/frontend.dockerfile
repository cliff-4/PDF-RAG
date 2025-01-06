# Use an official Node.js runtime as a parent image
FROM node:20.15.1

# Set the working directory
WORKDIR /frontend

# Copy package.json and package-lock.json
COPY package*.json ./

# Install frontend dependencies
RUN npm install

# Copy the rest of the frontend code
COPY . .

# Expose the frontend port
EXPOSE 3000

# Start the frontend application
CMD ["npm", "run", "dev"]
