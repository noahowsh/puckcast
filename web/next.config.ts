import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "assets.nhle.com",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "cms.nhl.bamgrid.com",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "nhl.bamcontent.com",
        pathname: "/**",
      },
    ],
  },
};

export default nextConfig;
