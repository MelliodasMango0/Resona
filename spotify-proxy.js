// spotify-proxy.js
import express from 'express';
import fetch from 'node-fetch';
import cors from 'cors';
import dotenv from 'dotenv';
dotenv.config();

const clientId = process.env.SPOTIFY_CLIENT_ID;
const clientSecret = process.env.SPOTIFY_CLIENT_SECRET;

const app = express();
app.use(cors());
app.use(express.json());


let cachedToken = null;
let tokenExpiresAt = 0;

async function getAccessToken() {
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

  const data = await res.json();
  cachedToken = data.access_token;
  tokenExpiresAt = now + data.expires_in * 1000;
  return cachedToken;
}

app.get('/search', async (req, res) => {
  const query = req.query.q;
  if (!query) return res.status(400).json({ error: 'Missing query parameter' });

  try {
    const token = await getAccessToken();
    const searchRes = await fetch(`https://api.spotify.com/v1/search?q=${encodeURIComponent(query)}&type=track&market=US&limit=1`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    const json = await searchRes.json();
    const track = json.tracks?.items?.[0];
    if (!track) return res.status(404).json({ error: 'No track found' });

    res.json({
      title: track.name,
      artist: track.artists.map(a => a.name).join(', '),
      previewUrl: track.preview_url,
      artwork: track.album.images?.[0]?.url || '',
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Spotify search failed' });
  }
});

app.listen(3001, () => {
  console.log('🎧 Spotify token proxy listening on http://localhost:3001');
});
// spotify-proxy.js
import express from 'express';
import fetch from 'node-fetch';
import cors from 'cors';
import dotenv from 'dotenv';
dotenv.config();

const clientId = process.env.SPOTIFY_CLIENT_ID;
const clientSecret = process.env.SPOTIFY_CLIENT_SECRET;

const app = express();
app.use(cors());
app.use(express.json());


let cachedToken = null;
let tokenExpiresAt = 0;

async function getAccessToken() {
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

  const data = await res.json();
  cachedToken = data.access_token;
  tokenExpiresAt = now + data.expires_in * 1000;
  return cachedToken;
}

app.get('/search', async (req, res) => {
  const query = req.query.q;
  if (!query) return res.status(400).json({ error: 'Missing query parameter' });

  try {
    const token = await getAccessToken();
    const searchRes = await fetch(`https://api.spotify.com/v1/search?q=${encodeURIComponent(query)}&type=track&market=US&limit=1`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    const json = await searchRes.json();
    const track = json.tracks?.items?.[0];
    if (!track) return res.status(404).json({ error: 'No track found' });

    res.json({
      title: track.name,
      artist: track.artists.map(a => a.name).join(', '),
      previewUrl: track.preview_url,
      artwork: track.album.images?.[0]?.url || '',
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Spotify search failed' });
  }
});

app.listen(3001, () => {
  console.log('🎧 Spotify token proxy listening on http://localhost:3001');
});