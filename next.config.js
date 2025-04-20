/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    domains: ['localhost', 'handwrite-app.vercel.app'],
  },
  experimental: {
    serverActions: true,
  },
};

module.exports = nextConfig;
