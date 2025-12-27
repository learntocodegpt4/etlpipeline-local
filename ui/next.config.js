/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  basePath: process.env.NEXT_PUBLIC_BASE_PATH || '',
  assetPrefix: process.env.NEXT_PUBLIC_ASSET_PREFIX || '',
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws',
    NEXT_PUBLIC_RULE_ENGINE_API_URL: process.env.NEXT_PUBLIC_RULE_ENGINE_API_URL || '/ruleapi/api',
  },
  // Fix for standalone mode with custom basePath
  experimental: {
    outputFileTracingRoot: undefined,
  },
};

module.exports = nextConfig;