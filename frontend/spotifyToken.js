// spotifySearch.js (or whatever your frontend filename is)
export async function searchSpotifyPreview(query) {
  const res = await fetch(`http://localhost:3001/search?q=${encodeURIComponent(query)}`);

  if (!res.ok) {
    console.error("❌ Failed to fetch from local proxy:", await res.text());
    return null;
  }

  const data = await res.json();
  return data;
}
