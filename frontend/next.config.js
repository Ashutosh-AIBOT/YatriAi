/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  async rewrites() {
    const orchestratorUrl = process.env.ORCHESTRATOR_URL || 'http://localhost:8001';
    const notificationUrl = process.env.NOTIFICATION_URL || 'http://localhost:3001';
    return [
      {
        source: '/api/v1/:path*',
        destination: `${orchestratorUrl}/api/v1/:path*`,
      },
      {
        source: '/socket.io/:path*',
        destination: `${notificationUrl}/socket.io/:path*`,
      }
    ];
  },
};

module.exports = nextConfig;
