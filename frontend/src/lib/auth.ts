import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import Kakao from "next-auth/providers/kakao";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Credentials({
      name: "Email",
      credentials: {
        email: { label: "이메일", type: "email" },
        password: { label: "비밀번호", type: "password" },
      },
      async authorize(credentials) {
        const res = await fetch(`${API_URL}/api/v1/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: credentials?.email,
            password: credentials?.password,
          }),
        });

        if (!res.ok) return null;

        const data = await res.json();
        return {
          id: data.user.id,
          email: data.user.email,
          name: data.user.name,
          accessToken: data.access_token,
          refreshToken: data.refresh_token,
          profile: data.user.profile,
          provider: data.user.provider,
        };
      },
    }),
    Kakao({
      clientId: process.env.KAKAO_CLIENT_ID!,
      clientSecret: process.env.KAKAO_CLIENT_SECRET!,
    }),
  ],
  callbacks: {
    authorized({ auth, request: { nextUrl } }) {
      // 개발 모드에서는 모든 경로 허용
      return true;
    },
    async jwt({ token, user, account }) {
      if (user) {
        token.id = user.id;
        token.accessToken = (user as any).accessToken;
        token.refreshToken = (user as any).refreshToken;
        token.profile = (user as any).profile;
        token.provider = (user as any).provider;
      }

      // 카카오 OAuth인 경우 백엔드에 토큰 전달
      if (account?.provider === "kakao" && account.access_token) {
        const res = await fetch(`${API_URL}/api/v1/auth/kakao`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ access_token: account.access_token }),
        });
        if (res.ok) {
          const data = await res.json();
          token.id = data.user.id;
          token.accessToken = data.access_token;
          token.refreshToken = data.refresh_token;
          token.profile = data.user.profile;
          token.provider = data.user.provider;
        }
      }

      return token;
    },
    async session({ session, token }) {
      session.user.id = token.id as string;
      (session as any).accessToken = token.accessToken;
      (session as any).profile = token.profile;
      (session as any).provider = token.provider;
      return session;
    },
  },
  pages: {
    signIn: "/login",
  },
  session: {
    strategy: "jwt",
  },
});
