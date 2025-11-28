import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Handle /@username routes - rewrite to /u/username
  if (pathname.startsWith('/@')) {
    const username = pathname.slice(2); // Remove /@
    if (username) {
      const url = request.nextUrl.clone();
      url.pathname = `/u/${username}`;
      return NextResponse.rewrite(url);
    }
  }

  return NextResponse.next();
}

// Only run middleware on paths starting with /@
export const config = {
  matcher: '/((?!api|_next/static|_next/image|favicon.ico).*)',
};
