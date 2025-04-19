// server.js
import express from 'express';
import fetch from 'node-fetch';
import cors from 'cors';

const app = express();
const PORT = 3001;

const clientId = 'df18606c34634d53b54a6da720c75d0e';
const clientSecret = '0139389ffb5a4d059c5df0ce9fcb99bf';

let cachedToken = null;
let tokenExpiresAt = 0;

app.use(cors());
app.use(express.json());

// Get or refresh Spotify token
async function getSpotifyToken() {
  const now = Date.now();
  if (cachedToken && now < tokenExpiresAt) return cachedToken;

  const authString = Buffer.from(`${clientId}:${clientSecret}`).toString('base64');

  const res = await fetch('https://accounts.spotify.com/api/token', {
    method: 'POST',
    headers: {
      Authorization: `Basic ${authString}`,
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: 'grant_type=client_credentials',
  });

  if (!res.ok) {
    throw new Error(await res.text());
  }

  const data = await res.json();
  cachedToken = data.access_token;
  tokenExpiresAt = now + data.expires_in * 1000;

  return cachedToken;
}

// 🔍 New /search endpoint for song lookup
app.get('/search', async (req, res) => {
  const query = req.query.q;
  if (!query) return res.status(400).send('Missing search query');

  try {
    const token = await getSpotifyToken();

    const searchRes = await fetch(`https://api.spotify.com/v1/search?q=${encodeURIComponent(query)}&type=track&limit=1`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    const data = await searchRes.json();
    const track = data.tracks?.items?.[0];

    if (!track) return res.status(404).send('Track not found');

    res.json({
      title: track.name,
      artist: track.artists.map(a => a.name).join(', '),
      previewUrl: track.preview_url,
      artwork: track.album.images?.[0]?.url || '',
      genre: null, // Could be improved by calling /artists endpoint
    });
  } catch (err) {
    console.error(err);
    res.status(500).send('Server error');
  }
});

app.listen(PORT, () => {
  console.log(`🎧 Spotify token proxy + search running at http://localhost:${PORT}`);
});
