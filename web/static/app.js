const modeButtons = Array.from(document.querySelectorAll(".mode-button"));
const panels = {
  webcam: document.querySelector("#webcamPanel"),
  image: document.querySelector("#imagePanel"),
  video: document.querySelector("#videoPanel"),
};

const labels = {
  webcam: "Webcam",
  image: "Image",
  video: "Video",
};

const statusBadge = document.querySelector("#statusBadge");
const modeLabel = document.querySelector("#modeLabel");
const preview = document.querySelector("#previewImage");
const emptyState = document.querySelector("#emptyState");
const postureValue = document.querySelector("#postureValue");
const scoreValue = document.querySelector("#scoreValue");
const sideValue = document.querySelector("#sideValue");
const angleList = document.querySelector("#angleList");
const adviceList = document.querySelector("#adviceList");

modeButtons.forEach((button) => {
  button.addEventListener("click", () => setMode(button.dataset.mode));
});

document.querySelector("#startWebcam").addEventListener("click", startWebcam);
document.querySelector("#stopWebcam").addEventListener("click", stopPreview);
document.querySelector("#analyzeImage").addEventListener("click", analyzeImage);
document.querySelector("#playVideo").addEventListener("click", analyzeVideo);

function setMode(mode) {
  modeButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.mode === mode);
  });
  Object.entries(panels).forEach(([key, panel]) => {
    panel.classList.toggle("active", key === mode);
  });
  modeLabel.textContent = labels[mode];
  stopPreview();
  resetMetrics();
}

function startWebcam() {
  showStream(`/stream/webcam?ts=${Date.now()}`);
  setStatus("Camera", "good");
  resetMetrics("Live overlay");
}

function stopPreview() {
  preview.removeAttribute("src");
  preview.classList.remove("active");
  emptyState.style.display = "block";
  setStatus("Ready");
}

async function analyzeImage() {
  const input = document.querySelector("#imageInput");
  const file = input.files[0];
  if (!file) {
    setStatus("Choose image", "bad");
    return;
  }

  const form = new FormData();
  form.append("file", file);
  setStatus("Analyzing");

  try {
    const response = await fetch("/api/analyze-image", {
      method: "POST",
      body: form,
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Image analysis failed.");
    }
    preview.src = payload.image;
    preview.classList.add("active");
    emptyState.style.display = "none";
    renderMetrics(payload.result);
    setStatus(payload.result.detected ? "Done" : "No detection", payload.result.detected ? "good" : "bad");
  } catch (error) {
    stopPreview();
    setStatus("Error", "bad");
    resetMetrics(error.message);
  }
}

async function analyzeVideo() {
  const input = document.querySelector("#videoInput");
  const file = input.files[0];
  if (!file) {
    setStatus("Choose video", "bad");
    return;
  }

  const form = new FormData();
  form.append("file", file);
  setStatus("Loading");

  try {
    const response = await fetch("/api/load-video", {
      method: "POST",
      body: form,
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Video analysis failed.");
    }
    showStream(`${payload.stream_url}?ts=${Date.now()}`);
    resetMetrics("Video overlay");
    setStatus("Video", "good");
  } catch (error) {
    stopPreview();
    setStatus("Error", "bad");
    resetMetrics(error.message);
  }
}

function showStream(url) {
  preview.src = url;
  preview.classList.add("active");
  emptyState.style.display = "none";
}

function setStatus(text, kind = "") {
  statusBadge.textContent = text;
  statusBadge.classList.toggle("good", kind === "good");
  statusBadge.classList.toggle("bad", kind === "bad");
}

function resetMetrics(message = "") {
  postureValue.textContent = message || "-";
  scoreValue.textContent = "-";
  sideValue.textContent = "-";
  angleList.innerHTML = "";
  adviceList.innerHTML = "";
}

function renderMetrics(result) {
  postureValue.textContent = result.posture || "-";
  scoreValue.textContent = result.detected ? `${result.score}/100` : "-";
  sideValue.textContent = result.side || "-";
  angleList.innerHTML = "";
  adviceList.innerHTML = "";

  if (!result.detected) {
    return;
  }

  result.angles.forEach((angle) => {
    const item = document.createElement("div");
    item.className = `angle-item ${angle.is_good ? "good" : "bad"}`;
    item.innerHTML = `
      <div class="angle-title">
        <span>${angle.label}</span>
        <span>${angle.angle} deg</span>
      </div>
      <div class="angle-detail">Deviation ${angle.deviation} deg / threshold ${angle.threshold} deg</div>
    `;
    angleList.appendChild(item);
  });

  result.advice.forEach((advice) => {
    const item = document.createElement("div");
    item.className = "advice-item";
    item.textContent = advice;
    adviceList.appendChild(item);
  });
}
