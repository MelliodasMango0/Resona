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
    .replace(/\.[^/.]+$/, '')   // Remove file extension
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
playBtn.addEventListener("click", async () => {
  if (uploadedSongData?.previewUrl) {
    const panel = document.querySelector(".upload-box");
    panel.innerHTML = `
      <img src="${uploadedSongData.artwork}" width="100" style="border-radius:8px;margin-bottom:1rem"/>
      <h3>${uploadedSongData.title}</h3>
      <p>${uploadedSongData.artist} • ${uploadedSongData.genre}</p>
      <div class="audio-container">
        <audio id="songAudio" controls src="${uploadedSongData.previewUrl}"></audio>
        <canvas id="audioVisualizer" width="300" height="60"></canvas>
      </div>
      <br />
      <button id="analyzeBtn">🔍 Find Similar</button>
      <button id="uploadAnotherBtn">📂 Upload Another Song</button>
      <input type="file" id="reUploadInput" style="display:none" />
    `;

    // Get references to the elements
    const audioElement = document.getElementById("songAudio");
    const canvas = document.getElementById("audioVisualizer");
    
    setupVisualizer(audioElement, canvas);
    
    // Add button event listeners
    document.getElementById("analyzeBtn").onclick = () => handleAnalyze(uploadedSongData);
    
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
async function renderLeftPanel(song) {
  const panel = document.querySelector(".upload-box");
  panel.innerHTML = `
    <img src="${song.artwork}" width="100" style="border-radius:8px;margin-bottom:1rem"/>
    <h3>${song.title}</h3>
    <p>${song.artist} • ${song.genre}</p>
    <div class="audio-container">
      <audio id="songAudio" controls></audio>
      <canvas id="audioVisualizer" width="300" height="60"></canvas>
    </div>
    <br />
    <button id="analyzeBtn">🔍 Find Similar</button>
    <button id="uploadAnotherBtn">📂 Upload Another Song</button>
    <input type="file" id="reUploadInput" style="display:none" />
  `;

  // Set up the visualizer after the audio element is rendered
  const audioElement = document.getElementById("songAudio");
  // Fetch the audio preview and convert to blob to avoid CORS issues
  try {
    const res = await fetch(song.previewUrl);
    const blob = await res.blob();
    const localUrl = URL.createObjectURL(blob);
    audioElement.src = localUrl;

    // Setup visualizer with blob-based local audio
    const canvas = document.getElementById("audioVisualizer");
    setupVisualizer(audioElement, canvas);
  } catch (err) {
    console.error("Failed to fetch preview audio as blob:", err);
  }

  const canvas = document.getElementById("audioVisualizer");

  document.getElementById("analyzeBtn").onclick = () => handleAnalyze(song);
  
  // Re-upload logic
  const reUploadInput = document.getElementById("reUploadInput");
  document.getElementById("uploadAnotherBtn").onclick = () => {
    reUploadInput.click();
  };

  reUploadInput.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

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

// === SETUP VISUALIZER FUNCTION ===
function setupVisualizer(audioElement, canvas) {
  if (!audioElement || !canvas) return;
  
  // Get canvas context
  const canvasCtx = canvas.getContext('2d');
  
  // Create a fresh audio context each time
  const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  const analyser = audioCtx.createAnalyser();
  analyser.fftSize = 128;
  
  // Create media source from audio element
  const source = audioCtx.createMediaElementSource(audioElement);
  source.connect(analyser);
  analyser.connect(audioCtx.destination);
  
  // Create data array for visualization
  const bufferLength = analyser.frequencyBinCount;
  const dataArray = new Uint8Array(bufferLength);
  
  // Animation frame ID for cleanup
  let animationId = null;
  
  // Draw function that gets called repeatedly
  function draw() {
    // Set dimensions
    canvas.width = canvas.clientWidth || 300;
    canvas.height = canvas.clientHeight || 60;
    
    // Request next frame first
    animationId = requestAnimationFrame(draw);
    
    // Get frequency data
    analyser.getByteFrequencyData(dataArray);
    
    // Clear canvas with semi-transparent black for trails
    canvasCtx.fillStyle = 'rgba(0, 0, 0, 0.2)';
    canvasCtx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Calculate bar width and spacing
    const barWidth = (canvas.width / bufferLength) * 2;
    const barSpacing = 1;
    let x = 0;
    
    // Draw bars
    for (let i = 0; i < bufferLength; i++) {
      // Skip some bars for aesthetics
      if (i % 2 !== 0) continue;
      
      // Calculate bar height based on frequency data
      const barHeight = dataArray[i] * (canvas.height / 255) * 0.7;
      
      // Vibrant color gradient based on frequency
      const hue = 120 + (i / bufferLength * 180);
      canvasCtx.fillStyle = `hsl(${hue}, 80%, 50%)`;
      
      // Draw the bar
      canvasCtx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
      
      // Move to next bar position
      x += barWidth + barSpacing;
    }
  }
  
  // Handle play/pause/stop events
  audioElement.addEventListener('play', () => {
    // Resume context if suspended
    if (audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
    
    // Start drawing
    draw();
  });
  
  audioElement.addEventListener('pause', () => {
    // Stop animation
    if (animationId) {
      cancelAnimationFrame(animationId);
      animationId = null;
    }
  });
  
  audioElement.addEventListener('ended', () => {
    // Stop animation
    if (animationId) {
      cancelAnimationFrame(animationId);
      animationId = null;
    }
  });
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

function getMatchClass(score) {
  if (score >= 90) return "match-high";
  if (score >= 80) return "match-medium";
  return "match-low";
}

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
        <p class="match-score ${getMatchClass(song.matchScore)}">
          ${song.matchScore}% match
        </p>
        ${song.previewUrl ? `<audio controls src="${song.previewUrl}"></audio>` : ""}
      </div>
    `;
    rightPanel.appendChild(card);
  });
}

// === SHOW LOADING PLACEHOLDER ===
function showLoading() {
  rightPanel.innerHTML = "";

  for (let i = 0; i < 5; i++) {
    const placeholder = document.createElement("div");
    placeholder.className = "song-card placeholder";
    placeholder.innerHTML = `
      <div class="image-placeholder shimmer"></div>
      <div class="info-placeholder shimmer"></div>
    `;
    rightPanel.appendChild(placeholder);
  }
}

// === RESET ON LOAD ===
window.onload = () => {
  if (fileInput) fileInput.value = "";
  uploadedSongData = null;

  // Clear left panel
  const panel = document.querySelector(".upload-box");
  if (panel) {
    panel.innerHTML = `
      <p>Drag & Drop your song here</p>
      <input type="file" id="fileInput" />
      <button id="playBtn">▶️ Play Sample</button>
      <button id="analyzeBtn">🔍 Find Similar</button>
    `;

    // Rebind file input event listener
    document.getElementById("fileInput").addEventListener("change", async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      const baseName = file.name.replace(/\.[^/.]+$/, "").replace(/[-_]/g, " ").trim();
      const previewData = await getPreviewForUploadedSong(baseName);

      if (previewData) {
        uploadedSongData = { ...previewData, filename: file.name };
        renderLeftPanel(uploadedSongData);
      } else {
        renderLeftPanelError();
      }
    });

    document.getElementById("analyzeBtn").addEventListener("click", () => {
      if (uploadedSongData?.title) handleAnalyze(uploadedSongData);
    });
  }
};

