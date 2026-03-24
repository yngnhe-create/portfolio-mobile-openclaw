const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Static files
app.use(express.static(path.join(__dirname, 'public')));

// ── CORS Proxy: Naver Stock API ──
app.get('/api/stock/:code', async (req, res) => {
  const { code } = req.params;
  if (!/^\d{6}$/.test(code)) return res.status(400).json({ error: 'Invalid stock code' });

  try {
    const url = `https://m.stock.naver.com/api/stock/${code}/basic`;
    const resp = await fetch(url, {
      headers: { 'User-Agent': 'Mozilla/5.0', 'Referer': 'https://m.stock.naver.com/' }
    });
    if (!resp.ok) return res.status(resp.status).json({ error: 'Naver API error' });
    const data = await resp.json();
    res.json(data);
  } catch (e) {
    res.status(502).json({ error: 'Proxy fetch failed' });
  }
});

// ── CORS Proxy: Generic (replaces AllOrigins) ──
app.get('/api/proxy', async (req, res) => {
  const { url } = req.query;
  if (!url) return res.status(400).json({ error: 'Missing url parameter' });

  // Allowlist: only proxy known external APIs
  const allowed = [
    'query1.finance.yahoo.com',
    'api.upbit.com',
    'api.coingecko.com',
    'news.google.com',
    'api.allorigins.win'
  ];
  let parsedHost;
  try { parsedHost = new URL(url).hostname; } catch { return res.status(400).json({ error: 'Invalid URL' }); }
  if (!allowed.some(h => parsedHost.endsWith(h))) {
    return res.status(403).json({ error: 'Domain not allowed' });
  }

  try {
    const resp = await fetch(url, {
      headers: { 'User-Agent': 'Mozilla/5.0' }
    });
    const contentType = resp.headers.get('content-type') || '';
    const body = await resp.text();
    // Return in AllOrigins-compatible format for easy migration
    res.json({ contents: body, status: { content_type: contentType, http_code: resp.status } });
  } catch (e) {
    res.status(502).json({ error: 'Proxy fetch failed' });
  }
});

app.listen(PORT, () => {
  console.log(`Investment Command server running on port ${PORT}`);
});
