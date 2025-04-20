// server.js
import express from 'express';
import fetch from 'node-fetch';
import cors from 'cors';
import dotenv from 'dotenv';
import multer from 'multer';
import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';


const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config();

const app = express();
const PORT = 3005;

const clientId = process.env.SPOTIFY_CLIENT_ID;
const clientSecret = process.env.SPOTIFY_CLIENT_SECRET;

let cachedToken = null;
let tokenExpiresAt = 0;

app.use(cors());
app.use(express.json());

// === MULTER SETUP FOR FILE UPLOADS ===
const upload = multer({ dest: 'uploads/' });

// === SPOTIFY TOKEN HELPER ===
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

// === EXISTING SPOTIFY SEARCH ROUTE ===
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
      genre: null,
    });
  } catch (err) {
    console.error(err);
    res.status(500).send('Server error');
  }
});

app.post('/recommend', upload.single('file'), (req, res) => {
  const filePath = req.file.path;
  console.log("/recommend route was hit");
  console.log("Received file upload:", filePath);

  const pythonScript = path.join(__dirname, '../siamese_network/recommend_from_file.py');
  const python = spawn('python', [pythonScript, filePath]);

  let output = '';
  let errorOutput = '';

  python.stdout.on("data", (data) => {
    output += data.toString();
    console.log("[Python stdout]", data.toString());
  });

  python.stderr.on("data", (data) => {
    errorOutput += data.toString();
    console.error("[Python stderr]", data.toString());
  });

  python.on("close", (code) => {
    console.log("Python exited with code:", code);
  
    if (code !== 0) {
      console.error("Python script failed:", errorOutput);
      return res.status(500).json({
        error: "Python script failed",
        stderr: errorOutput
      });
    }
  
    try {
      // Safely extract JSON from the full output
      const matches = output.match(/\[\s*\{[\s\S]*?\}\s*\]/); // Regex to extract a JSON array
  
      if (!matches || matches.length === 0) {
        throw new Error("No valid JSON found in Python output");
      }
  
      const parsed = JSON.parse(matches[0]);
      res.json(parsed);
    } catch (err) {
      console.error("Failed to parse Python output:", err.message);
      res.status(500).json({
        error: "Invalid JSON from Python",
        raw: output
      });
    }
  });  
});
  

app.use(express.static(path.join(__dirname, '../frontend')));


app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
