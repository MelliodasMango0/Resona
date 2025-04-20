// retrieves high res artwork from Spotify API

export async function getSpotifyArtwork(title, artist) {
    try {
      const res = await fetch(`http://localhost:3001/search?q=${encodeURIComponent(`${title} ${artist}`)}`);
      const data = await res.json();
      return data?.artwork || null;
    } catch (err) {
      console.error("❌ Spotify artwork fetch failed:", err);
      return null;
    }
  }
  