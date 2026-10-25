import { createLandingServer } from './serve.mjs';

// Container startup consumes the verified build; it never rebuilds or writes it.
try {
  const server = await createLandingServer();
  server.on('error', error => { console.error(error.message); process.exitCode = 1; });
  server.listen(8080, '0.0.0.0', () => console.log('Economicon landing ready on port 8080'));
  for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => {
    server.close();
    server.closeIdleConnections();
  });
} catch (error) { console.error(error.message); process.exitCode = 1; }
