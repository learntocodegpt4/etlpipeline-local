const { createServer } = require('http');
const { parse } = require('url');
const next = require('next');

const app = next({ 
  dev: false,
  dir: '.',
  conf: {
    basePath: '/etlui',
    assetPrefix: '/etlui',
  }
});

const handle = app.getRequestHandler();

app.prepare().then(() => {
  createServer(async (req, res) => {
    try {
      // Parse URL
      const parsedUrl = parse(req.url, true);
      
      // If request is for /etlui/*, rewrite to /* for Next.js
      if (parsedUrl.pathname.startsWith('/etlui')) {
        parsedUrl.pathname = parsedUrl.pathname.replace(/^\/etlui/, '') || '/';
        req.url = parsedUrl.pathname + (parsedUrl.query ? '?' + new URLSearchParams(parsedUrl.query) : '');
      }
      
      await handle(req, res, parsedUrl);
    } catch (err) {
      console.error(err);
      res.statusCode = 500;
      res.end('Internal server error');
    }
  }).listen(3001, (err) => {
    if (err) throw err;
    console.log('> Ready on http://localhost:3001/etlui');
  });
});