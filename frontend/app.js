import { getRecommendations } from './api.js';
import { enrichWithItunesData, getPreviewForUploadedSong } from './itunes.js';

const fileInput = document.getElementById("fileInput");
const playBtn = document.getElementById("playBtn");
const analyzeBtn = document.getElementById("analyzeBtn");
const leftPanel = document.querySelector(".upload-box");
const rightPanel = document.querySelector(".recommendations");

let uploadedSongData = null;

// === HANDLE FILE UPLOAD ===
fileInput.addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  const baseName = file.name
  .replace(/\.[^/.]+$/, '') // Remove file extension
  .replace(/[-_]/g, ' ')     // Replace dashes/underscores with spaces
  .trim();
  uploadedSongData = await getPreviewForUploadedSong(baseName, file.name);

  if (!uploadedSongData) {
    leftPanel.innerHTML = `<p>Could not find preview for this song.</p>`;
    return;
  }

  renderLeftPanel(uploadedSongData);
});

// === PLAY BUTTON HANDLER ===
playBtn.addEventListener("click", () => {
  if (uploadedSongData?.previewUrl) {
    const audio = new Audio(uploadedSongData.previewUrl);
    audio.play();
  }
});

// === ANALYZE BUTTON HANDLER ===
analyzeBtn.addEventListener("click", async () => {
  if (!uploadedSongData?.title) return;

  showLoading();
  const rawRecs = await getRecommendations(uploadedSongData.title);
  const enriched = await Promise.all(rawRecs.map(enrichWithItunesData));
  renderRecommendations(enriched);
});

// === RENDER LEFT PANEL ===
function renderLeftPanel(song) {
    const previewArea = document.getElementById("previewArea");
  
    previewArea.innerHTML = `
      <img src="${song.artwork}" width="100" style="border-radius:8px;margin-bottom:1rem"/>
      <h3>${song.title}</h3>
      <p>${song.artist}</p>
      <audio controls src="${song.previewUrl}"></audio>
    `;
  }
  

// === RENDER RIGHT PANEL ===
function renderRecommendations(list) {
  rightPanel.innerHTML = "";

  list.forEach(song => {
    const card = document.createElement("div");
    card.className = "song-card";
    card.innerHTML = `
      <img src="${song.artwork || 'https://via.placeholder.com/100?text=🎵'}" />
      <div class="song-info">
        <h3>${song.title}</h3>
        <p>${song.artist} • ${song.genre}</p>
        <p><strong>${song.matchScore}% match</strong></p>
        ${song.previewUrl ? `<audio controls src="${song.previewUrl}"></audio>` : ""}
      </div>
    `;
    rightPanel.appendChild(card);
  });
}

// === SHOW LOADING PLACEHOLDER ===
function showLoading() {
  rightPanel.innerHTML = `
    <div class="song-card placeholder">
      <div class="image-placeholder shimmer"></div>
      <div class="info-placeholder shimmer"></div>
    </div>
    <div class="song-card placeholder">
      <div class="image-placeholder shimmer"></div>
      <div class="info-placeholder shimmer"></div>
    </div>
    <div class="song-card placeholder">
      <div class="image-placeholder shimmer"></div>
      <div class="info-placeholder shimmer"></div>
    </div>
  `;
}
