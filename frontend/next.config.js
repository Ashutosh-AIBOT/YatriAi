/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: 'http://localhost:8080/api/v1/:path*', // Proxy to Spring Boot Gateway
      },
      {
        source: '/socket.io/:path*',
        destination: 'http://localhost:3001/socket.io/:path*', // Proxy to Notification Service
      }
    ];
  },
};

module.exports = nextConfig;
