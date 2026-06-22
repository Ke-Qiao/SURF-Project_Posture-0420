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
const previewVideo = document.querySelector("#previewVideo");
const emptyState = document.querySelector("#emptyState");
const postureValue = document.querySelector("#postureValue");
const scoreValue = document.querySelector("#scoreValue");
const sideValue = document.querySelector("#sideValue");
const angleList = document.querySelector("#angleList");
const adviceList = document.querySelector("#adviceList");
const footerPosture = document.querySelector("#footerPosture");
const footerMeta = document.querySelector("#footerMeta");
const footerAngles = document.querySelector("#footerAngles");
const footerAdvice = document.querySelector("#footerAdvice");
const imageInput = document.querySelector("#imageInput");
const videoInput = document.querySelector("#videoInput");
const downloadEvidence = document.querySelector("#downloadEvidence");
let selectedMediaUrl = "";
let activeStreamController = null;
let activeMode = "webcam";
let latestResult = null;
let latestFrameDataUrl = "";
let latestSourceName = "";

modeButtons.forEach((button) => {
  button.addEventListener("click", () => setMode(button.dataset.mode));
});

document.querySelector("#startWebcam").addEventListener("click", startWebcam);
document.querySelector("#stopWebcam").addEventListener("click", stopPreview);
document.querySelector("#analyzeImage").addEventListener("click", analyzeImage);
document.querySelector("#playVideo").addEventListener("click", analyzeVideo);
downloadEvidence.addEventListener("click", downloadCurrentEvidence);
imageInput.addEventListener("change", previewSelectedImage);
videoInput.addEventListener("change", previewSelectedVideo);

function setMode(mode) {
  activeMode = mode;
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
  stopActiveStream();
  clearSelectedMediaUrl();
  latestSourceName = "webcam";
  resetMetrics("Starting camera");
  setStatus("Camera", "good");
  activeStreamController = new AbortController();
  readFrameStream(`/stream/webcam-json?ts=${Date.now()}`, activeStreamController.signal, "Camera");
}

function stopPreview() {
  stopActiveStream();
  clearSelectedMediaUrl();
  latestFrameDataUrl = "";
  refreshEvidenceButton();
  preview.removeAttribute("src");
  previewVideo.removeAttribute("src");
  previewVideo.pause();
  preview.classList.remove("active");
  previewVideo.classList.remove("active");
  emptyState.style.display = "block";
  setStatus("Ready");
}

async function readFrameStream(url, signal, statusLabel) {
  try {
    const response = await fetch(url, { signal });
    if (!response.ok || !response.body) {
      throw new Error(`${statusLabel} stream could not start.`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (!line.trim()) {
          continue;
        }
        const payload = JSON.parse(line);
        if (payload.error) {
          throw new Error(payload.error);
        }
        showImage(payload.image);
        renderMetrics(payload.result);
        setStatus(payload.result.detected ? statusLabel : "No detection", payload.result.detected ? "good" : "bad");
      }
    }
  } catch (error) {
    if (signal.aborted) {
      return;
    }
    stopPreview();
    setStatus("Error", "bad");
    showError(error.message);
  }
}

