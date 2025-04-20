import { disambiguateUploadedSong } from './api.js';
import {getSpotifyArtwork} from './spotifySearch.js';

function sanitizeQuery(text) {
  return text
    .replace(/\(.*?\)/g, "")
    .replace(/[\[\]!"#$%&'()*+,./:;<=>?@^_`{|}~]/g, "")
    .replace(/[-_]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export async function getPreviewForUploadedSong(filename) {
  const baseQuery = filename.replace(/\.[^/.]+$/, "").replace(/[-_]/g, " ").trim();
  const disambiguated = await disambiguateUploadedSong(baseQuery, filename);

  if (!disambiguated) {
    console.error("❌ Could not disambiguate song, falling back to base query.");
    return null;
  }

  const query = sanitizeQuery(`${disambiguated.title} ${disambiguated.artist}`);
  const url = `https://itunes.apple.com/search?term=${encodeURIComponent(query)}&entity=song&limit=5`;

  try {
    const res = await fetch(url);
    const data = await res.json();

    if (data.results.length === 0) return null;

    const filtered = data.results.filter(track =>
      track.artistName.toLowerCase() === disambiguated.artist.toLowerCase() &&
      !/karaoke|cover|remix|tribute|live/i.test(track.collectionName)
    );

    const bestMatch = filtered[0] || data.results[0];
    const spotifyArtwork = await getSpotifyArtwork(bestMatch.trackName, bestMatch.artistName);

    return {
      title: bestMatch.trackName,
      artist: bestMatch.artistName,
      genre: disambiguated.genre || "unknown",
      artwork: spotifyArtwork || bestMatch.artworkUrl100 || null,
      previewUrl: bestMatch.previewUrl || null
    };
  } catch (err) {
    console.error("❌ iTunes fetch error:", err);
    return null;
  }
}

/**
 * Enhances a song object with preview/audio from iTunes and artwork from Spotify
 */
export async function enrichWithItunesData(song) {
  const query = sanitizeQuery(`${song.title} ${song.artist}`);
  const url = `https://itunes.apple.com/search?term=${encodeURIComponent(query)}&entity=song&limit=5`;

  try {
    const res = await fetch(url);
    const data = await res.json();
    if (data.results.length === 0) return song;

    const filtered = data.results.filter(track =>
      track.artistName.toLowerCase() === song.artist.toLowerCase() &&
      !/karaoke|cover|remix|tribute|live/i.test(track.collectionName)
    );

    const bestMatch = filtered[0] || data.results[0];
    const spotifyArtwork = await getSpotifyArtwork(bestMatch.trackName, bestMatch.artistName);

    return {
      ...song,
      previewUrl: bestMatch.previewUrl || null,
      artwork: spotifyArtwork || bestMatch.artworkUrl100 || bestMatch.artworkUrl60 || null
    };
  } catch (err) {
    console.error("❌ Failed to enrich with iTunes:", err);
    return song;
  }
}

export async function enrichRecommendedSong(rawSong) {
  const baseQuery = `${rawSong.title} ${rawSong.artist}`;
  const disambiguated = await disambiguateUploadedSong(baseQuery, `${rawSong.artist} ~ ${rawSong.title}`);

  if (!disambiguated) {
    console.warn("⚠️ Could not disambiguate recommended song:", rawSong);
    return rawSong;
  }

  const query = sanitizeQuery(`${disambiguated.title} ${disambiguated.artist}`);
  const url = `https://itunes.apple.com/search?term=${encodeURIComponent(query)}&entity=song&limit=5`;

  try {
    const res = await fetch(url);
    const data = await res.json();
    if (data.results.length === 0) return rawSong;

    const filtered = data.results.filter(track =>
      track.artistName.toLowerCase() === disambiguated.artist.toLowerCase() &&
      !/karaoke|cover|remix|tribute|live/i.test(track.collectionName)
    );

    const bestMatch = filtered[0] || data.results[0];
    const spotifyArtwork = await getSpotifyArtwork(bestMatch.trackName, bestMatch.artistName);

    return {
      title: bestMatch.trackName,
      artist: bestMatch.artistName,
      genre: disambiguated.genre || "Unknown",
      matchScore: rawSong.matchScore || 0,
      previewUrl: bestMatch.previewUrl || null,
      artwork: spotifyArtwork || bestMatch.artworkUrl100 || null
    };
  } catch (err) {
    console.error("❌ Failed to enrich recommended song:", err);
    return rawSong;
  }
}
