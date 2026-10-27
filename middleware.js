import { createClerkClient } from '@clerk/backend';
import { next } from '@vercel/functions';
import { createAuthGate } from './auth.js';

let client;
export default createAuthGate({
  getClient: () => client ??= createClerkClient({
    secretKey: process.env.CLERK_SECRET_KEY,
    publishableKey: process.env.CLERK_PUBLISHABLE_KEY,
  }),
  proceed: options => next(options),
});

// Includes index.html and all media; extension-based exclusions would leak data.
export const config = { matcher: '/:path*', runtime: 'nodejs' };
