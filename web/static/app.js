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
let selectedMediaUrl = "";
let activeStreamController = null;

modeButtons.forEach((button) => {
  button.addEventListener("click", () => setMode(button.dataset.mode));
});

document.querySelector("#startWebcam").addEventListener("click", startWebcam);
document.querySelector("#stopWebcam").addEventListener("click", stopPreview);
document.querySelector("#analyzeImage").addEventListener("click", analyzeImage);
document.querySelector("#playVideo").addEventListener("click", analyzeVideo);
imageInput.addEventListener("change", previewSelectedImage);
videoInput.addEventListener("change", previewSelectedVideo);

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
  stopActiveStream();
  clearSelectedMediaUrl();
  resetMetrics("Starting camera");
  setStatus("Camera", "good");
  activeStreamController = new AbortController();
  readWebcamStream(activeStreamController.signal);
}

function stopPreview() {
  stopActiveStream();
  clearSelectedMediaUrl();
  preview.removeAttribute("src");
  previewVideo.removeAttribute("src");
  previewVideo.pause();
  preview.classList.remove("active");
  previewVideo.classList.remove("active");
  emptyState.style.display = "block";
  setStatus("Ready");
}

async function readWebcamStream(signal) {
  try {
    const response = await fetch(`/stream/webcam-json?ts=${Date.now()}`, { signal });
    if (!response.ok || !response.body) {
      throw new Error("Webcam stream could not start.");
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
        setStatus(payload.result.detected ? "Camera" : "No detection", payload.result.detected ? "good" : "bad");
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
    showImage(`${payload.stream_url}?ts=${Date.now()}`);
    resetMetrics("Video overlay");
    setStatus("Video", "good");
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
  showVideo(selectedMediaUrl);
  resetMetrics("Video selected");
  setStatus("Selected", "good");
}

function showImage(url) {
  preview.src = url;
  preview.classList.add("active");
  previewVideo.pause();
  previewVideo.removeAttribute("src");
  previewVideo.classList.remove("active");
  emptyState.style.display = "none";
}

function showVideo(url) {
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
  postureValue.classList.remove("error-text");
  postureValue.textContent = result.posture || "-";
  scoreValue.textContent = result.detected ? `${result.score}/100` : "-";
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

  footerPosture.textContent = result.overall_good ? "Good Posture" : "Bad Posture";
  footerPosture.className = result.overall_good ? "good" : "bad";
  footerMeta.textContent = `Score ${result.score}/100 / Side ${result.side || "-"}`;

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

    const footerItem = document.createElement("span");
    footerItem.className = `footer-angle ${angle.is_good ? "good" : "bad"}`;
    footerItem.textContent = `${angle.label}: ${angle.angle} deg, dev ${angle.deviation} deg`;
    footerAngles.appendChild(footerItem);
  });

  footerAdvice.textContent = result.advice.slice(0, 2).join(" | ");

  result.advice.forEach((advice) => {
    const item = document.createElement("div");
    item.className = "advice-item";
    item.textContent = advice;
    adviceList.appendChild(item);
  });
}

function stopActiveStream() {
  if (activeStreamController) {
    activeStreamController.abort();
    activeStreamController = null;
  }
}
