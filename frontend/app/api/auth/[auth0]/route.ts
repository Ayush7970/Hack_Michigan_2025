import { handleAuth } from '@auth0/nextjs-auth0/edge';

// App Router route handler – supports GET/POST
export const GET = handleAuth();
export const POST = handleAuth();