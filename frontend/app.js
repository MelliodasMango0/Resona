import { getRecommendations } from './api.js';
import { enrichWithItunesData, getPreviewForUploadedSong } from './itunes.js';
import { getLocalRecommendationsFromFile } from './api.js';
import { enrichRecommendedSong } from './itunes.js';

const fileInput = document.getElementById("fileInput");
const playBtn = document.getElementById("playBtn");
const leftPanel = document.querySelector(".upload-box");
const rightPanel = document.querySelector(".recommendations");

let uploadedSongData = null;
let currentlyPlayingAudio = null;

window.onerror = function (message, source, lineno, colno, error) {
  console.error("Global JS Error Caught:", message, source, lineno, colno, error);
};

window.onunhandledrejection = function (e) {
  console.error("Unhandled Promise Rejection:", e.reason);
};

function pauseCurrentAudio() {
  if (currentlyPlayingAudio && !currentlyPlayingAudio.paused) {
    currentlyPlayingAudio.pause();
  }
}


// === HANDLE FILE UPLOAD ===
fileInput.addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  const baseName = file.name
    .replace(/\.[^/.]+$/, '')   // Remove file extension
    .replace(/[-_]/g, ' ')     // Replace dashes/underscores with spaces
    .trim();

  const previewData = await getPreviewForUploadedSong(baseName);

  console.log("Preview Data:", previewData);

  if (!previewData) {
    renderLeftPanelError();
    return;
  }

  uploadedSongData = {
    ...previewData,
    filename: file.name,
    originalFile: file
  };

  console.log("Sending to renderLeftPanel:", uploadedSongData);

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
    
    console.log("▶️ Play button clicked. Rendering audio element with preview URL:", uploadedSongData.previewUrl);
    console.log("🎨 Setting up visualizer for audio element:", audioElement);
    setupVisualizer(audioElement, canvas);
    
    // Add button event listeners
    document.getElementById("analyzeBtn").onclick = () => handleAnalyze(uploadedSongData);
    
  }
});

// === ANALYZE LOGIC ===
async function handleAnalyze(song) {

  console.log("Analyzing Song: ", song)

  if (!song?.filename || !song?.originalFile){ 
    console.log("Missing file");
    return;
  }

  showLoading();

  try {
    console.log("Getting Local Recommendations");
    const rawRecs = await getLocalRecommendationsFromFile(song.originalFile);
    console.log("Got Local Recommendations");
    const enriched = await Promise.all(rawRecs.map(enrichRecommendedSong));
    renderRecommendations(enriched);
  } catch (err) {
    console.error("Recommendation error:", err);
    alert("Something went wrong during recommendation.");
  }
}

// === RENDER LEFT PANEL ===
async function renderLeftPanel(song) {

  console.log("Rendering song:", song);

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
      uploadedSongData = { ...previewData, filename: file.name, originalFile: file };
      renderLeftPanel(uploadedSongData);
    } else {
      renderLeftPanelError();
    }
  });
}

function setupVisualizer(audioElement, canvas) {
  if (!audioElement || !canvas) return;

  const ctx = canvas.getContext('2d');
  const audioContext = new (window.AudioContext || window.webkitAudioContext)();
  const analyser = audioContext.createAnalyser();
  analyser.fftSize = 2048;
  analyser.smoothingTimeConstant = 0.7;

  const source = audioContext.createMediaElementSource(audioElement);
    source.connect(analyser);
  analyser.connect(audioContext.destination);

  const bufferLength = analyser.frequencyBinCount;
  const dataArray = new Uint8Array(bufferLength);

  let animationId = null; // needed to cancel animation

  function drawCenterLineOnly() {
    canvas.width = canvas.clientWidth || 300;
    canvas.height = canvas.clientHeight || 60;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const centerY = canvas.height / 2;
    ctx.strokeStyle = 'red';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, centerY);
    ctx.lineTo(canvas.width, centerY);
    ctx.stroke();
  }

  function draw() {
    animationId = requestAnimationFrame(draw); // store ID to cancel it

    analyser.getByteFrequencyData(dataArray);

    canvas.width = canvas.clientWidth || 300;
    canvas.height = canvas.clientHeight || 60;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const centerY = canvas.height / 2;

    // Red axis
    ctx.strokeStyle = 'red';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, centerY);
    ctx.lineTo(canvas.width, centerY);
    ctx.stroke();

    // Gradient fill
    const gradient = ctx.createLinearGradient(0, 0, canvas.width, 0);
    gradient.addColorStop(0, 'red');
    gradient.addColorStop(0.2, 'orange');
    gradient.addColorStop(0.4, 'yellow');
    gradient.addColorStop(0.6, 'green');
    gradient.addColorStop(0.8, 'blue');
    gradient.addColorStop(1, 'violet');
    ctx.fillStyle = gradient;

    const barWidth = canvas.width / bufferLength;
    let x = 0;

    for (let i = 0; i < bufferLength; i++) {
      const v = dataArray[i] / 128.0;
      const barHeight = (v - 1) * canvas.height * 0.4;

      ctx.fillRect(x, centerY, barWidth, barHeight);
      ctx.fillRect(x, centerY, barWidth, -barHeight);
      x += barWidth;
    }
  }

  audioElement.addEventListener('play', () => {
    pauseCurrentAudio(); // Pause any currently playing audio
    currentlyPlayingAudio = audioElement; // Set the currently playing audio
    audioContext.resume();
    draw(); // start drawing
  });

  audioElement.addEventListener('pause', () => {
    if (animationId) {
      cancelAnimationFrame(animationId);
      animationId = null;
    }
    drawCenterLineOnly();
  });

  audioElement.addEventListener('ended', () => {
    if (animationId) {
      cancelAnimationFrame(animationId);
      animationId = null;
    }
    drawCenterLineOnly();
  });

  drawCenterLineOnly(); // draw red axis on load
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
      uploadedSongData = { ...previewData, filename: file.name, originalFile: file };
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

