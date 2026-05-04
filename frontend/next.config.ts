import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    const orchestratorUrl = process.env.ORCHESTRATOR_URL || "http://localhost:8001";
    const gatewayUrl = process.env.GATEWAY_URL || "http://localhost:8080";
    const notificationUrl = process.env.NOTIFICATION_URL || "http://localhost:3001";

    return [
      {
        source: "/api/v1/auth/:path*",
        destination: `${gatewayUrl}/api/v1/auth/:path*`,
      },
      {
        source: "/api/v1/users/:path*",
        destination: `${gatewayUrl}/api/v1/users/:path*`,
      },
      {
        source: "/api/v1/:path*",
        destination: `${orchestratorUrl}/api/v1/:path*`,
      },
      {
        source: "/socket.io/:path*",
        destination: `${notificationUrl}/socket.io/:path*`,
      },
    ];
  },
};

export default nextConfig;
