import { handleAuth } from '@auth0/nextjs-auth0';

// App Router route handler – supports GET/POST
export const GET = handleAuth();
export const POST = handleAuth();