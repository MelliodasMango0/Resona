/**
 * Standardizes titles for better iTunes match accuracy
 */
function sanitizeQuery(text) {
  return text
    .replace(/\(.*?\)/g, "")           // remove text in parentheses
    .replace(/[\[\]!"#$%&'()*+,./:;<=>?@^_`{|}~]/g, "") // remove special chars
    .replace(/[-_]/g, " ")             // replace -/_ with space
    .replace(/\s+/g, " ")              // collapse multiple spaces
    .trim();
}

/**
 * Enhances a song object with iTunes metadata: artwork + 30s preview
 */
export async function enrichWithItunesData(song) {
  const query = sanitizeQuery(`${song.title} ${song.artist}`);
  const url = `https://itunes.apple.com/search?term=${encodeURIComponent(query)}&entity=song&limit=1`;

  console.log(`🎧 Enriching song with iTunes query: ${query}`);

  try {
    const res = await fetch(url);
    const data = await res.json();
    console.log("📀 iTunes response:", data);

    if (data.results.length === 0) return song;

    const match = data.results.find(result =>
      result.trackName.toLowerCase().includes(song.title.toLowerCase()) &&
      result.artistName.toLowerCase().includes(song.artist.toLowerCase())
    );
    
    if (!match) return song; // fallback to raw song data
    
    return {
      ...song,
      previewUrl: match.previewUrl || null,
      artwork: match.artworkUrl100 || match.artworkUrl60 || null
    };
    
  } catch (err) {
    console.error("❌ Failed to enrich with iTunes:", err);
    return song;
  }
}


/**
 * Gets preview/audio/artwork for the uploaded song using just the filename/title
 */
export async function getPreviewForUploadedSong(title, artist) {
  const query = sanitizeQuery(`${title} ${artist}`);
  const url = `https://itunes.apple.com/search?term=${encodeURIComponent(query)}&entity=song&limit=1`;

  console.log(`🎵 Searching iTunes for uploaded song: ${query}`);

  try {
    const res = await fetch(url);
    const data = await res.json();
    console.log("🎶 Uploaded song iTunes result:", data);

    if (data.results.length === 0) return null;

    const result = data.results[0];
    return {
      title: result.trackName,
      artist: result.artistName,
      artwork: result.artworkUrl100 || null,
      previewUrl: result.previewUrl || null
    };
  } catch (err) {
    console.error("❌ Failed to get preview for uploaded song:", err);
    return null;
  }
}