async function analyzeImage() {
  const file = imageInput.files[0];
  if (!file) {
    setStatus("Choose image", "bad");
    return;
  }

  const form = new FormData();
  form.append("file", file);
  setStatus("Analyzing");
  latestSourceName = file.name;

  try {
    const response = await fetch("/api/analyze-image", {
      method: "POST",
      body: form,
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Image analysis failed.");
    }
    clearSelectedMediaUrl();
    showImage(payload.image);
    renderMetrics(payload.result);
    setStatus(payload.result.detected ? "Done" : "No detection", payload.result.detected ? "good" : "bad");
  } catch (error) {
    stopPreview();
    setStatus("Error", "bad");
    showError(error.message);
  }
}

async function analyzeVideo() {
  const file = videoInput.files[0];
  if (!file) {
    setStatus("Choose video", "bad");
    return;
  }

  const form = new FormData();
  form.append("file", file);
  setStatus("Loading");
  latestSourceName = file.name;

  try {
    const response = await fetch("/api/load-video", {
      method: "POST",
      body: form,
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Video analysis failed.");
    }
    clearSelectedMediaUrl();
    resetMetrics("Video overlay");
    setStatus("Video", "good");
    activeStreamController = new AbortController();
    const streamUrl = payload.json_stream_url || payload.stream_url.replace("/stream/video/", "/stream/video-json/");
    readFrameStream(`${streamUrl}?ts=${Date.now()}`, activeStreamController.signal, "Video");
  } catch (error) {
    stopPreview();
    setStatus("Error", "bad");
    showError(error.message);
  }
}

function previewSelectedImage() {
  const file = imageInput.files[0];
  if (!file) {
    return;
  }
  clearSelectedMediaUrl();
  selectedMediaUrl = URL.createObjectURL(file);
  latestSourceName = file.name;
  showImage(selectedMediaUrl);
  resetMetrics("Image selected");
  setStatus("Selected", "good");
}

function previewSelectedVideo() {
  const file = videoInput.files[0];
  if (!file) {
    return;
  }
  clearSelectedMediaUrl();
  selectedMediaUrl = URL.createObjectURL(file);
  latestSourceName = file.name;
  showVideo(selectedMediaUrl);
  resetMetrics("Video selected");
  setStatus("Selected", "good");
}

function showImage(url) {
  preview.src = url;
  if (url.startsWith("data:image/")) {
    latestFrameDataUrl = url;
    refreshEvidenceButton();
  }
  preview.classList.add("active");
  previewVideo.pause();
  previewVideo.removeAttribute("src");
  previewVideo.classList.remove("active");
  emptyState.style.display = "none";
}

function showVideo(url) {
  latestFrameDataUrl = "";
  refreshEvidenceButton();
  preview.removeAttribute("src");
  preview.classList.remove("active");
  previewVideo.src = url;
  previewVideo.classList.add("active");
  emptyState.style.display = "none";
}

function clearSelectedMediaUrl() {
  if (selectedMediaUrl) {
    URL.revokeObjectURL(selectedMediaUrl);
    selectedMediaUrl = "";
  }
}

function setStatus(text, kind = "") {
  statusBadge.textContent = text;
  statusBadge.classList.toggle("good", kind === "good");
  statusBadge.classList.toggle("bad", kind === "bad");
}

function resetMetrics(message = "") {
  latestResult = null;
  latestFrameDataUrl = "";
  refreshEvidenceButton();
  postureValue.classList.remove("error-text");
  postureValue.textContent = message || "-";
  scoreValue.textContent = "-";
  sideValue.textContent = "-";
  angleList.innerHTML = "";
  adviceList.innerHTML = "";
  footerPosture.className = "";
  footerPosture.textContent = message || "Waiting for input";
  footerMeta.textContent = "Score - / Side -";
  footerAngles.innerHTML = "";
  footerAdvice.textContent = "";
}

function showError(message) {
  latestResult = null;
  refreshEvidenceButton();
  postureValue.textContent = "Error";
  postureValue.classList.add("error-text");
  scoreValue.textContent = "-";
  sideValue.textContent = "-";
  angleList.innerHTML = "";
  adviceList.innerHTML = "";
  footerPosture.textContent = "Error";
  footerPosture.className = "error-text";
  footerMeta.textContent = "Score - / Side -";
  footerAngles.innerHTML = "";
  footerAdvice.textContent = message;

  const item = document.createElement("div");
  item.className = "advice-item error-item";
  item.textContent = message;
  adviceList.appendChild(item);
}

function renderMetrics(result) {
  const advice = result.advice || [];
  const angles = result.angles || [];
  latestResult = result;
  refreshEvidenceButton();

  postureValue.classList.remove("error-text");
  postureValue.textContent = result.posture || "-";
  scoreValue.textContent = result.detected && typeof result.score === "number" ? `${result.score}/100` : "-";
  sideValue.textContent = result.side || "-";
  angleList.innerHTML = "";
  adviceList.innerHTML = "";
  footerAngles.innerHTML = "";
  footerAdvice.textContent = "";

  if (!result.detected) {
    footerPosture.textContent = "No detection";
    footerPosture.className = "bad";
    footerMeta.textContent = "Score - / Side -";
    return;
  }

  if (result.view_valid === false) {
    postureValue.textContent = result.posture || "Side view required";
    scoreValue.textContent = "-";
    sideValue.textContent = result.view || "-";
    footerPosture.textContent = result.posture || "Side view required";
    footerPosture.className = "bad";
    footerMeta.textContent = result.message || "Turn sideways before scoring";
    footerAdvice.textContent = advice.slice(0, 2).join(" | ");
    advice.forEach((adviceText) => {
      const item = document.createElement("div");
      item.className = "advice-item";
      item.textContent = adviceText;
      adviceList.appendChild(item);
    });
    return;
  }

  footerPosture.textContent = result.overall_good ? "Good Posture" : "Bad Posture";
  footerPosture.className = result.overall_good ? "good" : "bad";
  footerMeta.textContent = `Score ${result.score}/100 / Side ${result.side || "-"}`;

  angles.forEach((angle) => {
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

    const footerItem = document.createElement("span");
    footerItem.className = `footer-angle ${angle.is_good ? "good" : "bad"}`;
    footerItem.textContent = `${angle.label}: ${angle.angle} deg, dev ${angle.deviation} deg`;
    footerAngles.appendChild(footerItem);
  });

  footerAdvice.textContent = advice.slice(0, 2).join(" | ");

  advice.forEach((adviceText) => {
    const item = document.createElement("div");
    item.className = "advice-item";
    item.textContent = adviceText;
    adviceList.appendChild(item);
  });
}

function stopActiveStream() {
  if (activeStreamController) {
    activeStreamController.abort();
    activeStreamController = null;
  }
}

function refreshEvidenceButton() {
  downloadEvidence.disabled = !(latestResult && latestFrameDataUrl);
}

function downloadCurrentEvidence() {
  if (!latestResult || !latestFrameDataUrl) {
    setStatus("No evidence", "bad");
    return;
  }

  const evidence = {
    app: "surf-posture-demo",
    exported_at: new Date().toISOString(),
    mode: activeMode,
    source: latestSourceName || activeMode,
    result: latestResult,
    preview_image: latestFrameDataUrl,
  };
  const text = JSON.stringify(evidence, null, 2);
  const blob = new Blob([text], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  const stamp = evidence.exported_at.replace(/[:.]/g, "-");
  link.href = url;
  link.download = `surf-posture-evidence-${activeMode}-${stamp}.json`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
  setStatus("Evidence saved", "good");
}
