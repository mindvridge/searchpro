import "next-auth";

declare module "next-auth" {
  interface Session {
    user: {
      id: string;
      email: string;
      name?: string | null;
    };
    accessToken?: string;
    profile?: Record<string, unknown>;
    provider?: string;
  }

  interface User {
    id: string;
    email: string;
    name?: string | null;
    accessToken?: string;
    refreshToken?: string;
    profile?: Record<string, unknown>;
    provider?: string;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    id?: string;
    accessToken?: string;
    refreshToken?: string;
    profile?: Record<string, unknown>;
    provider?: string;
  }
}
