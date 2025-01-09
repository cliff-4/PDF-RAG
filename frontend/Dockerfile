FROM node:20.15.1

WORKDIR /frontend

# Installing dependencies
COPY package*.json ./
RUN npm install

COPY . .

# Building
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
