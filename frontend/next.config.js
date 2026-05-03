/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: 'http://localhost:8001/api/v1/:path*', // Proxy directly to Python Orchestrator (bypass Gateway for local dev)
      },
      {
        source: '/socket.io/:path*',
        destination: 'http://localhost:3001/socket.io/:path*', // Proxy to Notification Service
      }
    ];
  },
};

module.exports = nextConfig;
