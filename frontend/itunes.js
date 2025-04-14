// itunes.js

/**
 * Enhances a song object with iTunes metadata: artwork + 30s preview
 */
export async function enrichWithItunesData(song) {
    const query = `${song.title} ${song.artist}`;
    const url = `https://itunes.apple.com/search?term=${encodeURIComponent(query)}&entity=song&limit=1`;
  
    try {
      const res = await fetch(url);
      const data = await res.json();
  
      if (data.results.length === 0) return song; // fallback: return original song
  
      const result = data.results[0];
      return {
        ...song,
        previewUrl: result.previewUrl,
        artwork: result.artworkUrl100 || result.artworkUrl60
      };
    } catch (err) {
      console.error("Failed to enrich with iTunes:", err);
      return song;
    }
  }
  
  
  /**
   * Gets preview/audio/artwork for the uploaded song using just the filename/title
   */
  export async function getPreviewForUploadedSong(query) {
    const url = `https://itunes.apple.com/search?term=${encodeURIComponent(query)}&entity=song&limit=1`;
  
    try {
      const res = await fetch(url);
      const data = await res.json();
  
      if (data.results.length === 0) return null;
  
      const result = data.results[0];
      return {
        title: result.trackName,
        artist: result.artistName,
        artwork: result.artworkUrl100,
        previewUrl: result.previewUrl
      };
    } catch (err) {
      console.error("Failed to get preview for uploaded song:", err);
      return null;
    }
  }
  