import { getRecommendations } from './api.js';
import { enrichWithItunesData, getPreviewForUploadedSong } from './itunes.js';

const fileInput = document.getElementById("fileInput");
const playBtn = document.getElementById("playBtn");
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

  const previewData = await getPreviewForUploadedSong(baseName);

  if (!previewData) {
    renderLeftPanelError();
    return;
  }

  uploadedSongData = {
    ...previewData,
    filename: file.name
  };

  renderLeftPanel(uploadedSongData);
});

// === PLAY BUTTON HANDLER ===
playBtn.addEventListener("click", () => {
  if (uploadedSongData?.previewUrl) {
    const audio = new Audio(uploadedSongData.previewUrl);
    audio.play();
  }
});

// === ANALYZE LOGIC ===
async function handleAnalyze(song) {
  if (!song?.title) return;

  showLoading();
  const rawRecs = await getRecommendations(song.title, song.filename || "");
  const enriched = await Promise.all(rawRecs.map(enrichWithItunesData));
  renderRecommendations(enriched);
}

// === RENDER LEFT PANEL ===
function renderLeftPanel(song) {
  const panel = document.querySelector(".upload-box");
  panel.innerHTML = `
    <img src="${song.artwork}" width="100" style="border-radius:8px;margin-bottom:1rem"/>
    <h3>${song.title}</h3>
    <p>${song.artist}</p>
    <audio controls src="${song.previewUrl}"></audio>
    <br />
    <button id="analyzeBtn">🔍 Find Similar</button>
    <button id="resetBtn">⏹ Reset</button>
  `;

  document.getElementById("analyzeBtn").onclick = () => handleAnalyze(song);
  document.getElementById("resetBtn").onclick = () => window.location.reload();
}

function renderLeftPanelError() {
  const panel = document.querySelector(".upload-box");
  panel.innerHTML = `
    <p style="color:#ccc; margin-bottom: 0.5rem;">⚠️ Could not find preview for this song.</p>
    <p style="color:#888;">Try uploading a different file.</p>
    <input type="file" id="fileInput" />
  `;

  document.getElementById("fileInput").addEventListener("change", async (e) => {
    const file = e.target.files[0];
    const baseName = file.name.replace(/\.[^/.]+$/, "").replace(/[-_]/g, " ").trim();
    const previewData = await getPreviewForUploadedSong(baseName);

    if (previewData) {
      uploadedSongData = { ...previewData, filename: file.name };
      renderLeftPanel(uploadedSongData);
    } else {
      renderLeftPanelError();
    }
  });
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