function setupMiniVisualizer(audioElement, canvas) {
  const ctx = canvas.getContext('2d');
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const analyser = audioCtx.createAnalyser();
    analyser.fftSize = 2048;
    analyser.smoothingTimeConstant = 0.7;

  const source = audioCtx.createMediaElementSource(audioElement);
      source.connect(analyser);
      analyser.connect(audioCtx.destination);

  const bufferLength = analyser.frequencyBinCount;
  const dataArray = new Uint8Array(bufferLength);

  let animationId = null;

  function drawCenterLineOnly() {
    canvas.width = canvas.clientWidth || 80;
    canvas.height = canvas.clientHeight || 30;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const centerY = canvas.height / 2;
    ctx.strokeStyle = 'red';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, centerY);
    ctx.lineTo(canvas.width, centerY);
    ctx.stroke();
  }

  function draw() {
    animationId = requestAnimationFrame(draw);
    analyser.getByteFrequencyData(dataArray);

    canvas.width = canvas.clientWidth || 80;
    canvas.height = canvas.clientHeight || 30;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const centerY = canvas.height / 2;

    // Red axis
    ctx.strokeStyle = 'red';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, centerY);
    ctx.lineTo(canvas.width, centerY);
    ctx.stroke();

    // Gradient
    const gradient = ctx.createLinearGradient(0, 0, canvas.width, 0);
    gradient.addColorStop(0, 'red');
    gradient.addColorStop(0.25, 'yellow');
    gradient.addColorStop(0.5, 'lime');
    gradient.addColorStop(0.75, 'cyan');
    gradient.addColorStop(1, 'magenta');
    ctx.fillStyle = gradient;

    const barWidth = canvas.width / bufferLength;
    let x = 0;

    for (let i = 0; i < bufferLength; i++) {
      const v = dataArray[i] / 128.0;
      const barHeight = (v - 1) * canvas.height * 0.4;

      ctx.fillRect(x, centerY, barWidth, barHeight);
      ctx.fillRect(x, centerY, barWidth, -barHeight);
      x += barWidth;
    }
  }

  audioElement.addEventListener('play', () => {
    pauseCurrentAudio(); // Pause any currently playing audio
    currentlyPlayingAudio = audioElement; // Set the currently playing audio
    audioCtx.resume();
    draw();
  });

  audioElement.addEventListener('pause', () => {
    if (animationId) {
    cancelAnimationFrame(animationId);
      animationId = null;
    }
    drawCenterLineOnly();
  });

  audioElement.addEventListener('ended', () => {
    if (animationId) {
    cancelAnimationFrame(animationId);
      animationId = null;
    }
    drawCenterLineOnly();
  });

  drawCenterLineOnly();
}


function renderRecommendations(list) {
  rightPanel.innerHTML = "";

  list.forEach(async (song) => {
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
        <canvas class="mini-visualizer" width="80" height="30"></canvas>
        <audio class="rec-audio" controls></audio>
      </div>
    `;

    rightPanel.appendChild(card);

    const audio = card.querySelector('.rec-audio');
    const canvas = card.querySelector('.mini-visualizer');

    try {
      // Fetch blob version of the preview audio
      const res = await fetch(song.previewUrl);
      const blob = await res.blob();
      const localUrl = URL.createObjectURL(blob);
      audio.src = localUrl;

      // Now it's safe to create the visualizer
      setupMiniVisualizer(audio, canvas);
    } catch (err) {
      console.error("Error loading preview blob for:", song.title, err);
    }
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
        uploadedSongData = { ...previewData, filename: file.name, originalFile: file };
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

