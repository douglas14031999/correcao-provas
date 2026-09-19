// Application State
let examsList = [];
let activeExamId = "AUTO"; // Default to AUTO recognition via QR Code
let currentFacingMode = "environment"; // Rear camera by default on smartphones
let cameraStream = null;
let currentAnswerKeyDraft = {};
let editingExamId = null; // ID of the exam currently being edited, or null if creating
let currentGradingResult = null; // Stores the latest graded submission result

// DOM Elements
const videoEl = document.getElementById("camera-video");
const canvasEl = document.getElementById("capture-canvas");
const captureBtn = document.getElementById("capture-btn");
const switchCameraBtn = document.getElementById("switch-camera-btn");
const fileInput = document.getElementById("file-fallback-input");
const nativeCameraInput = document.getElementById("native-camera-input");
const btnTriggerMobileCam = document.getElementById("btn-trigger-mobile-cam");
const btnTriggerGallery = document.getElementById("btn-trigger-gallery");
const cameraLoadingEl = document.getElementById("camera-loading");
const activeExamSelect = document.getElementById("active-exam-select");
const studentNameInput = document.getElementById("student-name-input");

// Tab Navigation
const tabButtons = document.querySelectorAll(".tab-btn");
const tabContents = document.querySelectorAll(".tab-content");

// Matrix generation elements
const numQuestionsInput = document.getElementById("exam-num-q-input");
const numOptionsSelect = document.getElementById("exam-num-opts-select");
const matrixContainer = document.getElementById("answer-key-matrix");
const createExamForm = document.getElementById("create-exam-form");
const goToCreateBtn = document.getElementById("go-to-create-btn");
const cancelCreateBtn = document.getElementById("cancel-create-btn");
const btnCancelEdit = document.getElementById("btn-cancel-edit");
const editModeBanner = document.getElementById("edit-mode-banner");
const editExamTitleSpan = document.getElementById("edit-exam-title");
const createCardTitle = document.getElementById("create-card-title");
const createCardDesc = document.getElementById("create-card-desc");
const saveExamBtn = document.getElementById("save-exam-btn");

// Results Elements
const resultPlaceholder = document.getElementById("result-placeholder");
const resultDisplay = document.getElementById("result-display");
const resScoreEl = document.getElementById("res-score");
const resMaxScoreEl = document.getElementById("res-max-score");
const resStudentNameEl = document.getElementById("res-student-name");
const resCorrectBadge = document.getElementById("res-correct-badge");
const resWrongBadge = document.getElementById("res-wrong-badge");
const resBlankBadge = document.getElementById("res-blank-badge");
const resProgressBar = document.getElementById("res-progress-bar");
const resOverlayImg = document.getElementById("res-overlay-img");
const resQuestionsTbody = document.getElementById("res-questions-tbody");

// Toggle Results View
const viewXrayBtn = document.getElementById("view-xray-btn");
const viewListBtn = document.getElementById("view-list-btn");
const xrayContainer = document.getElementById("xray-container");
const tableContainer = document.getElementById("table-container");

// Toast
const toastEl = document.getElementById("toast");

// --- Initialization ---
document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  loadSystemSettings();
  loadExams();
  initAnswerKeyMatrix();
  initEventListeners();
  checkAuthStatus();
  initLandscapeCameraListeners();
  checkOrientationAndAdjustCamera();
});

// Sound feedback using Web Audio API
function playSuccessSound() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
    osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.15); // A5
    gain.gain.setValueAtTime(0.2, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.25);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.25);
  } catch (e) {
    // Ignore audio context errors if browser blocks auto-play
  }
}

// --- Tabs Management ---
function initTabs() {
  // Pré-restauração visual rápida da aba antes de requisições de rede
  try {
    const savedTab = localStorage.getItem("omr_active_tab");
    if (savedTab && document.getElementById(savedTab)) {
      tabButtons.forEach(b => b.classList.toggle("active", b.dataset.tab === savedTab));
      const mobileBottomBtns = document.querySelectorAll(".bottom-nav-btn[data-tab]");
      mobileBottomBtns.forEach(b => b.classList.toggle("active", b.dataset.tab === savedTab));
      tabContents.forEach(c => {
        c.classList.toggle("active", c.id === savedTab);
      });
    }
  } catch (e) {}

  const brandLink = document.getElementById("nav-brand-link");
  if (brandLink) {
    brandLink.addEventListener("click", (e) => {
      e.preventDefault();
      switchTab("dashboard-tab");
    });
  }

  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetTab = btn.dataset.tab;
      switchTab(targetTab);
    });
  });

  if (goToCreateBtn) {
    goToCreateBtn.addEventListener("click", () => {
      resetCreateForm();
      switchTab("create-tab");
    });
  }

  if (cancelCreateBtn) {
    cancelCreateBtn.addEventListener("click", () => {
      resetCreateForm();
      switchTab("exams-tab");
    });
  }

  if (btnCancelEdit) {
    btnCancelEdit.addEventListener("click", () => {
      resetCreateForm();
      showToast("Edição cancelada", "info");
    });
  }
}

function switchTab(tabId) {
  // Permission gate based on user role
  if (currentUserProfile) {
    const role = currentUserProfile.role;
    if (role === "professor" && tabId !== "scanner-tab") {
      showToast("Acesso restrito. Professores têm acesso exclusivo à Correção de Provas.", "warning");
      tabId = "scanner-tab";
    } else if (tabId === "backup-tab" && role !== "admin") {
      showToast("Acesso restrito. Apenas administradores podem gerenciar backups do sistema.", "warning");
      tabId = "dashboard-tab";
    }
  }

  // If classroom full report view was active, close it
  const reportView = document.getElementById("classroom-report-view");
  if (reportView) {
    reportView.style.display = "none";
    reportView.classList.remove("active");
  }

  try {
    localStorage.removeItem("omr_active_subpage");
    localStorage.setItem("omr_active_tab", tabId);
  } catch (e) {}

  tabButtons.forEach(b => b.classList.toggle("active", b.dataset.tab === tabId));

  // Sincronizar botões da barra inferior mobile
  const mobileBottomBtns = document.querySelectorAll(".bottom-nav-btn[data-tab]");
  mobileBottomBtns.forEach(b => b.classList.toggle("active", b.dataset.tab === tabId));

  // Sincronizar itens do menu drawer lateral mobile
  const mobileDrawerItems = document.querySelectorAll(".mobile-drawer-item[data-tab]");
  mobileDrawerItems.forEach(b => b.classList.toggle("active", b.dataset.tab === tabId));

  // Fechar drawer lateral se estiver aberto
  if (typeof closeMobileMenu === "function") {
    closeMobileMenu();
  }

  tabContents.forEach(c => {
    c.style.display = ""; // Reset any inline display override
    c.classList.toggle("active", c.id === tabId);
  });

  if (tabId === "scanner-tab") {
    startCamera();
    setTimeout(checkOrientationAndAdjustCamera, 200);
  } else {
    deactivateLandscapeCamera();
    stopCamera();
    if (tabId === "exams-tab") {
      loadExams(false);
    } else if (tabId === "schools-tab") {
      loadSchools();
    } else if (tabId === "dashboard-tab") {
      loadDashboardData();
    } else if (tabId === "users-tab") {
      loadUsers();
    } else if (tabId === "backup-tab") {
      loadBackupStats();
    }
  }

  // Update Gestão dropdown active indicator
  const adminBtn = document.getElementById("btn-admin-dropdown");
  if (adminBtn) {
    adminBtn.classList.toggle("active", tabId === "users-tab" || tabId === "backup-tab");
  }
  const itemUsers = document.getElementById("menu-item-users");
  const itemBackup = document.getElementById("menu-item-backup");
  if (itemUsers) itemUsers.classList.toggle("active", tabId === "users-tab");
  if (itemBackup) itemBackup.classList.toggle("active", tabId === "backup-tab");
}

// --- Toast System ---
function showToast(message, type = "normal") {
  toastEl.textContent = message;
  toastEl.className = `toast show ${type}`;
  setTimeout(() => {
    toastEl.classList.remove("show");
  }, 4000);
}

// --- Mobile & HTTPS Camera Helper ---
function checkHttpsEnvironment() {
  const isHttp = window.location.protocol === "http:";
  const isRemote = window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1";
  const banner = document.getElementById("https-helper-banner");
  const link = document.getElementById("open-https-link");
  
  if (isHttp && isRemote) {
    if (banner && link) {
      link.href = `https://${window.location.hostname}:8443`;
      banner.style.display = "flex";
    }
  }
}

// Call on startup
checkHttpsEnvironment();

function showMobileCameraFallback() {
  if (!cameraLoadingEl) return;
  const isRemote = window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1";
  const httpsUrl = `https://${window.location.hostname}:8443`;
  
  cameraLoadingEl.style.display = "flex";
  cameraLoadingEl.innerHTML = `
    <div class="mobile-cam-fallback-box">
      <div class="mobile-cam-icon">🔒</div>
      <div class="mobile-cam-title">Ativar Câmera no Navegador</div>
      <p class="mobile-cam-desc">Navegadores de celular exigem conexão segura para exibir a câmera ao vivo diretamente na tela:</p>
      <a href="${httpsUrl}" class="btn btn-primary btn-lg" style="margin-top: 0.6rem; text-decoration: none; display: inline-flex; align-items: center; gap: 0.5rem; font-weight: 700;">
        <span>Toque aqui para abrir em HTTPS (:8443)</span>
      </a>
      <p style="font-size: 0.72rem; color: #94a3b8; margin-top: 0.6rem;">(No primeiro acesso, clique em "Avançado" ➔ "Continuar" para permitir o vídeo).</p>
    </div>
  `;
}

// --- Camera Management ---
async function startCamera() {
  // If browser mediaDevices is not accessible (e.g. mobile HTTP), offer HTTPS
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    showMobileCameraFallback();
    return;
  }

  cameraLoadingEl.style.display = "flex";
  cameraLoadingEl.innerHTML = '<div class="spinner"></div><span>Iniciando câmera...</span>';

  if (cameraStream) {
    stopCamera();
  }

  // Try optimal mobile rear camera, then relaxed constraints
  const constraintOptions = [
    { video: { facingMode: { ideal: currentFacingMode }, width: { ideal: 1920 }, height: { ideal: 1080 } }, audio: false },
    { video: { facingMode: { ideal: currentFacingMode } }, audio: false },
    { video: true, audio: false }
  ];

  let stream = null;
  for (const c of constraintOptions) {
    try {
      stream = await navigator.mediaDevices.getUserMedia(c);
      if (stream) break;
    } catch (err) {
      console.warn("Retrying camera constraints:", err);
    }
  }

  if (stream) {
    cameraStream = stream;
    videoEl.srcObject = cameraStream;
    videoEl.setAttribute("playsinline", "true");
    
    videoEl.onloadedmetadata = () => {
      cameraLoadingEl.style.display = "none";
      videoEl.play();
    };
  } else {
    showMobileCameraFallback();
  }
}

function stopCamera() {
  if (cameraStream) {
    cameraStream.getTracks().forEach(track => track.stop());
    cameraStream = null;
  }
}

// Switch front/back camera
if (switchCameraBtn) {
  switchCameraBtn.addEventListener("click", () => {
    currentFacingMode = (currentFacingMode === "environment") ? "user" : "environment";
    startCamera();
  });
}

if (btnTriggerGallery && fileInput) {
  btnTriggerGallery.addEventListener("click", () => fileInput.click());
}

// --- Mobile Landscape Fullscreen Camera System ---
let isLandscapeCameraActive = false;
let userDismissedLandscapeSession = false;
let cameraTorchEnabled = false;

function isMobileDevice() {
  const ua = navigator.userAgent || "";
  const isMobileUA = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(ua);
  const isTouchDevice = (('ontouchstart' in window) || (navigator.maxTouchPoints > 0) || window.matchMedia("(pointer: coarse)").matches);
  const isSmallScreen = Math.min(window.innerWidth, window.innerHeight) <= 900;
  return (isMobileUA || isTouchDevice) && isSmallScreen;
}

function isLandscapeOrientation() {
  if (window.screen && window.screen.orientation && window.screen.orientation.type) {
    if (window.screen.orientation.type.includes("landscape")) return true;
    if (window.screen.orientation.type.includes("portrait")) return false;
  }
  if (typeof window.orientation !== "undefined" && window.orientation !== null) {
    if (Math.abs(window.orientation) === 90) return true;
    if (window.orientation === 0 || window.orientation === 180) return false;
  }
  if (window.matchMedia && window.matchMedia("(orientation: landscape)").matches) {
    return true;
  }
  return window.innerWidth > window.innerHeight;
}

function getCurrentActiveTabId() {
  const activeContent = document.querySelector(".tab-content.active");
  return activeContent ? activeContent.id : (localStorage.getItem("omr_active_tab") || "dashboard-tab");
}

function updateLandscapeExamTitle() {
  const titleEl = document.getElementById("landscape-hud-exam-title");
  if (!titleEl) return;
  if (!activeExamId || activeExamId === "AUTO") {
    titleEl.textContent = "Identificação Automática (QR Code)";
  } else {
    const exam = examsList.find(e => String(e.id) === String(activeExamId));
    titleEl.textContent = exam ? (exam.title || "Simulado") : "Simulado Selecionado";
  }
}

async function activateLandscapeCamera() {
  if (isLandscapeCameraActive) return;
  const currentTab = getCurrentActiveTabId();
  if (currentTab !== "scanner-tab") return;

  isLandscapeCameraActive = true;
  document.body.classList.add("mobile-landscape-camera-active");
  updateLandscapeExamTitle();

  // Garante que o stream da câmera está ativo
  if (!cameraStream || !videoEl.srcObject) {
    startCamera();
  }

  // Tenta tela cheia nativa do navegador para esconder barras do sistema
  try {
    const el = document.documentElement;
    if (el.requestFullscreen && !document.fullscreenElement) {
      el.requestFullscreen().catch(() => {});
    } else if (el.webkitRequestFullscreen && !document.webkitFullscreenElement) {
      el.webkitRequestFullscreen().catch(() => {});
    }
  } catch (e) {}

  if (navigator.vibrate) {
    navigator.vibrate([30]);
  }
}

function deactivateLandscapeCamera() {
  if (!isLandscapeCameraActive && !document.body.classList.contains("mobile-landscape-camera-active")) {
    return;
  }
  isLandscapeCameraActive = false;
  document.body.classList.remove("mobile-landscape-camera-active");

  // Desliga lanterna caso tenha ficado acesa
  if (cameraTorchEnabled) {
    toggleCameraTorch(false);
  }

  // Sai de tela cheia nativa se estiver ativa
  try {
    if (document.fullscreenElement && document.exitFullscreen) {
      document.exitFullscreen().catch(() => {});
    } else if (document.webkitFullscreenElement && document.webkitExitFullscreen) {
      document.webkitExitFullscreen().catch(() => {});
    }
  } catch (e) {}
}

async function toggleCameraTorch(forceState = null) {
  const torchBtn = document.getElementById("landscape-torch-btn");
  if (!cameraStream) {
    showToast("Câmera não iniciada.", "warning");
    return;
  }
  const track = cameraStream.getVideoTracks()[0];
  if (!track) return;

  const targetState = (forceState !== null) ? forceState : !cameraTorchEnabled;

  try {
    const capabilities = track.getCapabilities ? track.getCapabilities() : {};
    if (!capabilities.torch) {
      if (forceState === null) {
        showToast("Lanterna não disponível neste dispositivo.", "info");
      }
      return;
    }

    await track.applyConstraints({
      advanced: [{ torch: targetState }]
    });
    cameraTorchEnabled = targetState;
    if (torchBtn) {
      torchBtn.classList.toggle("active", cameraTorchEnabled);
    }
  } catch (err) {
    console.warn("Erro ao controlar lanterna:", err);
  }
}

function checkOrientationAndAdjustCamera() {
  const onMobile = isMobileDevice();
  const currentTab = getCurrentActiveTabId();
  const onScanner = (currentTab === "scanner-tab");
  const inLandscape = isLandscapeOrientation();

  if (onMobile && onScanner && inLandscape) {
    if (!userDismissedLandscapeSession) {
      activateLandscapeCamera();
    }
  } else {
    // Ao voltar para orientação vertical, permite reativação automática na próxima rotação
    if (!inLandscape) {
      userDismissedLandscapeSession = false;
    }
    if (isLandscapeCameraActive) {
      deactivateLandscapeCamera();
    }
  }
}

function initLandscapeCameraListeners() {
  if (window.screen && window.screen.orientation) {
    window.screen.orientation.addEventListener("change", checkOrientationAndAdjustCamera);
  }
  window.addEventListener("orientationchange", () => {
    setTimeout(checkOrientationAndAdjustCamera, 150);
  });
  window.addEventListener("resize", () => {
    setTimeout(checkOrientationAndAdjustCamera, 100);
  });

  // Gatilho de Disparo / Correção em Paisagem
  const landscapeShutterBtn = document.getElementById("landscape-shutter-btn");
  if (landscapeShutterBtn) {
    landscapeShutterBtn.addEventListener("click", async (e) => {
      e.preventDefault();
      e.stopPropagation();

      if (navigator.vibrate) {
        navigator.vibrate([45]);
      }

      landscapeShutterBtn.classList.add("processing");
      try {
        if (captureBtn) {
          captureBtn.click();
        }
      } finally {
        setTimeout(() => {
          landscapeShutterBtn.classList.remove("processing");
        }, 1200);
      }
    });
  }

  // Botão de Lanterna
  const torchBtn = document.getElementById("landscape-torch-btn");
  if (torchBtn) {
    torchBtn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      toggleCameraTorch();
    });
  }

  // Botão de Alternar Câmera em Paisagem
  const landscapeSwitchCamBtn = document.getElementById("landscape-switch-cam-btn");
  if (landscapeSwitchCamBtn) {
    landscapeSwitchCamBtn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (switchCameraBtn) {
        switchCameraBtn.click();
      }
    });
  }

  // Botão de Galeria / Arquivo em Paisagem
  const landscapeGalleryBtn = document.getElementById("landscape-gallery-btn");
  if (landscapeGalleryBtn) {
    landscapeGalleryBtn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (fileInput) {
        fileInput.click();
      }
    });
  }

  // Botão de Sair do Modo Paisagem (✕)
  const landscapeExitBtn = document.getElementById("landscape-exit-btn");
  if (landscapeExitBtn) {
    landscapeExitBtn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      userDismissedLandscapeSession = true;
      deactivateLandscapeCamera();
      showToast("Modo horizontal pausado. Gire o celular ou selecione Corrigir para reabrir.", "info");
    });
  }
}

// --- Grading & Capture ---
captureBtn.addEventListener("click", async () => {
  if (!activeExamId) {
    showToast("Selecione uma prova antes de corrigir.", "error");
    return;
  }

  // Capture directly from the in-browser live video stream
  if (videoEl.videoWidth > 0 && cameraStream) {
    canvasEl.width = videoEl.videoWidth;
    canvasEl.height = videoEl.videoHeight;
    const ctx = canvasEl.getContext("2d");
    ctx.drawImage(videoEl, 0, 0, canvasEl.width, canvasEl.height);

    canvasEl.toBlob(async (blob) => {
      if (blob) {
        await processGradingUpload(blob);
      }
    }, "image/jpeg", 0.92);
    return;
  }

  // If camera stream is not active yet, start it
  startCamera();
});

// Listener for file input (gallery / file picker)
if (fileInput) {
  fileInput.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!activeExamId) {
      showToast("Por favor, selecione um simulado antes de enviar.", "error");
      return;
    }

    await processGradingUpload(file);
    fileInput.value = "";
  });
}

// Listener for native camera input (mobile rear camera capture)
if (nativeCameraInput) {
  nativeCameraInput.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!activeExamId) {
      showToast("Por favor, selecione um simulado antes de enviar.", "error");
      return;
    }

    showToast("Foto capturada! Processando correção...", "info");
    await processGradingUpload(file);
    nativeCameraInput.value = "";
  });
}

/**
 * Otimiza e comprime a foto capturada no cliente antes do upload.
 * Fotos mobile de 12MP a 48MP (5MB a 15MB) são reduzidas proporcionalmente
 * para até 1920px com JPEG 86%, pesando apenas ~350KB-450KB.
 * Isso reduz o tempo de transferência via rede móvel em até 95%
 * sem nenhuma perda na detecção de ArUco, QR codes ou bolhas.
 */
async function compressImageForOMR(fileOrBlob, maxDimension = 1920, quality = 0.86) {
  // Se já for um blob pequeno (< 500KB), não precisa reprocessar
  if (fileOrBlob.size && fileOrBlob.size < 500 * 1024) {
    return fileOrBlob;
  }

  try {
    let bitmapOrImg;
    let width, height;

    if (window.createImageBitmap) {
      try {
        bitmapOrImg = await createImageBitmap(fileOrBlob);
        width = bitmapOrImg.width;
        height = bitmapOrImg.height;
      } catch (e) {
        bitmapOrImg = null;
      }
    }

    if (!bitmapOrImg) {
      // Fallback para elemento Image
      bitmapOrImg = await new Promise((resolve, reject) => {
        const img = new Image();
        const url = URL.createObjectURL(fileOrBlob);
        img.onload = () => {
          URL.revokeObjectURL(url);
          resolve(img);
        };
        img.onerror = () => {
          URL.revokeObjectURL(url);
          reject(new Error("Falha ao carregar imagem para compressão"));
        };
        img.src = url;
      });
      width = bitmapOrImg.naturalWidth || bitmapOrImg.width;
      height = bitmapOrImg.naturalHeight || bitmapOrImg.height;
    }

    // Se já estiver dentro das dimensões seguras e tamanho razoável, retorna o original
    if (width <= maxDimension && height <= maxDimension && fileOrBlob.size < 1.2 * 1024 * 1024) {
      if (bitmapOrImg.close) bitmapOrImg.close();
      return fileOrBlob;
    }

    // Calcular proporção mantendo aspect ratio
    let targetWidth = width;
    let targetHeight = height;
    if (width > maxDimension || height > maxDimension) {
      if (width > height) {
        targetWidth = maxDimension;
        targetHeight = Math.round((height * maxDimension) / width);
      } else {
        targetHeight = maxDimension;
        targetWidth = Math.round((width * maxDimension) / height);
      }
    }

    const canvas = document.createElement("canvas");
    canvas.width = targetWidth;
    canvas.height = targetHeight;
    const ctx = canvas.getContext("2d", { alpha: false });
    
    // Configurar interpolação de alta qualidade
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = "high";
    ctx.drawImage(bitmapOrImg, 0, 0, targetWidth, targetHeight);

    if (bitmapOrImg.close) {
      bitmapOrImg.close();
    }

    const compressedBlob = await new Promise((resolve) => {
      canvas.toBlob(
        (blob) => resolve(blob || fileOrBlob),
        "image/jpeg",
        quality
      );
    });

    console.info(`[OMR Speedup] Imagem otimizada: ${(fileOrBlob.size / 1024).toFixed(0)}KB -> ${(compressedBlob.size / 1024).toFixed(0)}KB (${targetWidth}x${targetHeight})`);
    return compressedBlob;
  } catch (err) {
    console.warn("[OMR Speedup] Fallback para arquivo original devido a erro na compressão:", err);
    return fileOrBlob;
  }
}

async function processGradingUpload(fileOrBlob) {
  const originalBtnText = captureBtn.innerHTML;
  captureBtn.disabled = true;
  captureBtn.innerHTML = '<div class="spinner"></div><span>Otimizando imagem...</span>';

  let uploadPayload = fileOrBlob;
  try {
    uploadPayload = await compressImageForOMR(fileOrBlob);
  } catch (err) {
    console.warn("Compressão ignorada:", err);
  }

  captureBtn.innerHTML = '<div class="spinner"></div><span>Processando OMR...</span>';

  const formData = new FormData();
  formData.append("file", uploadPayload, "scan.jpg");
  if (activeExamId && activeExamId !== "AUTO") {
    formData.append("exam_id", activeExamId);
  } else {
    formData.append("exam_id", "AUTO");
  }
  
  const studentName = studentNameInput ? studentNameInput.value.trim() : "";
  if (studentName) {
    formData.append("student_name", studentName);
  }

  try {
    const res = await fetch("/api/grade", {
      method: "POST",
      body: formData
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || "Erro ao processar folha de respostas.");
    }

    playSuccessSound();
    showToast("Leitura concluída! Revise as respostas e confirme abaixo para registrar a prova.", "info");
    displayGradingResult(data);
  } catch (err) {
    console.error(err);
    showToast(err.message, "error");
  } finally {
    captureBtn.disabled = false;
    captureBtn.innerHTML = originalBtnText;
  }
}

// Display results in UI
function displayGradingResult(result) {
  // Requisito 2: Sai do modo paisagem em tela cheia para mostrar o raio-x completo e nota a cada folha
  deactivateLandscapeCamera();

  // Garante que a aba do Raio-X visual esteja selecionada e exibida por padrão
  if (viewXrayBtn && xrayContainer) {
    viewXrayBtn.classList.add("active");
    if (viewListBtn) viewListBtn.classList.remove("active");
    xrayContainer.style.display = "block";
    if (tableContainer) tableContainer.style.display = "none";
  }

  currentGradingResult = result;
  resultPlaceholder.style.display = "none";
  resultDisplay.style.display = "block";

  resScoreEl.textContent = result.score.toFixed(1);
  resMaxScoreEl.textContent = `/ ${result.max_score.toFixed(1)}`;
  resStudentNameEl.textContent = result.student_name || "Aluno";

  // Update status badge
  const studentStatusBadge = document.getElementById("res-student-status-badge");
  if (studentStatusBadge) {
    if (result.student_name && result.student_name !== "Aluno" && result.student_name !== "Aluno Não Identificado") {
      studentStatusBadge.textContent = "Aluno Vinculado";
      studentStatusBadge.className = "student-status-badge status-identified";
    } else {
      studentStatusBadge.textContent = "Sem Vínculo QR";
      studentStatusBadge.className = "student-status-badge status-unidentified";
    }
  }

  // Update full identification metadata card (Simulado, Escola, Turma, Matrícula)
  const metaCard = document.getElementById("res-student-meta-card");
  const examTag = document.getElementById("res-exam-tag");
  const schoolTag = document.getElementById("res-school-tag");
  const classTag = document.getElementById("res-classroom-tag");
  const regTag = document.getElementById("res-reg-tag");

  if (examTag) examTag.textContent = result.exam_title || "Simulado";
  if (schoolTag) schoolTag.textContent = result.school_name || "Escola Padrão";
  if (classTag) classTag.textContent = result.classroom_name || "Turma Geral";
  if (regTag) regTag.textContent = result.registration || "—";

  if (metaCard) {
    metaCard.style.display = "block";
  }

  // Show Professor Confirmation Card
  const confirmBanner = document.getElementById("confirmation-banner");
  const confirmExamTitle = document.getElementById("confirm-exam-title");
  const confirmSubtext = document.getElementById("confirm-subtext");
  if (confirmBanner) {
    confirmBanner.style.display = "block";
    if (confirmExamTitle) {
      confirmExamTitle.textContent = `${result.student_name || "Aluno"} • ${result.exam_title || "Simulado"}`;
    }
    if (confirmSubtext) {
      const parts = [];
      if (result.school_name) parts.push(result.school_name);
      if (result.classroom_name) parts.push(`Turma: ${result.classroom_name}`);
      confirmSubtext.textContent = parts.length > 0 ? parts.join(" • ") : "Revise os dados apurados e confirme o registro no boletim escolar.";
    }
  }

  resCorrectBadge.textContent = `${result.correct_count} Acertos`;
  resWrongBadge.textContent = `${result.wrong_count} Erros`;
  resBlankBadge.textContent = `${result.blank_count} Em Branco`;

  const percent = result.percentage || 0;
  resProgressBar.style.width = `${percent}%`;
  resProgressBar.style.backgroundColor = percent >= 60 ? "var(--success)" : "var(--danger)";

  // Set annotated X-Ray image
  resOverlayImg.src = `${result.overlay_image_url}?t=${Date.now()}`;

  // Auto scroll to result smoothly on mobile devices
  setTimeout(() => {
    resultDisplay.scrollIntoView({ behavior: "smooth", block: "start" });
  }, 100);

  // Populate questions table
  resQuestionsTbody.innerHTML = "";
  result.results_detail.forEach(item => {
    const tr = document.createElement("tr");

    let statusBadge = "";
    if (item.is_correct) {
      statusBadge = '<span class="badge-status" style="background: var(--success-light); color: var(--success);">ACERTO</span>';
    } else if (item.chosen === "BLANK") {
      statusBadge = '<span class="badge-status" style="background: var(--warning-light); color: var(--warning);">EM BRANCO</span>';
    } else if (item.chosen === "DOUBLE") {
      statusBadge = '<span class="badge-status" style="background: var(--warning-light); color: var(--warning);">DUPLA</span>';
    } else {
      statusBadge = '<span class="badge-status" style="background: var(--danger-light); color: var(--danger);">ERRO</span>';
    }

    tr.innerHTML = `
      <td><strong>${String(item.question).padStart(2, '0')}</strong></td>
      <td><span style="font-weight: 700; color: ${item.is_correct ? 'var(--success)' : 'var(--danger)'}">${item.chosen}</span></td>
      <td><strong>${item.correct}</strong></td>
      <td>${statusBadge}</td>
      <td>+${item.points}</td>
    `;
    resQuestionsTbody.appendChild(tr);
  });
}

// Toggle between X-Ray image and Table List
viewXrayBtn.addEventListener("click", () => {
  viewXrayBtn.classList.add("active");
  viewListBtn.classList.remove("active");
  xrayContainer.style.display = "block";
  tableContainer.style.display = "none";
});

viewListBtn.addEventListener("click", () => {
  viewListBtn.classList.add("active");
  viewXrayBtn.classList.remove("active");
  xrayContainer.style.display = "none";
  tableContainer.style.display = "block";
});

// Discard / Delete current scan result
const btnDeleteCurrentResult = document.getElementById("btn-delete-current-result");
if (btnDeleteCurrentResult) {
  btnDeleteCurrentResult.addEventListener("click", async () => {
    if (currentUserProfile && currentUserProfile.role !== "admin") {
      showToast("Apenas o Administrador SEMED tem permissão para excluir correções.", "warning");
      return;
    }
    if (!currentGradingResult || !currentGradingResult.id) {
      showToast("Nenhuma correção ativa para excluir.", "warning");
      return;
    }
    const stName = currentGradingResult.student_name || "este aluno";
    const conf = confirm(`Deseja realmente excluir a correção de "${stName}"?\n\nOs arquivos de imagem e a nota calculada serão removidos permanentemente.`);
    if (!conf) return;

    try {
      const res = await fetch(`/api/submissions/${currentGradingResult.id}`, {
        method: "DELETE",
        headers: { ...getAuthHeaders() }
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Erro ao excluir correção.");
      }
      showToast("Correção excluída com sucesso!", "success");
      currentGradingResult = null;
      resultDisplay.style.display = "none";
      resultPlaceholder.style.display = "flex";
      loadExams(false);
    } catch (err) {
      console.error(err);
      showToast(err.message, "error");
    }
  });
}

// Professor Confirmation Card Buttons
const btnConfirmGrade = document.getElementById("btn-confirm-grade");
const btnRejectGrade = document.getElementById("btn-reject-grade");

if (btnConfirmGrade) {
  btnConfirmGrade.addEventListener("click", async () => {
    if (!currentGradingResult) return;
    const stName = currentGradingResult.student_name || "Aluno";
    const scoreVal = currentGradingResult.score;

    const originalBtnHtml = btnConfirmGrade.innerHTML;
    btnConfirmGrade.disabled = true;
    btnConfirmGrade.innerHTML = '<div class="spinner"></div><span>Gravando...</span>';

    try {
      const res = await fetch("/api/grade/confirm", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders()
        },
        body: JSON.stringify(currentGradingResult)
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Erro ao registrar confirmação da prova.");
      }

      playSuccessSound();
      showToast(`✓ Prova de ${stName} (${scoreVal} pts) confirmada e registrada com sucesso!`, "success");
      
      // Smooth reset for next sheet
      const confirmBanner = document.getElementById("confirmation-banner");
      if (confirmBanner) confirmBanner.style.display = "none";
      currentGradingResult = null;
      resultDisplay.style.display = "none";
      resultPlaceholder.style.display = "flex";
      
      // Scroll back to camera view
      if (videoEl) videoEl.scrollIntoView({ behavior: "smooth", block: "center" });

      // Se o usuário mantiver o celular na horizontal para a próxima folha, reabre modo tela cheia
      setTimeout(checkOrientationAndAdjustCamera, 350);

      // Sincronizar listas e dashboard agora que a prova foi formalmente confirmada
      loadExams(false);
      if (typeof loadDashboardData === "function") {
        loadDashboardData();
      }
    } catch (err) {
      console.error(err);
      showToast(err.message, "error");
    } finally {
      btnConfirmGrade.disabled = false;
      btnConfirmGrade.innerHTML = originalBtnHtml;
    }
  });
}

if (btnRejectGrade) {
  btnRejectGrade.addEventListener("click", async () => {
    if (!currentGradingResult) return;
    try {
      await fetch("/api/grade/discard", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders()
        },
        body: JSON.stringify(currentGradingResult)
      });
      showToast("Leitura descartada. A prova não foi registrada.", "info");
    } catch (err) {
      console.error(err);
    }
    const confirmBanner = document.getElementById("confirmation-banner");
    if (confirmBanner) confirmBanner.style.display = "none";
    currentGradingResult = null;
    resultDisplay.style.display = "none";
    resultPlaceholder.style.display = "flex";
    if (videoEl) videoEl.scrollIntoView({ behavior: "smooth", block: "center" });
    setTimeout(checkOrientationAndAdjustCamera, 350);
  });
}

// --- Exams Management ---
async function loadExams(selectFirst = true) {
  try {
    const res = await fetch("/api/exams");
    examsList = await res.json();

    // Populate active exam selector in scanner tab if present
    if (activeExamSelect) {
      activeExamSelect.innerHTML = "";
      if (examsList.length === 0) {
        activeExamSelect.innerHTML = '<option value="">Nenhum simulado cadastrado</option>';
        activeExamId = "AUTO";
      } else {
        // Add AUTO mode as the primary and default option
        const autoOpt = document.createElement("option");
        autoOpt.value = "AUTO";
        autoOpt.textContent = "🔍 Reconhecimento Automático via QR Code (Recomendado)";
        activeExamSelect.appendChild(autoOpt);

        examsList.forEach(ex => {
          const opt = document.createElement("option");
          opt.value = ex.id;
          opt.textContent = `${ex.title} (${ex.num_questions}Q)`;
          activeExamSelect.appendChild(opt);
        });

        if (selectFirst && (!activeExamId || activeExamId === "AUTO")) {
          activeExamId = "AUTO";
        }
        activeExamSelect.value = activeExamId || "AUTO";
      }
    }

    // Populate Exams Grid in exams tab
    renderExamsGrid();
    if (typeof populateDashboardExamFilter === "function") {
      populateDashboardExamFilter();
    }
  } catch (err) {
    console.error("Erro ao carregar simulados:", err);
  }
}

if (activeExamSelect) {
  activeExamSelect.addEventListener("change", (e) => {
    activeExamId = e.target.value;
  });
}

// Smart Search Helpers (accent-insensitive, ordinal-insensitive, multi-token)
function normalizeSearchText(str) {
  if (str == null) return "";
  return String(str)
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[ºª°]/g, "")
    .replace(/[^\w\s-]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function matchesSearchTokens(searchableFields, query) {
  const normQuery = normalizeSearchText(query);
  if (!normQuery) return true;

  const tokens = normQuery.split(" ").filter(t => t.length > 0);
  if (tokens.length === 0) return true;

  const haystack = Array.isArray(searchableFields)
    ? searchableFields.map(f => normalizeSearchText(f)).join(" ")
    : normalizeSearchText(searchableFields);

  return tokens.every(tok => haystack.includes(tok));
}

function highlightSearchTokens(rawText, query) {
  if (!rawText) return "";
  const safeText = escapeHtml(rawText);
  const normQuery = normalizeSearchText(query);
  if (!normQuery) return safeText;

  const tokens = normQuery.split(" ").filter(t => t.length >= 2);
  if (tokens.length === 0) return safeText;

  try {
    const escaped = tokens.map(t => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|");
    const regex = new RegExp(`(${escaped})`, "gi");
    return safeText.replace(regex, `<mark class="search-match-mark">$1</mark>`);
  } catch (e) {
    return safeText;
  }
}

function renderExamsGrid(filterTerm = "") {
  const container = document.getElementById("exams-list") || document.getElementById("exams-tbody") || document.getElementById("exams-grid");
  if (!container) return;

  const examsSearchInput = document.getElementById("exams-search-input");
  const examsSearchClear = document.getElementById("exams-search-clear");
  const countBadge = document.getElementById("exams-count-badge");
  const rawTerm = (filterTerm !== undefined && filterTerm !== "" ? filterTerm : (examsSearchInput ? examsSearchInput.value : "")).trim();

  if (examsSearchClear) {
    examsSearchClear.style.display = rawTerm ? "flex" : "none";
  }

  if (!examsList || examsList.length === 0) {
    if (countBadge) countBadge.style.display = "none";
    container.innerHTML = `
      <div style="text-align: center; padding: 2.5rem 1rem; color: var(--text-secondary);">
        <p style="font-size: 0.95rem; font-weight: 600; color: #1e293b; margin-bottom: 0.5rem;">Nenhuma prova ou simulado cadastrado.</p>
        <button class="btn btn-primary btn-sm" onclick="resetCreateForm(); switchTab('create-tab')">Cadastrar Nova Prova</button>
      </div>
    `;
    return;
  }

  const filteredExams = rawTerm
    ? examsList.filter(ex => {
        const subCount = ex.submissions_count || 0;
        const subText = subCount > 0 ? `${subCount} corrigidas com correcao` : "sem correcao pendente nenhuma correcao";
        const questText = `${ex.num_questions || 0} questoes ${ex.num_alternatives ? 'alternativas A-' + String.fromCharCode(64 + ex.num_alternatives) : ''}`;
        
        return matchesSearchTokens([
          ex.title || "",
          ex.subtitle || "",
          questText,
          subText
        ], rawTerm);
      })
    : examsList;

  // Atualiza badge de contagem de simulados
  if (countBadge) {
    if (rawTerm) {
      countBadge.style.display = "inline-flex";
      countBadge.innerHTML = `<span><strong>${filteredExams.length}</strong> de ${examsList.length} simulado(s)</span>`;
    } else {
      countBadge.style.display = "none";
    }
  }

  if (filteredExams.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 2.5rem 1rem; color: var(--text-secondary); background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 8px;">
        <div style="width: 44px; height: 44px; border-radius: 50%; background: #e2e8f0; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 0.65rem; color: #64748b;">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        </div>
        <p style="font-size: 0.95rem; font-weight: 700; color: #1e293b; margin-bottom: 0.3rem;">Nenhum simulado encontrado para "${escapeHtml(rawTerm)}"</p>
        <p style="font-size: 0.82rem; color: var(--text-secondary); margin-bottom: 0.85rem;">Tente pesquisar por outros termos, número de questões ou limpe a busca.</p>
        <button type="button" class="btn btn-secondary btn-sm" onclick="clearExamsSearch()">Limpar busca</button>
      </div>
    `;
    return;
  }

  container.innerHTML = "";
  filteredExams.forEach(ex => {
    const row = document.createElement("div");
    row.className = "exam-row";

    const subCount = ex.submissions_count || 0;
    const subHtml = subCount > 0 
      ? `<span class="cl-student-toggle-btn" style="cursor: default; background: #f0fdf4; border-color: #bbf7d0; color: #166534;" title="${subCount} provas corrigidas"><strong>${subCount}</strong> ${subCount === 1 ? 'corrigida' : 'corrigidas'}</span>` 
      : `<span class="cl-no-exams">Nenhuma correção</span>`;

    const titleHtml = rawTerm ? highlightSearchTokens(ex.title, rawTerm) : escapeHtml(ex.title);
    const subTitleHtml = rawTerm ? highlightSearchTokens(ex.subtitle || "PROVA OFICIAL", rawTerm) : escapeHtml(ex.subtitle || "PROVA OFICIAL");

    row.innerHTML = `
      <div class="cl-col-main">
        <div class="cl-title-wrap">
          <strong class="cl-name">${titleHtml}</strong>
          <span class="cl-grade">${subTitleHtml}</span>
        </div>
      </div>

      <div class="cl-col-exams">
        <span class="cl-exam-chip">${ex.num_questions} Questões • Opções A-${String.fromCharCode(64 + ex.num_alternatives)}</span>
        ${ex.is_linked_to_school ? `
          <span class="cl-exam-chip" style="background-color: #eff6ff; color: #1e40af; border: 1px solid #bfdbfe; font-weight: 600;" title="Vinculado à(s) escola(s): ${(ex.linked_schools || []).map(s => s.name).join(', ')}">
            🏫 Vinculado (${(ex.linked_schools || []).length} escola${(ex.linked_schools || []).length > 1 ? 's' : ''})
          </span>
        ` : ''}
      </div>

      <div class="cl-col-students" style="justify-content: center;">
        ${subHtml}
      </div>

      <div class="cl-col-actions">
        <a href="/api/exams/${ex.id}/sheet.pdf?layout=single&filled=true" target="_blank" class="cl-action-btn cl-action-btn-primary" title="Baixar Gabarito Oficial preenchido com as respostas corretas (1 por folha)">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
          <span>PDF 1x</span>
        </a>
        <a href="/api/exams/${ex.id}/sheet.pdf?layout=double&filled=true" target="_blank" class="cl-action-btn cl-action-btn-secondary" style="color: #0284c7; border-color: #bae6fd; font-weight: 700;" title="Baixar Gabarito Oficial preenchido com as respostas corretas (2 por folha)">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="6" cy="6" r="3"></circle><circle cx="6" cy="18" r="3"></circle><line x1="20" y1="4" x2="8.12" y2="15.88"></line><line x1="14.47" y1="14.48" x2="20" y2="20"></line><line x1="8.12" y1="8.12" x2="12" y2="12"></line></svg>
          <span>Folha 2x</span>
        </a>
        <button type="button" class="cl-action-btn cl-action-btn-secondary edit-exam-btn" data-id="${ex.id}" title="Editar dados do gabarito">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
          <span>Editar</span>
        </button>
        ${currentUserProfile && currentUserProfile.role === "admin" ? `
        <button type="button" class="cl-action-btn cl-action-btn-danger delete-exam-btn" data-id="${ex.id}" 
          title="${ex.is_linked_to_school ? 'Bloqueado: gabarito vinculado a escola(s)' : 'Excluir simulado'}"
          ${ex.is_linked_to_school ? 'style="opacity: 0.55; cursor: not-allowed;"' : ''}>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
          <span>Excluir</span>
        </button>` : ''}
      </div>
    `;

    row.querySelector(".edit-exam-btn").addEventListener("click", () => {
      startEditingExam(ex.id);
    });

    const delExamBtn = row.querySelector(".delete-exam-btn");
    if (delExamBtn) {
      delExamBtn.addEventListener("click", async () => {
        if (currentUserProfile && currentUserProfile.role !== "admin") {
          showToast("Apenas o Administrador SEMED tem permissão para excluir simulados.", "warning");
          return;
        }

        // Validação: Só permitir excluir se NÃO estiver vinculado a nenhuma escola
        if (ex.is_linked_to_school && ex.linked_schools && ex.linked_schools.length > 0) {
          const nomes = ex.linked_schools.map(s => s.name).join(", ");
          showToast(`Não é permitido excluir: o gabarito "${ex.title}" está vinculado à(s) escola(s): ${nomes}. Desvincule-o das turmas na aba "Turmas" primeiro.`, "warning");
          return;
        }

        const confirmDelete = confirm(
          `Tem certeza que deseja excluir o gabarito "${ex.title}"?\n\n` +
          `ATENÇÃO: Esta ação é definitiva e removerá a folha de respostas gerada.`
        );
        if (!confirmDelete) return;

        try {
          const res = await fetch(`/api/exams/${ex.id}`, {
            method: "DELETE",
            headers: { ...getAuthHeaders() }
          });
          if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || "Erro ao excluir gabarito.");
          }
          showToast("Gabarito excluído com sucesso!", "success");
          if (activeExamId === ex.id) {
            activeExamId = null;
          }
          await loadExams(true);
        } catch (err) {
          console.error(err);
          showToast(err.message, "error");
        }
      });
    }

    container.appendChild(row);
  });
}

// --- Logo & Live Preview Management ---
let currentLogoBase64 = null;
const DEFAULT_LOGO_URL = "/static/assets/logo_lagoa_da_canoa.png";
let currentLogoSrc = DEFAULT_LOGO_URL;

const logoPreviewImg = document.getElementById("logo-preview-img");
const previewLogoImg = document.getElementById("preview-logo-img");
const examLogoFile = document.getElementById("exam-logo-file");
const btnUploadLogo = document.getElementById("btn-upload-logo");
const btnDefaultLogo = document.getElementById("btn-default-logo");
const btnRemoveLogo = document.getElementById("btn-remove-logo");

// Live Preview DOM Elements
const examTitleInput = document.getElementById("exam-title-input");
const examSubtitleInput = document.getElementById("exam-subtitle-input");
const examSchoolInput = document.getElementById("exam-school-input");
const examClassInput = document.getElementById("exam-class-input");
const examShiftInput = document.getElementById("exam-shift-input");

const previewTitleEl = document.getElementById("preview-title");
const previewSubEl = document.getElementById("preview-sub");
const previewSchoolEl = document.getElementById("preview-school");
const previewClassEl = document.getElementById("preview-class");
const previewShiftEl = document.getElementById("preview-shift");
const previewQuestionsGrid = document.getElementById("preview-questions-grid");

// Cor do Gabarito (Header & Question Table)
let currentSheetColor = "#244061";

function setSheetColor(color) {
  if (!color) color = "#244061";
  color = color.trim();
  if (!color.startsWith("#")) color = "#" + color;
  if (/^#[0-9A-Fa-f]{3}$/.test(color)) {
    color = `#${color[1]}${color[1]}${color[2]}${color[2]}${color[3]}${color[3]}`;
  } else if (!/^#[0-9A-Fa-f]{6}$/.test(color)) {
    color = "#244061";
  }
  currentSheetColor = color.toLowerCase();

  const picker = document.getElementById("exam-color-picker");
  const hexInput = document.getElementById("exam-color-input");
  const previewBox = document.getElementById("custom-color-preview-box");

  if (picker) picker.value = currentSheetColor;
  if (hexInput) hexInput.value = currentSheetColor.toUpperCase();
  if (previewBox) previewBox.style.backgroundColor = currentSheetColor;

  document.querySelectorAll(".color-pill").forEach(pill => {
    if (pill.getAttribute("data-color").toLowerCase() === currentSheetColor) {
      pill.classList.add("active");
    } else {
      pill.classList.remove("active");
    }
  });

  const mockupBanner = document.getElementById("mockup-banner") || document.querySelector(".mockup-banner");
  if (mockupBanner) {
    mockupBanner.style.backgroundColor = currentSheetColor;
  }
  document.querySelectorAll("#preview-questions-grid .th-item").forEach(th => {
    th.style.backgroundColor = currentSheetColor;
  });
}

function initColorPickerEventListeners() {
  document.querySelectorAll(".color-pill").forEach(pill => {
    pill.addEventListener("click", () => {
      const col = pill.getAttribute("data-color");
      if (col) setSheetColor(col);
    });
  });

  const picker = document.getElementById("exam-color-picker");
  if (picker) {
    picker.addEventListener("input", (e) => {
      if (e.target.value) setSheetColor(e.target.value);
    });
  }

  const hexInput = document.getElementById("exam-color-input");
  if (hexInput) {
    hexInput.addEventListener("input", (e) => {
      let val = e.target.value.trim();
      if (!val.startsWith("#") && val.length > 0) val = "#" + val;
      if (/^#[0-9A-Fa-f]{6}$/.test(val)) {
        setSheetColor(val);
      }
    });
    hexInput.addEventListener("blur", (e) => {
      let val = e.target.value.trim();
      if (!val.startsWith("#") && val.length > 0) val = "#" + val;
      if (/^#[0-9A-Fa-f]{6}$/.test(val)) {
        setSheetColor(val);
      } else {
        hexInput.value = currentSheetColor.toUpperCase();
      }
    });
  }
}

// Logo Handlers
if (btnUploadLogo && examLogoFile) {
  btnUploadLogo.addEventListener("click", () => examLogoFile.click());

  examLogoFile.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (ev) => {
      currentLogoBase64 = ev.target.result;
      currentLogoSrc = currentLogoBase64;
      if (logoPreviewImg) logoPreviewImg.src = currentLogoSrc;
      if (previewLogoImg) previewLogoImg.src = currentLogoSrc;
      showToast("Logo carregada com sucesso!", "success");
    };
    reader.readAsDataURL(file);
  });
}

if (btnDefaultLogo) {
  btnDefaultLogo.addEventListener("click", () => {
    currentLogoBase64 = null; // Backend uses default Lagoa da Canoa logo
    currentLogoSrc = DEFAULT_LOGO_URL;
    if (logoPreviewImg) logoPreviewImg.src = currentLogoSrc;
    if (previewLogoImg) previewLogoImg.src = currentLogoSrc;
    showToast("Logo de Lagoa da Canoa selecionada", "info");
  });
}

if (btnRemoveLogo) {
  btnRemoveLogo.addEventListener("click", () => {
    currentLogoBase64 = "NONE";
    currentLogoSrc = "";
    if (logoPreviewImg) logoPreviewImg.src = "";
    if (previewLogoImg) previewLogoImg.src = "";
    showToast("Logo removida", "info");
  });
}

// Live Update Preview Functions
function updateLiveSheetMockup() {
  if (previewTitleEl && examTitleInput) {
    previewTitleEl.textContent = (examTitleInput.value.trim() || "PROVA CANOA 2026 – AVALIAÇÃO").toUpperCase();
  }
  if (previewSubEl && examSubtitleInput) {
    previewSubEl.textContent = (examSubtitleInput.value.trim() || "2º ANO DO ENSINO FUNDAMENTAL").toUpperCase();
  }
  if (previewSchoolEl) {
    const sc = examSchoolInput ? examSchoolInput.value.trim() : "";
    previewSchoolEl.textContent = sc ? sc.toUpperCase() : "_________________________________________";
  }
  if (previewClassEl) {
    const cl = examClassInput ? examClassInput.value.trim() : "";
    previewClassEl.textContent = cl ? cl.toUpperCase() : "___________";
  }
  if (previewShiftEl) {
    const sh = examShiftInput ? examShiftInput.value.trim() : "";
    previewShiftEl.textContent = sh || "(  ) MANHÃ       (  ) TARDE";
  }

  const mockupBanner = document.getElementById("mockup-banner") || document.querySelector(".mockup-banner");
  if (mockupBanner) {
    mockupBanner.style.backgroundColor = currentSheetColor || "#244061";
  }

  // Update Questions Table Mockup
  renderPreviewQuestionsTable();
}

function renderPreviewQuestionsTable() {
  if (!previewQuestionsGrid) return;
  const numQ = parseInt(numQuestionsInput.value) || 20;
  const numOpts = parseInt(numOptionsSelect.value) || 4;
  const opts = ["A", "B", "C", "D", "E"].slice(0, numOpts);

  previewQuestionsGrid.innerHTML = "";
  
  // Show sample items in preview (5 per column) for a clean visual mockup
  const sampleCount = Math.min(numQ, 10);
  const cols = 2;
  const perCol = Math.ceil(sampleCount / cols);

  for (let c = 0; c < cols; c++) {
    const table = document.createElement("table");
    table.className = "mockup-q-col-table";

    // Table Header Row
    const thead = document.createElement("thead");
    const headerTr = document.createElement("tr");

    const thItem = document.createElement("th");
    thItem.className = "th-item";
    thItem.style.backgroundColor = currentSheetColor || "#244061";
    thItem.textContent = "ITEM";
    headerTr.appendChild(thItem);

    opts.forEach(opt => {
      const thOpt = document.createElement("th");
      thOpt.className = "th-opt";
      thOpt.textContent = opt;
      headerTr.appendChild(thOpt);
    });
    thead.appendChild(headerTr);
    table.appendChild(thead);

    // Table Body Rows
    const tbody = document.createElement("tbody");
    for (let r = 0; r < perCol; r++) {
      const qNum = c * perCol + r + 1;
      if (qNum > sampleCount) break;

      const tr = document.createElement("tr");

      // Item Cell
      const tdItem = document.createElement("td");
      tdItem.className = "td-item";
      tdItem.textContent = String(qNum).padStart(2, "0");
      tr.appendChild(tdItem);

      // Alternatives Cells
      opts.forEach(opt => {
        const tdAlt = document.createElement("td");
        tdAlt.className = "td-alt";
        const bubble = document.createElement("div");
        bubble.className = "mockup-bubble-dot";
        bubble.textContent = opt;
        tdAlt.appendChild(bubble);
        tr.appendChild(tdAlt);
      });

      tbody.appendChild(tr);
    }
    table.appendChild(tbody);
    previewQuestionsGrid.appendChild(table);
  }
}

// Attach Live Listeners
if (examTitleInput) examTitleInput.addEventListener("input", updateLiveSheetMockup);
if (examSubtitleInput) examSubtitleInput.addEventListener("input", updateLiveSheetMockup);
if (examSchoolInput) examSchoolInput.addEventListener("input", updateLiveSheetMockup);
if (examClassInput) examClassInput.addEventListener("input", updateLiveSheetMockup);
if (examShiftInput) examShiftInput.addEventListener("input", updateLiveSheetMockup);

// --- Create & Edit Exam Logic ---
function resetCreateForm() {
  editingExamId = null;
  createExamForm.reset();
  currentAnswerKeyDraft = {};
  currentLogoBase64 = null;
  currentLogoSrc = DEFAULT_LOGO_URL;
  if (logoPreviewImg) logoPreviewImg.src = currentLogoSrc;
  if (previewLogoImg) previewLogoImg.src = currentLogoSrc;

  if (editModeBanner) editModeBanner.style.display = "none";
  if (createCardTitle) createCardTitle.textContent = "Nova Prova";
  if (createCardDesc) createCardDesc.textContent = "";
  if (saveExamBtn) {
    saveExamBtn.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
        <polyline points="17 21 17 13 7 13 7 21"></polyline>
        <polyline points="7 3 7 8 15 8"></polyline>
      </svg>
      <span>Salvar Prova</span>
    `;
  }

  initAnswerKeyMatrix();
  setSheetColor("#244061");
  updateLiveSheetMockup();
}

async function startEditingExam(examId) {
  try {
    const res = await fetch(`/api/exams/${examId}`, {
      headers: { ...getAuthHeaders() }
    });
    if (!res.ok) throw new Error("Não foi possível carregar os dados.");
    const exam = await res.json();

    editingExamId = exam.id;

    // Fill form fields
    if (examTitleInput) examTitleInput.value = exam.title || "";
    if (examSubtitleInput) examSubtitleInput.value = exam.subtitle || "";
    if (examSchoolInput) examSchoolInput.value = exam.school_name || "";
    if (examClassInput) examClassInput.value = exam.classroom || "";
    if (examShiftInput) examShiftInput.value = exam.shift || "(  ) MANHÃ       (  ) TARDE";
    if (numQuestionsInput) numQuestionsInput.value = exam.num_questions || 20;
    if (numOptionsSelect) numOptionsSelect.value = exam.num_alternatives || 4;

    const ptsInput = document.getElementById("exam-points-input");
    if (ptsInput) ptsInput.value = exam.points_per_question || 1.0;

    // Set answer key & color
    currentAnswerKeyDraft = exam.answer_key || {};
    setSheetColor(exam.header_color || "#244061");

    // Update UI for Edit Mode
    if (createCardTitle) createCardTitle.textContent = "Editar Prova";
    if (createCardDesc) createCardDesc.textContent = "";
    if (editModeBanner) editModeBanner.style.display = "flex";
    if (editExamTitleSpan) editExamTitleSpan.textContent = exam.title;
    if (saveExamBtn) {
      saveExamBtn.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
          <polyline points="17 21 17 13 7 13 7 21"></polyline>
          <polyline points="7 3 7 8 15 8"></polyline>
        </svg>
        <span>Salvar Alterações</span>
      `;
    }

    initAnswerKeyMatrix();
    updateLiveSheetMockup();

    // Switch to create tab
    switchTab("create-tab");
    showToast(`Editando simulado: ${exam.title}`, "info");
  } catch (err) {
    showToast(err.message, "error");
  }
}

// --- Create Exam Matrix Generator ---
function initAnswerKeyMatrix() {
  const numQ = parseInt(numQuestionsInput.value) || 20;
  const numOpts = parseInt(numOptionsSelect.value) || 4;

  matrixContainer.innerHTML = "";
  const opts = ["A", "B", "C", "D", "E"].slice(0, numOpts);

  // Layout em colunas idêntico ao gabarito impresso (ex: 20 questões -> 2 colunas verticais)
  let cols = 1;
  let questionsPerCol = numQ;
  if (numQ <= 12) {
    cols = 1;
    questionsPerCol = numQ;
  } else if (numQ <= 24) {
    cols = 2;
    questionsPerCol = 12;
  } else if (numQ <= 36) {
    cols = 3;
    questionsPerCol = 12;
  } else if (numQ <= 48) {
    cols = 4;
    questionsPerCol = 12;
  } else {
    cols = Math.min(5, Math.ceil(numQ / 12));
    questionsPerCol = Math.ceil(numQ / cols);
  }

  for (let c = 0; c < cols; c++) {
    const startQ = c * questionsPerCol + 1;
    if (startQ > numQ) break;

    const colCard = document.createElement("div");
    colCard.className = "key-col-card";

    const table = document.createElement("table");
    table.className = "key-col-table";

    // Cabeçalho da coluna: ITEM | A | B | C | D
    const thead = document.createElement("thead");
    const headerTr = document.createElement("tr");

    const thItem = document.createElement("th");
    thItem.className = "key-th-item";
    thItem.textContent = "ITEM";
    headerTr.appendChild(thItem);

    opts.forEach(letter => {
      const thOpt = document.createElement("th");
      thOpt.className = "key-th-opt";
      thOpt.textContent = letter;
      headerTr.appendChild(thOpt);
    });
    thead.appendChild(headerTr);
    table.appendChild(thead);

    // Linhas de questões descendo na vertical nesta coluna
    const tbody = document.createElement("tbody");
    for (let r = 0; r < questionsPerCol; r++) {
      const qNum = c * questionsPerCol + r + 1;
      if (qNum > numQ) break;

      const qStr = String(qNum);
      if (!currentAnswerKeyDraft[qStr] || !opts.includes(currentAnswerKeyDraft[qStr])) {
        currentAnswerKeyDraft[qStr] = opts[(qNum - 1) % opts.length];
      }

      const tr = document.createElement("tr");
      tr.className = "key-tr-row";

      // Célula do número do item (01, 02...)
      const tdItem = document.createElement("td");
      tdItem.className = "key-td-item";
      tdItem.textContent = String(qNum).padStart(2, "0");
      tr.appendChild(tdItem);

      // Células das alternativas com bolhas interativas
      opts.forEach(letter => {
        const tdOpt = document.createElement("td");
        tdOpt.className = "key-td-opt";

        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = `key-bubble-btn ${currentAnswerKeyDraft[qStr] === letter ? 'selected' : ''}`;
        btn.textContent = letter;
        btn.title = `Questão ${String(qNum).padStart(2, "0")}: Alternativa ${letter}`;

        btn.addEventListener("click", () => {
          currentAnswerKeyDraft[qStr] = letter;
          tr.querySelectorAll(".key-bubble-btn").forEach(b => b.classList.remove("selected"));
          btn.classList.add("selected");
          updateLiveSheetMockup();
        });

        tdOpt.appendChild(btn);
        tr.appendChild(tdOpt);
      });

      tbody.appendChild(tr);
    }

    table.appendChild(tbody);
    colCard.appendChild(table);
    matrixContainer.appendChild(colCard);
  }

  updateLiveSheetMockup();
}

numQuestionsInput.addEventListener("input", () => {
  initAnswerKeyMatrix();
  updateLiveSheetMockup();
});

numOptionsSelect.addEventListener("change", () => {
  initAnswerKeyMatrix();
  updateLiveSheetMockup();
});

// Submit Create / Edit Exam Form
createExamForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const title = document.getElementById("exam-title-input").value.trim();
  const subtitle = (document.getElementById("exam-subtitle-input")?.value || "").trim();
  const schoolName = (document.getElementById("exam-school-input")?.value || "").trim();
  const classroom = (document.getElementById("exam-class-input")?.value || "").trim();
  const shift = (document.getElementById("exam-shift-input")?.value || "").trim();

  const numQuestions = parseInt(numQuestionsInput.value);
  const numAlternatives = parseInt(numOptionsSelect.value);
  const points = parseFloat(document.getElementById("exam-points-input").value) || 1.0;

  saveExamBtn.disabled = true;
  saveExamBtn.innerHTML = '<div class="spinner"></div><span>Salvando...</span>';

  try {
    const payload = {
      title,
      subtitle: subtitle || "2º ANO DO ENSINO FUNDAMENTAL",
      school_name: schoolName,
      classroom: classroom,
      shift: shift || "(  ) MANHÃ       (  ) TARDE",
      logo_base64: currentLogoBase64,
      header_color: currentSheetColor || "#244061",
      num_questions: numQuestions,
      num_alternatives: numAlternatives,
      points_per_question: points,
      answer_key: currentAnswerKeyDraft
    };

    let res;
    if (editingExamId) {
      // UPDATE EXISTING
      res = await fetch(`/api/exams/${editingExamId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders()
        },
        body: JSON.stringify(payload)
      });
    } else {
      // CREATE NEW
      res = await fetch("/api/exams", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders()
        },
        body: JSON.stringify(payload)
      });
    }

    if (!res.ok) {
      if (res.status === 401) {
        showToast("Sua sessão expirou. Por favor, faça login novamente.", "warning");
        clearAuthToken();
        checkAuthStatus();
        return;
      }
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Erro ao salvar prova");
    }

    const saved = await res.json();
    const successMsg = editingExamId ? "Prova atualizada com sucesso!" : "Prova criada com sucesso!";
    showToast(successMsg, "success");

    activeExamId = saved.id;
    await loadExams(false);
    if (activeExamSelect) activeExamSelect.value = saved.id;

    // Reset edit state and form
    resetCreateForm();

    // Switch to exams tab
    switchTab("exams-tab");
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    saveExamBtn.disabled = false;
    saveExamBtn.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
        <polyline points="17 21 17 13 7 13 7 21"></polyline>
        <polyline points="7 3 7 8 15 8"></polyline>
      </svg>
      <span>Salvar Prova</span>
    `;
  }
});

function initEventListeners() {
  initColorPickerEventListeners();
  updateLiveSheetMockup();
  initSchoolBatchEventListeners();
}
initColorPickerEventListeners();

// ==========================================================================
// Gestão Escolar, Turmas, Importação CSV e Gabaritos em Lote
// ==========================================================================

let schoolsList = [];
let activeBatchClassId = null;
let activeBatchSchoolName = "";
let activeBatchClassName = "";
let activeReportClassId = null;
let selectedCsvFile = null;

async function loadSchools() {
  const container = document.getElementById("schools-container");
  if (!container) return;

  container.innerHTML = `
    <div style="grid-column: 1/-1; text-align: center; padding: 2rem; color: var(--text-secondary);">
      <div class="spinner" style="margin: 0 auto 0.75rem auto;"></div>
      <span>Carregando escolas e turmas...</span>
    </div>
  `;

  try {
    const res = await fetch("/api/schools");
    if (!res.ok) throw new Error("Erro ao carregar escolas.");
    schoolsList = await res.json();

    const searchInput = document.getElementById("schools-search-input");
    renderSchoolsGrid(searchInput ? searchInput.value : "");
  } catch (err) {
    container.innerHTML = `<div style="grid-column: 1/-1; color: var(--danger); text-align: center; padding: 2rem;">${err.message}</div>`;
  }
}

function renderSchoolsGrid(filterTerm = "") {
  const container = document.getElementById("schools-container");
  if (!container) return;

  const searchInput = document.getElementById("schools-search-input");
  const clearBtn = document.getElementById("schools-search-clear");
  const statsEl = document.getElementById("schools-search-stats");

  const term = (filterTerm !== undefined && filterTerm !== "" ? filterTerm : (searchInput ? searchInput.value : "")).trim().toLowerCase();

  if (clearBtn) {
    clearBtn.style.display = term ? "flex" : "none";
  }

  if (!schoolsList || schoolsList.length === 0) {
    if (statsEl) statsEl.style.display = "none";
    container.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 3.5rem 1.5rem; background: #ffffff; border: 1px dashed #cbd5e1; border-radius: var(--radius-md);">
        <div style="width: 48px; height: 48px; border-radius: 50%; background: #f1f5f9; display: flex; align-items: center; justify-content: center; margin: 0 auto 0.75rem auto; color: #64748b;">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 21h18M5 21V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16M9 9h1M9 13h1M9 17h1M14 9h1M14 13h1M14 17h1"></path></svg>
        </div>
        <h3 style="font-size: 1.05rem; font-weight: 700; margin-bottom: 0.25rem; color: #0f172a;">Nenhuma escola cadastrada ainda</h3>
        <p style="font-size: 0.85rem; color: var(--text-secondary); max-width: 420px; margin: 0 auto 1.25rem auto;">
          Importe a planilha .CSV com escolas, turmas e alunos para gerar gabaritos nominais automáticos e relatórios.
        </p>
        <button type="button" class="btn btn-primary" onclick="openCsvModal()">
          <span>Importar Alunos (.CSV)</span>
        </button>
      </div>
    `;
    return;
  }

  let matchedSchools = [];
  let totalMatchedClassrooms = 0;

  if (term) {
    schoolsList.forEach(school => {
      const schoolNameMatch = matchesSearchTokens(school.name, term);
      const matchedClassrooms = (school.classrooms || []).filter(cl => {
        return matchesSearchTokens([cl.name, cl.grade_year, cl.shift, school.name], term);
      });

      if (schoolNameMatch) {
        matchedSchools.push(school);
        totalMatchedClassrooms += (school.classrooms ? school.classrooms.length : 0);
      } else if (matchedClassrooms.length > 0) {
        matchedSchools.push({
          ...school,
          classrooms: matchedClassrooms,
          classroom_count: matchedClassrooms.length
        });
        totalMatchedClassrooms += matchedClassrooms.length;
      }
    });

    if (statsEl) {
      statsEl.style.display = "inline-flex";
      statsEl.innerHTML = `<span><strong>${matchedSchools.length}</strong> escola(s) e <strong>${totalMatchedClassrooms}</strong> turma(s) encontrada(s)</span>`;
    }
  } else {
    matchedSchools = schoolsList;
    if (statsEl) statsEl.style.display = "none";
  }

  if (matchedSchools.length === 0) {
    container.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 2.5rem 1.5rem; background: #ffffff; border: 1px dashed #cbd5e1; border-radius: var(--radius-md);">
        <p style="font-size: 0.95rem; font-weight: 600; color: #1e293b; margin-bottom: 0.35rem;">Nenhuma escola ou turma encontrada para "${escapeHtml(term)}"</p>
        <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.85rem;">Tente pesquisar por outro nome de escola, série (ex: 9º Ano) ou turno.</p>
        <button type="button" class="btn btn-secondary btn-sm" onclick="clearSchoolsSearch()">Limpar busca</button>
      </div>
    `;
    return;
  }

  container.innerHTML = "";
  matchedSchools.forEach(school => {
      const card = document.createElement("div");
      card.className = "school-card";

      let classListHtml = "";
      if (school.classrooms && school.classrooms.length > 0) {
        classListHtml = school.classrooms.map(cl => {
          const linkedBadges = (cl.linked_exams && cl.linked_exams.length > 0)
            ? cl.linked_exams.map(e => `<span class="cl-exam-chip" title="${e.title}">${e.title}</span>`).join("")
            : `<button type="button" class="cl-no-exams-btn" onclick="openLinkExamsModal('${cl.id}', '${cl.name.replace(/'/g, "\\'")}', '${school.name.replace(/'/g, "\\'")}')" title="Clique para vincular simulados a esta turma">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                <span>Vincular simulado</span>
              </button>`;

          // Clean display for grade year
          let displayGrade = "";
          if (cl.grade_year) {
            const gyUpper = cl.grade_year.trim().toUpperCase();
            if (!["MANHÃ", "TARDE", "NOITE", "INTEGRAL"].includes(gyUpper)) {
              const m = cl.grade_year.match(/\b([1-9]º?\s*ANO)\b/i);
              const shortGrade = m ? m[1].toUpperCase() : cl.grade_year;
              if (!cl.name.toUpperCase().includes(shortGrade)) {
                displayGrade = `<span class="cl-grade" title="${cl.grade_year}">${shortGrade}</span>`;
              }
            }
          }

          // Clean display for shift
          let displayShift = "";
          if (cl.shift) {
            const sUpper = cl.shift.toUpperCase();
            if (sUpper.includes("MANHÃ") && sUpper.includes("TARDE")) {
              displayShift = `<span class="cl-shift">MANHÃ / TARDE</span>`;
            } else if (sUpper.includes("MANHÃ")) {
              displayShift = `<span class="cl-shift">MANHÃ</span>`;
            } else if (sUpper.includes("TARDE")) {
              displayShift = `<span class="cl-shift">TARDE</span>`;
            } else if (sUpper.includes("NOITE")) {
              displayShift = `<span class="cl-shift">NOITE</span>`;
            } else if (cl.shift.trim().length > 0 && !cl.shift.includes("()")) {
              displayShift = `<span class="cl-shift">${cl.shift.trim()}</span>`;
            }
          }

          return `
          <div class="classroom-row">
            <div class="cl-col-main">
              <strong class="cl-name" title="${cl.name}">${cl.name}</strong>
              <div class="cl-tags-wrap">
                ${displayGrade}
                ${displayShift}
              </div>
            </div>

            <div class="cl-col-exams">
              ${linkedBadges}
            </div>

            <div class="cl-col-students">
              <button type="button" class="cl-student-toggle-btn" onclick="toggleStudentList('${cl.id}')" title="Ver lista de alunos">
                <strong>${cl.student_count || 0}</strong> alunos ▾
              </button>
            </div>

            <div class="cl-col-actions">
              <button type="button" class="cl-action-btn cl-action-btn-primary" onclick="openBatchModal('${cl.id}', '${cl.name.replace(/'/g, "\\'")}', '${school.name.replace(/'/g, "\\'")}', ${cl.student_count || 0})" title="Gerar folha de gabaritos personalizada em lote para esta turma">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                <span>Gabaritos</span>
              </button>
              <button type="button" class="cl-action-btn cl-action-btn-secondary" onclick="downloadSchoolEnvelopeLabels('${school.id}', '${school.name.replace(/'/g, "\\'")}', '${cl.id}', '${cl.name.replace(/'/g, "\\'")}')" title="Gerar Etiqueta de Envelope desta turma">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path><line x1="7" y1="7" x2="7.01" y2="7"></line></svg>
                <span>Etiqueta</span>
              </button>
              <button type="button" class="cl-action-btn cl-action-btn-secondary" onclick="openClassroomReportPage('${cl.id}', '${cl.name.replace(/'/g, "\\'")}', '${school.name.replace(/'/g, "\\'")}')" title="Ver relatório de avaliação e ranking da turma">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
                <span>Relatório</span>
              </button>

              <div class="cl-more-wrapper">
                <button type="button" class="cl-action-btn cl-action-btn-more" onclick="toggleClassroomMoreMenu(event, '${cl.id}')" title="Mais opções da turma" aria-label="Mais opções">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="1"></circle><circle cx="19" cy="12" r="1"></circle><circle cx="5" cy="12" r="1"></circle></svg>
                </button>
                <div id="cl-more-menu-${cl.id}" class="cl-dropdown-menu" style="display: none;">
                  <button type="button" class="cl-dropdown-item" onclick="openLinkExamsModal('${cl.id}', '${cl.name.replace(/'/g, "\\'")}', '${school.name.replace(/'/g, "\\'")}'); closeAllClassroomMenus();">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
                    <span>Vincular simulados</span>
                  </button>
                  <button type="button" class="cl-dropdown-item" onclick="openEditClassroomModal('${cl.id}', '${cl.name.replace(/'/g, "\\'")}', '${(cl.shift || '').replace(/'/g, "\\'")}', '${(cl.grade_year || '').replace(/'/g, "\\'")}', '${school.name.replace(/'/g, "\\'")}'); closeAllClassroomMenus();">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                    <span>Editar turma</span>
                  </button>
                  ${currentUserProfile && currentUserProfile.role === "admin" ? `
                  <div class="cl-dropdown-divider"></div>
                  <button type="button" class="cl-dropdown-item cl-dropdown-item-danger" onclick="deleteClassroomConfirm('${cl.id}', '${cl.name.replace(/'/g, "\\'")}'); closeAllClassroomMenus();">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                    <span>Excluir turma</span>
                  </button>` : ''}
                </div>
              </div>
            </div>

            <div id="students-collapse-${cl.id}" class="students-collapse-pane" style="display: none;">
              <div style="text-align: center; padding: 0.5rem; color: var(--text-secondary);">Carregando alunos...</div>
            </div>
          </div>
        `;
        }).join("");
      } else {
        classListHtml = `<div style="font-size: 0.85rem; color: var(--text-secondary); text-align: center; padding: 1.5rem;">Nenhuma turma cadastrada nesta escola.</div>`;
      }

      card.innerHTML = `
        <div class="school-card-header">
          <div class="school-header-info">
            <h3 class="school-name">${school.name}</h3>
            <span class="school-meta-pill">${school.classroom_count || 0} turmas • ${school.student_count || 0} alunos</span>
          </div>
          <div class="school-header-actions">
            <button type="button" class="btn btn-secondary btn-sm" onclick="downloadSchoolEnvelopeLabels('${school.id}', '${school.name.replace(/'/g, "\\'")}', ${school.classrooms && school.classrooms.length === 1 ? `'${school.classrooms[0].id}', '${school.classrooms[0].name.replace(/'/g, "\\'")}'` : 'null, null'})" title="Gerar Etiquetas de Envelope das Turmas (4 por folha A4)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path>
                <line x1="7" y1="7" x2="7.01" y2="7"></line>
              </svg>
              <span>Etiquetas</span>
            </button>
            <button type="button" class="btn btn-secondary btn-sm" onclick="openExportReportModal('school', 'school_performance', 'pdf', '${school.id}')" title="Exportar Relatório Consolidado da Escola">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              <span>Relatório</span>
            </button>
            <button type="button" class="btn btn-secondary btn-sm" onclick="openCsvModal('${school.id}')">
              Importar CSV
            </button>
            ${currentUserProfile && currentUserProfile.role === "admin" ? `
            <button type="button" class="btn btn-danger-subtle btn-sm delete-school-btn" onclick="deleteSchoolConfirm('${school.id}', '${school.name.replace(/'/g, "\\'")}')" title="Excluir escola">
              Excluir Escola
            </button>` : ''}
          </div>
        </div>
        <div class="school-card-body">
          <div class="classroom-table-header">
            <span>Turma</span>
            <span>Simulados</span>
            <span style="text-align: center;">Alunos</span>
            <span style="text-align: right;">Ações</span>
          </div>
          <div class="classroom-list">
            ${classListHtml}
          </div>
        </div>
      `;
      container.appendChild(card);
    });
}

function clearSchoolsSearch() {
  const searchInput = document.getElementById("schools-search-input");
  const clearBtn = document.getElementById("schools-search-clear");
  if (searchInput) {
    searchInput.value = "";
  }
  if (clearBtn) clearBtn.style.display = "none";
  renderSchoolsGrid("");
}

function clearExamsSearch() {
  const searchInput = document.getElementById("exams-search-input");
  const clearBtn = document.getElementById("exams-search-clear");
  const kbdHint = document.getElementById("exams-search-kbd");
  if (searchInput) {
    searchInput.value = "";
  }
  if (clearBtn) clearBtn.style.display = "none";
  if (kbdHint) kbdHint.style.display = "inline-flex";
  renderExamsGrid("");
}

// Toggle and lazy-load student list inside class card
async function toggleStudentList(classId) {
  const el = document.getElementById(`students-collapse-${classId}`);
  if (!el) return;

  if (el.style.display === "block") {
    el.style.display = "none";
    return;
  }

  el.style.display = "block";
  try {
    const res = await fetch(`/api/classrooms/${classId}`);
    if (!res.ok) throw new Error("Falha ao carregar alunos");
    const data = await res.json();
    const students = data.students || [];

    if (students.length === 0) {
      el.innerHTML = '<div style="padding: 0.5rem; color: var(--text-secondary);">Nenhum aluno cadastrado.</div>';
      return;
    }

    el.innerHTML = `
      <ul class="students-list-mini" style="display: flex; flex-direction: column; gap: 0.25rem; max-height: 240px; overflow-y: auto;">
        ${students.map((s, idx) => {
          const parts = (s.name || "").trim().split(/\s+/).filter(Boolean);
          const initials = parts.length === 1 
            ? parts[0].substring(0, 2).toUpperCase() 
            : ((parts[0] ? parts[0][0] : "") + (parts.length > 1 ? parts[parts.length - 1][0] : "")).toUpperCase();

          return `
          <li style="display: flex; align-items: center; justify-content: space-between; padding: 0.4rem 0.65rem; border-radius: 6px; background: #f8fafc; border: 1px solid #e2e8f0;">
            <div style="display: flex; align-items: center; gap: 0.55rem; min-width: 0;">
              <span style="display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; border-radius: 50%; background: #0f2942; color: #ffffff; font-size: 0.65rem; font-weight: 700; flex-shrink: 0;">
                ${initials || "AL"}
              </span>
              <span style="font-size: 0.825rem; font-weight: 600; color: #0f172a; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                ${idx + 1}. ${s.name}
              </span>
            </div>
            <span class="student-reg-num" style="font-family: monospace; font-size: 0.75rem; color: #64748b; background: #ffffff; padding: 2px 7px; border-radius: 4px; border: 1px solid #e2e8f0; flex-shrink: 0; margin-left: 0.5rem;">
              ${s.registration || "-"}
            </span>
          </li>
        `;
        }).join("")}
      </ul>
    `;
  } catch (err) {
    el.innerHTML = `<div style="padding: 0.5rem; color: var(--danger);">${err.message}</div>`;
  }
}

// Manual School Modal Functions
function openNewSchoolModal() {
  const modal = document.getElementById("new-school-modal");
  const nameInput = document.getElementById("new-school-name-input");
  const inepInput = document.getElementById("new-school-inep-input");
  if (nameInput) nameInput.value = "";
  if (inepInput) inepInput.value = "";
  if (modal) modal.style.display = "flex";
}

function closeNewSchoolModal() {
  const modal = document.getElementById("new-school-modal");
  if (modal) modal.style.display = "none";
}

async function deleteSchoolConfirm(schoolId, schoolName) {
  if (currentUserProfile && currentUserProfile.role !== "admin") {
    showToast("Apenas o Administrador SEMED tem permissão para excluir escolas.", "warning");
    return;
  }
  if (!confirm(`Tem certeza que deseja excluir a escola "${schoolName}"?\n\nEsta ação excluirá permanentemente em cascata todas as turmas, alunos e notas desta escola.`)) {
    return;
  }
  try {
    const res = await fetch(`/api/schools/${schoolId}`, {
      method: "DELETE",
      headers: { ...getAuthHeaders() }
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Erro ao excluir escola.");
    }
    showToast("Escola excluída com sucesso.", "success");
    await loadSchools();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function downloadSchoolEnvelopeLabels(schoolId, schoolName, classroomId = null, classroomName = null) {
  showToast("Gerando etiquetas de envelopes... O download iniciará em instantes.", "info");
  try {
    let url = `/api/schools/${schoolId}/envelope-labels-pdf`;
    if (classroomId) {
      url += `?classroom_id=${encodeURIComponent(classroomId)}`;
    }
    const res = await fetch(url, {
      headers: { ...getAuthHeaders() }
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const msg = err.detail || "Erro ao gerar etiquetas de envelopes da escola.";
      showToast(msg, res.status === 400 ? "warning" : "error");
      return;
    }

    const blob = await res.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = blobUrl;

    const safeSchoolName = (schoolName || "Escola").replace(/[/\\?%*:|"<>]/g, "_").trim();
    let downloadFileName = `Turmas - Etiquetas - ${safeSchoolName}.pdf`;

    if (classroomName) {
      const safeClassName = classroomName.replace(/[/\\?%*:|"<>]/g, "_").trim();
      downloadFileName = `${safeClassName} - Etiquetas - ${safeSchoolName}.pdf`;
    }

    const disposition = res.headers.get("Content-Disposition");
    if (disposition && disposition.includes("filename*=UTF-8''")) {
      try {
        const parts = disposition.split("filename*=UTF-8''");
        if (parts[1]) {
          downloadFileName = decodeURIComponent(parts[1].split(";")[0].replace(/"/g, "").trim());
        }
      } catch (e) {
        // fallback
      }
    } else if (disposition && disposition.includes('filename="')) {
      try {
        const parts = disposition.split('filename="');
        if (parts[1]) {
          downloadFileName = parts[1].split('"')[0].trim();
        }
      } catch (e) {
        // fallback
      }
    }

    link.download = downloadFileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setTimeout(() => window.URL.revokeObjectURL(blobUrl), 2000);

    showToast("Etiquetas de envelopes geradas com sucesso!", "success");
  } catch (err) {
    console.error(err);
    showToast(err.message || "Erro ao baixar etiquetas.", "error");
  }
}

async function deleteClassroomConfirm(classId, className) {
  if (currentUserProfile && currentUserProfile.role !== "admin") {
    showToast("Apenas o Administrador SEMED tem permissão para excluir turmas.", "warning");
    return;
  }
  if (!confirm(`Tem certeza que deseja excluir a turma "${className}" e seus alunos?`)) {
    return;
  }
  try {
    const res = await fetch(`/api/classrooms/${classId}`, {
      method: "DELETE",
      headers: { ...getAuthHeaders() }
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Erro ao excluir turma.");
    }
    showToast("Turma excluída com sucesso.", "success");
    await loadSchools();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// CSV Modal Functions
function openCsvModal(preselectedSchoolId = null) {
  const modal = document.getElementById("csv-import-modal");
  selectedCsvFile = null;
  const fileInfo = document.getElementById("csv-file-info");
  const submitBtn = document.getElementById("btn-submit-csv");
  const fileInput = document.getElementById("csv-file-input");
  const schoolSelect = document.getElementById("csv-school-select");

  if (fileInfo) fileInfo.style.display = "none";
  if (submitBtn) submitBtn.disabled = true;
  if (fileInput) fileInput.value = "";

  if (schoolSelect) {
    schoolSelect.innerHTML = '<option value="">-- Selecione a Escola --</option>';
    schoolsList.forEach(s => {
      const opt = document.createElement("option");
      opt.value = s.id;
      opt.textContent = s.name;
      if (preselectedSchoolId && s.id === preselectedSchoolId) {
        opt.selected = true;
      }
      schoolSelect.appendChild(opt);
    });
  }

  if (modal) modal.style.display = "flex";
}

function closeCsvModal() {
  const modal = document.getElementById("csv-import-modal");
  if (modal) modal.style.display = "none";
}

// Link Multiple Exams to Classroom Modal Functions
let currentLinkingClassId = null;

function openLinkExamsModal(classId, className, schoolName) {
  currentLinkingClassId = classId;
  const modal = document.getElementById("link-exams-modal");
  const subtitle = document.getElementById("link-exams-class-subtitle");
  const container = document.getElementById("link-exams-list-container");

  if (subtitle) {
    subtitle.textContent = `Turma: ${className} • ${schoolName}`;
  }

  if (container) {
    if (examsList.length === 0) {
      container.innerHTML = '<div style="color: var(--text-secondary); font-size: 0.85rem; padding: 0.5rem;">Nenhum simulado cadastrado. Crie um simulado primeiro na aba "Criar Prova".</div>';
    } else {
      let linkedIds = [];
      schoolsList.forEach(s => {
        (s.classrooms || []).forEach(c => {
          if (c.id === classId && c.linked_exams) {
            linkedIds = c.linked_exams.map(e => e.id);
          }
        });
      });

      container.innerHTML = examsList.map(ex => {
        const isChecked = linkedIds.includes(ex.id) ? "checked" : "";
        return `
          <label style="display: flex; align-items: center; gap: 0.6rem; padding: 0.5rem 0.6rem; background: #f8fafc; border-radius: 6px; cursor: pointer; transition: background 0.15s ease;">
            <input type="checkbox" class="link-exam-chk" value="${ex.id}" ${isChecked} style="width: 17px; height: 17px; cursor: pointer;">
            <div style="flex: 1;">
              <strong style="font-size: 0.85rem; color: var(--text-primary); display: block;">${ex.title}</strong>
              <div style="font-size: 0.75rem; color: var(--text-secondary);">${ex.num_questions} Questões • ${ex.subtitle || "PROVA OFICIAL"}</div>
            </div>
          </label>
        `;
      }).join("");
    }
  }

  if (modal) modal.style.display = "flex";
}

function closeLinkExamsModal() {
  const modal = document.getElementById("link-exams-modal");
  if (modal) modal.style.display = "none";
  currentLinkingClassId = null;
}

async function saveLinkedExams() {
  if (!currentLinkingClassId) return;
  const checkboxes = document.querySelectorAll(".link-exam-chk:checked");
  const selectedIds = Array.from(checkboxes).map(c => c.value);

  try {
    const res = await fetch(`/api/classrooms/${currentLinkingClassId}/exams`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders()
      },
      body: JSON.stringify({ exam_ids: selectedIds })
    });

    if (!res.ok) throw new Error("Erro ao salvar gabaritos vinculados.");
    showToast("Gabaritos vinculados à turma com sucesso!", "success");
    closeLinkExamsModal();
    await loadSchools();
  } catch (err) {
    console.error(err);
    showToast(err.message, "error");
  }
}

// Edit Classroom Modal Functions
function openEditClassroomModal(classId, className, shift, gradeYear, schoolName) {
  const modal = document.getElementById("edit-classroom-modal");
  const idInput = document.getElementById("edit-classroom-id-input");
  const nameInput = document.getElementById("edit-classroom-name-input");
  const shiftSelect = document.getElementById("edit-classroom-shift-select");
  const gradeSelect = document.getElementById("edit-classroom-grade-select");
  const gradeCustomWrap = document.getElementById("edit-classroom-grade-custom-wrap");
  const gradeCustomInput = document.getElementById("edit-classroom-grade-custom-input");
  const schoolSubtitle = document.getElementById("edit-classroom-school-subtitle");

  if (idInput) idInput.value = classId;
  if (nameInput) nameInput.value = className || "";
  if (schoolSubtitle) schoolSubtitle.textContent = schoolName ? `Escola: ${schoolName}` : "Dados da Turma";

  // Shift normalization
  if (shiftSelect) {
    const sUpper = (shift || "").toUpperCase();
    if (sUpper.includes("INTEGRAL")) {
      shiftSelect.value = "INTEGRAL";
    } else if (sUpper.includes("TARDE")) {
      shiftSelect.value = "TARDE";
    } else if (sUpper.includes("NOITE")) {
      shiftSelect.value = "NOITE";
    } else {
      shiftSelect.value = "MANHÃ";
    }
  }

  // Grade / Year normalization
  if (gradeSelect) {
    let matched = false;
    const rawGrade = (gradeYear || "").trim();
    for (let i = 0; i < gradeSelect.options.length; i++) {
      const optVal = gradeSelect.options[i].value;
      if (optVal === "OUTRO") continue;
      if (rawGrade && (rawGrade.toUpperCase() === optVal.toUpperCase() || rawGrade.toUpperCase().includes(optVal.toUpperCase()) || optVal.toUpperCase().includes(rawGrade.toUpperCase()))) {
        gradeSelect.selectedIndex = i;
        matched = true;
        break;
      }
    }

    if (!matched && rawGrade) {
      gradeSelect.value = "OUTRO";
      if (gradeCustomWrap) gradeCustomWrap.style.display = "block";
      if (gradeCustomInput) gradeCustomInput.value = rawGrade;
    } else {
      if (!matched) gradeSelect.selectedIndex = 0;
      if (gradeCustomWrap) gradeCustomWrap.style.display = "none";
      if (gradeCustomInput) gradeCustomInput.value = "";
    }
  }

  if (modal) modal.style.display = "flex";
}

function closeEditClassroomModal() {
  const modal = document.getElementById("edit-classroom-modal");
  if (modal) modal.style.display = "none";
}

// Batch PDF Modal Functions
function openBatchModal(classId, className, schoolName, studentCount) {
  activeBatchClassId = classId;
  activeBatchClassName = className || "";
  activeBatchSchoolName = schoolName || "";
  const modal = document.getElementById("batch-pdf-modal");
  const classNameEl = document.getElementById("batch-modal-class-name");
  const schoolNameEl = document.getElementById("batch-modal-school-name");
  const studentCountEl = document.getElementById("batch-modal-student-count");
  const examSelect = document.getElementById("batch-exam-select");

  if (classNameEl) classNameEl.textContent = className;
  if (schoolNameEl) schoolNameEl.textContent = schoolName;
  if (studentCountEl) studentCountEl.textContent = studentCount;

  if (examSelect) {
    examSelect.innerHTML = "";
    
    let linkedExams = [];
    schoolsList.forEach(s => {
      (s.classrooms || []).forEach(c => {
        if (c.id === classId && c.linked_exams) {
          linkedExams = c.linked_exams;
        }
      });
    });

    if (linkedExams.length === 0) {
      examSelect.innerHTML = '<option value="" disabled selected>Nenhum simulado vinculado a esta turma</option>';
    } else if (linkedExams.length === 2) {
      // Se tiver exatamente 2 simulados vinculados, opção combinada 2 em 1
      const bothOpt = document.createElement("option");
      bothOpt.value = "both";
      bothOpt.textContent = `Ambos os Simulados (${linkedExams[0].title} + ${linkedExams[1].title})`;
      bothOpt.selected = true;
      examSelect.appendChild(bothOpt);

      linkedExams.forEach(ex => {
        const opt = document.createElement("option");
        opt.value = ex.id;
        opt.textContent = `Apenas: ${ex.title} (${ex.num_questions}Q)`;
        examSelect.appendChild(opt);
      });
    } else if (linkedExams.length > 2) {
      const bothOpt = document.createElement("option");
      bothOpt.value = "both";
      bothOpt.textContent = `Todos os Simulados Vinculados (${linkedExams.length} Provas)`;
      bothOpt.selected = true;
      examSelect.appendChild(bothOpt);

      linkedExams.forEach(ex => {
        const opt = document.createElement("option");
        opt.value = ex.id;
        opt.textContent = `${ex.title} (${ex.num_questions}Q)`;
        examSelect.appendChild(opt);
      });
    } else {
      // Exatamente 1 simulado vinculado
      linkedExams.forEach((ex, idx) => {
        const opt = document.createElement("option");
        opt.value = ex.id;
        opt.textContent = `${ex.title} (${ex.num_questions} Questões)`;
        if (idx === 0) opt.selected = true;
        examSelect.appendChild(opt);
      });
    }
  }

  updateBatchNotice();

  if (modal) modal.style.display = "flex";
}

function updateBatchNotice() {
  const notice = document.getElementById("batch-dual-notice");
  const examSelect = document.getElementById("batch-exam-select");
  const layoutRadio = document.querySelector('input[name="batch-layout-radio"]:checked');
  if (!notice) return;

  const isDouble = layoutRadio && (layoutRadio.value === "double" || layoutRadio.value === "2");
  const isBoth = examSelect && examSelect.value === "both";

  if (isBoth && isDouble) {
    notice.style.display = "block";
    notice.innerHTML = `<strong>Modo 2 em 1 ativado:</strong> Como a opção "2 por folha" está selecionada, cada aluno receberá <strong>ambos os simulados na mesma folha A4</strong> (metade superior e metade inferior, com linha de corte).`;
  } else if (isBoth && !isDouble) {
    notice.style.display = "block";
    notice.innerHTML = `<strong>Modo 1 por folha:</strong> Serão geradas páginas A4 completas para ambos os simulados de cada aluno.`;
  } else {
    notice.style.display = "none";
  }
}

function closeBatchModal() {
  const modal = document.getElementById("batch-pdf-modal");
  if (modal) modal.style.display = "none";
}

// ==========================================================================
// CLASSROOM REPORT FULL VIEW & ANALYTICS
// ==========================================================================
let activeReportClassName = "";
let activeReportSchoolName = "";
let activeReportExamId = null;
let reportQuestionsChart = null;
let reportDistributionChart = null;
let currentReportData = null;

async function openClassroomReportPage(classId, className, schoolName) {
  activeReportClassId = classId;
  activeReportClassName = className || "Turma";
  activeReportSchoolName = schoolName || "Escola";

  try {
    localStorage.setItem("omr_active_tab", "schools-tab");
    localStorage.setItem("omr_active_subpage", JSON.stringify({
      type: "classroom-report",
      classId,
      className: activeReportClassName,
      schoolName: activeReportSchoolName
    }));
  } catch (e) {}

  // Hide all tab content and deactivate tab buttons
  document.querySelectorAll(".tab-content").forEach(el => {
    el.style.display = "none";
    el.classList.remove("active");
  });
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));

  // Show report view section
  const reportView = document.getElementById("classroom-report-view");
  if (reportView) {
    reportView.style.display = "block";
    reportView.classList.add("active");
  }
  window.scrollTo({ top: 0, behavior: "smooth" });

  // Update header text
  const classTitleEl = document.getElementById("page-rep-class-title");
  const schoolSubEl = document.getElementById("page-rep-school-subtitle");
  if (classTitleEl) classTitleEl.textContent = `Relatório da Turma: ${activeReportClassName}`;
  if (schoolSubEl) schoolSubEl.textContent = activeReportSchoolName;

  // Reset to single report sub tab view
  switchReportSubTab("single");

  // Populate exam select (only exams linked to this classroom)
  const examSelect = document.getElementById("page-rep-exam-select");
  if (examSelect) {
    examSelect.innerHTML = "";
    
    let linkedExams = [];
    schoolsList.forEach(s => {
      (s.classrooms || []).forEach(c => {
        if (c.id === classId && c.linked_exams) {
          linkedExams = c.linked_exams;
        }
      });
    });

    if (linkedExams.length === 0) {
      examSelect.innerHTML = '<option value="">Nenhum simulado vinculado a esta turma</option>';
    } else {
      linkedExams.forEach((ex, idx) => {
        const opt = document.createElement("option");
        opt.value = ex.id;
        opt.textContent = `${ex.title} (${ex.num_questions}Q)`;
        if (idx === 0) opt.selected = true;
        examSelect.appendChild(opt);
      });
    }
  }

  const selectedExamId = examSelect ? examSelect.value : null;
  activeReportExamId = selectedExamId;
  if (selectedExamId) {
    await loadClassroomReportPage(classId, selectedExamId);
  } else {
    const tbody = document.getElementById("page-rep-students-tbody");
    if (tbody) {
      tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 2rem; color: var(--text-secondary);">Nenhum simulado vinculado a esta turma. Vincule um simulado na tela de turmas para visualizar relatórios.</td></tr>';
    }
  }
}

function closeClassroomReportPage() {
  try {
    localStorage.removeItem("omr_active_subpage");
  } catch (e) {}
  switchTab("schools-tab");
}

async function loadClassroomReportPage(classId, examId) {
  activeReportExamId = examId;
  const tbody = document.getElementById("page-rep-students-tbody");
  if (tbody) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 2rem; color: var(--text-secondary);">Carregando métricas e ranking da turma...</td></tr>';
  }

  try {
    const res = await fetch(`/api/classrooms/${classId}/exams/${examId}/report`);
    if (!res.ok) throw new Error("Erro ao carregar relatório da turma.");
    const data = await res.json();
    currentReportData = data;

    const totalStudents = data.total_students || 0;
    const gradedStudents = data.graded_students || 0;
    const pendingStudents = data.pending_students || 0;
    const avgScore = (data.average_score || 0).toFixed(1);
    const avgPct = data.average_percentage || 0;
    const maxScore = data.exam ? (data.exam.max_score || 10.0) : 10.0;

    // 1. Fill KPI Cards
    const elTotal = document.getElementById("page-rep-total-students");
    const elGraded = document.getElementById("page-rep-graded-students");
    const elGradedPct = document.getElementById("page-rep-graded-pct");
    const elPending = document.getElementById("page-rep-pending-students");
    const elAvgScore = document.getElementById("page-rep-avg-score");
    const elMaxScoreSub = document.getElementById("page-rep-max-score-sub");
    const elAvgPct = document.getElementById("page-rep-avg-pct");

    if (elTotal) elTotal.textContent = totalStudents;
    if (elGraded) elGraded.textContent = gradedStudents;
    if (elGradedPct) {
      const presencePct = totalStudents > 0 ? Math.round((gradedStudents / totalStudents) * 100) : 0;
      elGradedPct.textContent = `${presencePct}% de presença`;
    }
    if (elPending) elPending.textContent = pendingStudents;
    if (elAvgScore) elAvgScore.textContent = avgScore;
    if (elMaxScoreSub) elMaxScoreSub.textContent = `de ${maxScore.toFixed(1)} pontos`;
    if (elAvgPct) elAvgPct.textContent = `${avgPct}%`;

    // 2. Render Podium Top 3
    renderPodium(data.students || [], maxScore);

    // 3. Render Question Accuracy Bar Chart
    renderQuestionsAccuracyChart(data.questions_stats || {}, gradedStudents);

    // 4. Render Grade Distribution Chart
    renderGradeDistributionChart(data.grade_distribution || {}, gradedStudents);

    // 5. Render Ranking Table
    const searchInput = document.getElementById("report-ranking-search");
    const currentQuery = searchInput ? searchInput.value.trim() : "";
    renderRankingTable(data.students || [], maxScore, currentQuery);

  } catch (err) {
    console.error("Erro ao carregar relatório:", err);
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="8" style="color: var(--danger); text-align: center; padding: 2rem;">${err.message}</td></tr>`;
    }
  }
}

// Render Top 3 Best Students
function renderPodium(students, maxScore) {
  const container = document.getElementById("podium-stage-container");
  if (!container) return;

  const graded = students.filter(s => s.status === "CORRIGIDO" && s.score !== null);
  graded.sort((a, b) => (b.score || 0) - (a.score || 0));

  if (graded.length === 0) {
    container.innerHTML = `
      <div class="podium-empty-state">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" style="color: var(--text-muted); margin-bottom: 0.4rem;"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
        <div>Nenhuma prova corrigida para este simulado.</div>
      </div>
    `;
    return;
  }

  const topThree = [
    { student: graded[0] || null, rank: 1, label: "1º Lugar", classKey: "rank-1-card", pillKey: "pill-gold" },
    { student: graded.length > 1 ? graded[1] : null, rank: 2, label: "2º Lugar", classKey: "rank-2-card", pillKey: "pill-silver" },
    { student: graded.length > 2 ? graded[2] : null, rank: 3, label: "3º Lugar", classKey: "rank-3-card", pillKey: "pill-bronze" }
  ];

  let cardsHtml = topThree.map(item => {
    const st = item.student;
    if (!st) {
      return `
        <div class="top-student-card ${item.classKey} card-empty">
          <div class="top-card-header">
            <span class="top-rank-pill ${item.pillKey}">${item.label}</span>
          </div>
          <div class="top-student-name" style="color: var(--text-muted);">-</div>
        </div>
      `;
    }

    return `
      <div class="top-student-card ${item.classKey}">
        <div class="top-card-header">
          <span class="top-rank-pill ${item.pillKey}">${item.label}</span>
          <span class="top-student-reg">${st.registration ? `Matrícula: ${st.registration}` : ""}</span>
        </div>
        <div class="top-student-name" title="${st.name}">${st.name}</div>
        <div class="top-student-score-row">
          <span class="top-student-score">${st.score.toFixed(1)}</span>
          <span class="top-student-max">/ ${(maxScore || 10).toFixed(1)} pts</span>
        </div>
        <div class="top-student-hits">
          ${st.correct_count !== undefined ? `${st.correct_count} acertos (${st.percentage || 0}%)` : ""}
        </div>
      </div>
    `;
  }).join("");

  container.innerHTML = `<div class="top-students-grid">${cardsHtml}</div>`;
}

// Render Questions Accuracy Chart (Bar Chart)
function renderQuestionsAccuracyChart(questionsStats, gradedCount) {
  const canvas = document.getElementById("chart-questions-accuracy");
  if (!canvas || typeof Chart === "undefined") return;

  if (reportQuestionsChart) {
    reportQuestionsChart.destroy();
    reportQuestionsChart = null;
  }

  const qKeys = Object.keys(questionsStats).sort((a, b) => parseInt(a) - parseInt(b));
  if (qKeys.length === 0) {
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    return;
  }

  const labels = qKeys.map(k => `Q${k}`);
  const dataValues = qKeys.map(k => questionsStats[k].accuracy_percentage || 0);
  const correctAnswers = qKeys.map(k => questionsStats[k].correct_answer || "-");
  const hitsCount = qKeys.map(k => questionsStats[k].correct_count || 0);

  // Dynamic bar colors: Green (>=70%), Amber (40-69%), Red (<40%)
  const backgroundColors = dataValues.map(pct => {
    if (pct >= 70) return "#10b981"; // Emerald
    if (pct >= 40) return "#f59e0b"; // Amber
    return "#ef4444"; // Red
  });

  const ctx = canvas.getContext("2d");
  reportQuestionsChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: "% de Acerto",
        data: dataValues,
        backgroundColor: backgroundColors,
        borderRadius: 6,
        borderSkipped: false,
        maxBarThickness: 32
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#0f172a",
          padding: 10,
          titleFont: { family: "'Plus Jakarta Sans', sans-serif", size: 13, weight: "bold" },
          bodyFont: { family: "'Plus Jakarta Sans', sans-serif", size: 12 },
          callbacks: {
            title: function(context) {
              const idx = context[0].dataIndex;
              return `${labels[idx]} (Gabarito: ${correctAnswers[idx]})`;
            },
            label: function(context) {
              const idx = context.dataIndex;
              return `Taxa de Acertos: ${dataValues[idx]}% (${hitsCount[idx]} de ${gradedCount} alunos)`;
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          ticks: {
            stepSize: 25,
            callback: value => `${value}%`,
            font: { family: "'Plus Jakarta Sans', sans-serif", size: 11 }
          },
          grid: {
            color: "#f1f5f9"
          }
        },
        x: {
          ticks: {
            font: { family: "'Plus Jakarta Sans', sans-serif", size: 11, weight: "bold" }
          },
          grid: { display: false }
        }
      }
    }
  });
}

// Render Grade Distribution Chart (Doughnut Chart)
function renderGradeDistributionChart(gradeDist, totalGraded) {
  const canvas = document.getElementById("chart-grade-distribution");
  const summaryBox = document.getElementById("grade-dist-summary-box");
  if (!canvas || typeof Chart === "undefined") return;

  if (reportDistributionChart) {
    reportDistributionChart.destroy();
    reportDistributionChart = null;
  }

  const ins = gradeDist.insufficient || 0;
  const reg = gradeDist.regular || 0;
  const good = gradeDist.good || 0;
  const exc = gradeDist.excellent || 0;

  // Render chips summary
  if (summaryBox) {
    summaryBox.innerHTML = `
      <div class="dist-chip chip-danger">
        <span>Abaixo de 5.0 (Crítico)</span>
        <strong>${ins} aluno(s)</strong>
      </div>
      <div class="dist-chip chip-warning">
        <span>5.0 – 6.9 (Regular)</span>
        <strong>${reg} aluno(s)</strong>
      </div>
      <div class="dist-chip chip-primary">
        <span>7.0 – 8.9 (Bom)</span>
        <strong>${good} aluno(s)</strong>
      </div>
      <div class="dist-chip chip-success">
        <span>9.0 – 10.0 (Excelente)</span>
        <strong>${exc} aluno(s)</strong>
      </div>
    `;
  }

  const hasData = (ins + reg + good + exc) > 0;
  const ctx = canvas.getContext("2d");

  reportDistributionChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Crítico (< 5.0)", "Regular (5.0 - 6.9)", "Bom (7.0 - 8.9)", "Excelente (9.0 - 10.0)"],
      datasets: [{
        data: hasData ? [ins, reg, good, exc] : [1],
        backgroundColor: hasData ? ["#ef4444", "#f59e0b", "#2563eb", "#10b981"] : ["#e2e8f0"],
        borderWidth: 2,
        borderColor: "#ffffff"
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            font: { family: "'Plus Jakarta Sans', sans-serif", size: 11 },
            boxWidth: 12,
            padding: 10
          }
        },
        tooltip: {
          enabled: hasData,
          callbacks: {
            label: function(context) {
              const val = context.raw || 0;
              const pct = totalGraded > 0 ? Math.round((val / totalGraded) * 100) : 0;
              return ` ${val} aluno(s) (${pct}%)`;
            }
          }
        }
      },
      cutout: "68%"
    }
  });
}

// Render Ranking Table with Search Filter
function renderRankingTable(students, maxScore, filterQuery) {
  const tbody = document.getElementById("page-rep-students-tbody");
  if (!tbody) return;

  tbody.innerHTML = "";

  const q = (filterQuery || "").toLowerCase();
  const filtered = students.filter(st => {
    if (!q) return true;
    const nameMatch = (st.name || "").toLowerCase().includes(q);
    const regMatch = (st.registration || "").toLowerCase().includes(q);
    return nameMatch || regMatch;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 2rem; color: var(--text-secondary);">Nenhum estudante encontrado com o filtro aplicado.</td></tr>';
    return;
  }

  // Count graded rank
  let gradedRank = 1;

  filtered.forEach(st => {
    const tr = document.createElement("tr");
    const isGraded = st.status === "CORRIGIDO" && st.score !== null;
    const subId = st.submission ? st.submission.id : null;

    let rankBadge = "";
    if (isGraded) {
      if (gradedRank === 1) rankBadge = '<span class="rank-badge rank-1">1º</span>';
      else if (gradedRank === 2) rankBadge = '<span class="rank-badge rank-2">2º</span>';
      else if (gradedRank === 3) rankBadge = '<span class="rank-badge rank-3">3º</span>';
      else rankBadge = `<span class="rank-badge rank-default">${gradedRank}º</span>`;
      gradedRank++;
    } else {
      rankBadge = '<span style="color: var(--text-muted); font-size: 0.85rem;">-</span>';
    }

    const correctCount = st.correct_count !== undefined ? st.correct_count : (st.submission ? st.submission.correct_count : 0);
    const totalQuestions = currentReportData && currentReportData.exam ? currentReportData.exam.num_questions : 20;
    const pct = isGraded ? (st.percentage !== undefined && st.percentage !== null ? `${st.percentage}%` : `${Math.round((st.score / maxScore) * 100)}%`) : "-";

    tr.innerHTML = `
      <td style="text-align: center;">${rankBadge}</td>
      <td><strong>${st.name}</strong></td>
      <td style="text-align: center;">
        ${isGraded ? `<span style="font-weight: 800; font-size: 0.95rem; color: var(--text-primary);">${st.score.toFixed(1)}</span>` : '<span style="color: var(--text-muted);">-</span>'}
      </td>
      <td style="text-align: center;">
        ${isGraded ? `<span style="font-weight: 600; color: #0f172a;">${correctCount}</span> <span style="font-size: 0.75rem; color: var(--text-muted);">/ ${totalQuestions}</span>` : '<span style="color: var(--text-muted);">-</span>'}
      </td>
      <td style="text-align: center;">
        ${isGraded ? `
          <div style="display: flex; align-items: center; justify-content: center; gap: 0.4rem;">
            <div style="flex: 1; max-width: 60px; height: 6px; background: #e2e8f0; border-radius: 3px; overflow: hidden;">
              <div style="width: ${pct}; height: 100%; background: #10b981;"></div>
            </div>
            <span style="font-weight: 700; font-size: 0.8rem;">${pct}</span>
          </div>
        ` : '<span style="color: var(--text-muted);">-</span>'}
      </td>
      <td style="text-align: center;">
        <span class="badge-status" style="${isGraded ? 'background: var(--success-light); color: var(--success); font-weight: 700;' : 'background: #f1f5f9; color: #64748b;'}">
          ${isGraded ? 'CORRIGIDO' : 'PENDENTE'}
        </span>
      </td>
      <td style="text-align: center;">
        ${isGraded && subId && (currentUserProfile && currentUserProfile.role === "admin") ? `
          <button class="btn btn-xs delete-student-sub-btn" data-subid="${subId}" data-name="${st.name}" title="Excluir correção deste aluno" style="padding: 0.25rem 0.6rem; font-size: 0.75rem; color: var(--danger); border-color: rgba(239, 68, 68, 0.3); background: #fff5f5; border-radius: 4px; cursor: pointer;">
            Excluir
          </button>
        ` : '<span style="color: var(--text-secondary); font-size: 0.75rem;">-</span>'}
      </td>
    `;

    if (isGraded && subId) {
      const delBtn = tr.querySelector(".delete-student-sub-btn");
      if (delBtn) {
        delBtn.addEventListener("click", async () => {
          if (currentUserProfile && currentUserProfile.role !== "admin") {
            showToast("Apenas o Administrador SEMED tem permissão para excluir correções.", "warning");
            return;
          }
          const conf = confirm(`Deseja realmente excluir a correção de "${st.name}"?\n\nOs dados da folha serão removidos e o status voltará para PENDENTE.`);
          if (!conf) return;

          try {
            const delRes = await fetch(`/api/submissions/${subId}`, {
              method: "DELETE",
              headers: { ...getAuthHeaders() }
            });
            if (!delRes.ok) {
              const errJson = await delRes.json().catch(() => ({}));
              throw new Error(errJson.detail || "Erro ao excluir correção.");
            }
            showToast(`Correção de "${st.name}" excluída com sucesso!`, "success");
            await loadClassroomReportPage(activeReportClassId, activeReportExamId);
            loadExams(false);
          } catch (err) {
            console.error(err);
            showToast(err.message, "error");
          }
        });
      }
    }

    tbody.appendChild(tr);
  });
}

// ==========================================================================
// CLASSROOM EXAMS COMPARISON LOGIC
// ==========================================================================
let currentComparisonData = null;
let compareQuestionsChart = null;

function switchReportSubTab(tab) {
  const btnSingle = document.getElementById("btn-subnav-single");
  const btnCompare = document.getElementById("btn-subnav-compare");
  const viewSingle = document.getElementById("report-view-single");
  const viewCompare = document.getElementById("report-view-compare");

  // Top header comparison elements
  const dotExamA = document.getElementById("dot-exam-a");
  const txtExamSelect = document.getElementById("txt-page-rep-exam-select");
  const headerCompareVs = document.getElementById("header-compare-vs");
  const headerCompareExam2Pill = document.getElementById("header-compare-exam2-pill");
  const exportSingleItems = document.getElementById("export-menu-single-items");
  const exportCompareItems = document.getElementById("export-menu-compare-items");

  if (tab === "compare") {
    if (btnSingle) btnSingle.classList.remove("active");
    if (btnCompare) btnCompare.classList.add("active");
    if (viewSingle) viewSingle.style.display = "none";
    if (viewCompare) viewCompare.style.display = "block";

    // Show comparison elements in top header
    if (dotExamA) dotExamA.style.display = "inline-block";
    if (txtExamSelect) txtExamSelect.textContent = "Gabarito A:";
    if (headerCompareVs) headerCompareVs.style.display = "inline-flex";
    if (headerCompareExam2Pill) headerCompareExam2Pill.style.display = "inline-flex";

    // Adapt unified export dropdown menu
    if (exportSingleItems) exportSingleItems.style.display = "none";
    if (exportCompareItems) exportCompareItems.style.display = "block";

    // Populate and trigger comparison
    setupComparisonSelectors();
  } else {
    if (btnSingle) btnSingle.classList.add("active");
    if (btnCompare) btnCompare.classList.remove("active");
    if (viewSingle) viewSingle.style.display = "block";
    if (viewCompare) viewCompare.style.display = "none";

    // Hide comparison elements in top header
    if (dotExamA) dotExamA.style.display = "none";
    if (txtExamSelect) txtExamSelect.textContent = "Simulado:";
    if (headerCompareVs) headerCompareVs.style.display = "none";
    if (headerCompareExam2Pill) headerCompareExam2Pill.style.display = "none";

    // Adapt unified export dropdown menu
    if (exportSingleItems) exportSingleItems.style.display = "block";
    if (exportCompareItems) exportCompareItems.style.display = "none";

    const sel1 = document.getElementById("page-rep-exam-select");
    if (activeReportClassId && sel1 && sel1.value) {
      loadClassroomReportPage(activeReportClassId, sel1.value);
    }
  }
}

function setupComparisonSelectors() {
  const sel1 = document.getElementById("page-rep-exam-select");
  const sel2 = document.getElementById("compare-select-exam2");
  if (!sel1 || !sel2) return;

  // Find linked exams for the active classroom
  let linkedExams = [];
  schoolsList.forEach(s => {
    (s.classrooms || []).forEach(c => {
      if (c.id === activeReportClassId && c.linked_exams) {
        linkedExams = c.linked_exams;
      }
    });
  });

  sel2.innerHTML = "";

  if (linkedExams.length === 0) {
    sel2.innerHTML = '<option value="">Nenhum simulado vinculado</option>';
    return;
  }

  linkedExams.forEach((ex) => {
    const opt2 = document.createElement("option");
    opt2.value = ex.id;
    opt2.textContent = `${ex.title} (${ex.num_questions}Q)`;
    sel2.appendChild(opt2);
  });

  // Default selection: if sel1 is index 0 and there is a 2nd exam, pick index 1 for sel2
  if (linkedExams.length > 1) {
    if (sel1.selectedIndex === 0) {
      sel2.selectedIndex = 1;
    } else {
      sel2.selectedIndex = 0;
    }
  } else {
    sel2.selectedIndex = 0;
  }

  // Auto-trigger comparison
  if (sel1.value && sel2.value) {
    loadClassroomComparison(activeReportClassId, sel1.value, sel2.value);
  }
}

async function loadClassroomComparison(classId, exam1Id, exam2Id) {
  if (!classId || !exam1Id || !exam2Id) return;

  const tbody = document.getElementById("compare-students-tbody");
  if (tbody) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 2rem; color: var(--text-secondary);">Calculando comparativo entre os gabaritos...</td></tr>';
  }

  try {
    const res = await fetch(`/api/classrooms/${classId}/compare?exam1=${exam1Id}&exam2=${exam2Id}`);
    if (!res.ok) {
      const errJson = await res.json().catch(() => ({}));
      throw new Error(errJson.detail || "Erro ao calcular comparativo.");
    }
    const data = await res.json();
    currentComparisonData = data;

    const ex1 = data.exam1;
    const ex2 = data.exam2;
    const summary = data.summary;

    // 1. Update Highlight Insight Banner
    const bannerText = document.getElementById("compare-insight-text");
    if (bannerText) {
      bannerText.textContent = summary.highlight_summary || "Comparativo gerado com sucesso.";
    }

    // 2. Update Comparison KPIs
    const elName1 = document.getElementById("comp-kpi-name1");
    const elScore1 = document.getElementById("comp-kpi-score1");
    const elPct1 = document.getElementById("comp-kpi-pct1");
    const elName2 = document.getElementById("comp-kpi-name2");
    const elScore2 = document.getElementById("comp-kpi-score2");
    const elPct2 = document.getElementById("comp-kpi-pct2");
    const elDiffFooter = document.getElementById("comp-kpi-diff-footer");

    if (elName1) elName1.textContent = ex1.title;
    if (elScore1) elScore1.textContent = (summary.avg_score1 || 0).toFixed(1);
    if (elPct1) elPct1.textContent = `${summary.avg_pct1 || 0}% de acertos`;

    if (elName2) elName2.textContent = ex2.title;
    if (elScore2) elScore2.textContent = (summary.avg_score2 || 0).toFixed(1);
    if (elPct2) elPct2.textContent = `${summary.avg_pct2 || 0}% de acertos`;

    if (elDiffFooter) {
      const diffSign = summary.avg_diff > 0 ? `+${summary.avg_diff.toFixed(1)} pts em ${ex1.title}` : (summary.avg_diff < 0 ? `+${Math.abs(summary.avg_diff).toFixed(1)} pts em ${ex2.title}` : "Médias empatadas");
      elDiffFooter.textContent = `Variação: ${diffSign}`;
    }

    // Presence KPIs
    const elPresName1 = document.getElementById("comp-kpi-pres-name1");
    const elGraded1 = document.getElementById("comp-kpi-graded1");
    const elPresName2 = document.getElementById("comp-kpi-pres-name2");
    const elGraded2 = document.getElementById("comp-kpi-graded2");
    const elTotalFooter = document.getElementById("comp-kpi-total-students-footer");

    if (elPresName1) elPresName1.textContent = ex1.title;
    if (elGraded1) elGraded1.textContent = summary.graded_students1 || 0;
    if (elPresName2) elPresName2.textContent = ex2.title;
    if (elGraded2) elGraded2.textContent = summary.graded_students2 || 0;
    if (elTotalFooter) elTotalFooter.textContent = `Total na turma: ${summary.total_students || 0} matriculados`;

    // 3. Legend labels
    const leg1 = document.getElementById("leg-exam1-name");
    const leg2 = document.getElementById("leg-exam2-name");
    if (leg1) leg1.textContent = ex1.title;
    if (leg2) leg2.textContent = ex2.title;

    // 4. Render Grouped Bar Chart (Questions Side-by-Side)
    renderComparisonQuestionsChart(data.questions_comparison || [], ex1.title, ex2.title);

    // 5. Update Table Column Headers
    const th1 = document.getElementById("th-comp-exam1");
    const th2 = document.getElementById("th-comp-exam2");
    if (th1) th1.textContent = `Nota (${ex1.title})`;
    if (th2) th2.textContent = `Nota (${ex2.title})`;

    // 6. Render Student Comparison Table
    const searchInput = document.getElementById("compare-students-search");
    const q = searchInput ? searchInput.value.trim() : "";
    renderComparisonStudentsTable(data.students || [], q);

  } catch (err) {
    console.error("Erro ao carregar comparativo:", err);
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="7" style="color: var(--danger); text-align: center; padding: 2rem;">${err.message}</td></tr>`;
    }
  }
}

// Render Comparison Chart (Chart.js Grouped Bars)
function renderComparisonQuestionsChart(questionsComparison, title1, title2) {
  const canvas = document.getElementById("chart-compare-questions");
  if (!canvas || typeof Chart === "undefined") return;

  if (compareQuestionsChart) {
    compareQuestionsChart.destroy();
    compareQuestionsChart = null;
  }

  if (questionsComparison.length === 0) {
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    return;
  }

  const labels = questionsComparison.map(q => `Q${q.question}`);
  const data1 = questionsComparison.map(q => q.accuracy1 || 0);
  const data2 = questionsComparison.map(q => q.accuracy2 || 0);

  const ctx = canvas.getContext("2d");
  compareQuestionsChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: title1,
          data: data1,
          backgroundColor: "#2563eb",
          borderRadius: 4,
          maxBarThickness: 18
        },
        {
          label: title2,
          data: data2,
          backgroundColor: "#10b981",
          borderRadius: 4,
          maxBarThickness: 18
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#0f172a",
          padding: 10,
          titleFont: { family: "'Plus Jakarta Sans', sans-serif", size: 13, weight: "bold" },
          bodyFont: { family: "'Plus Jakarta Sans', sans-serif", size: 12 },
          callbacks: {
            label: function(context) {
              const datasetLabel = context.dataset.label || "";
              const val = context.parsed.y || 0;
              return ` ${datasetLabel}: ${val}% de acertos`;
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          ticks: {
            stepSize: 25,
            callback: v => `${v}%`,
            font: { family: "'Plus Jakarta Sans', sans-serif", size: 11 }
          },
          grid: { color: "#f1f5f9" }
        },
        x: {
          ticks: { font: { family: "'Plus Jakarta Sans', sans-serif", size: 11, weight: "bold" } },
          grid: { display: false }
        }
      }
    }
  });
}

function buildExamChipsHtml(examTitle, results, isGraded, score, correctCount, numQuestions) {
  if (!isGraded || !results || results.length === 0) {
    return `
      <div class="exam-answers-card">
        <div class="exam-answers-header">
          <strong>${examTitle}</strong>
          <span class="exam-answers-badge badge-pending">Pendente</span>
        </div>
        <div class="exam-answers-empty">Nenhuma prova corrigida para este gabarito.</div>
      </div>
    `;
  }

  const chipsHtml = results.map(r => {
    const qNum = r.question || 0;
    const isCorrect = !!r.is_correct;
    const chosen = r.chosen || "-";
    const correct = r.correct || "-";

    if (isCorrect) {
      return `
        <div class="q-chip q-correct" title="Questão ${qNum}: Resposta ${chosen} (Correta)">
          <span class="q-num">Q${qNum}</span>
          <span class="q-ans">${chosen}</span>
          <span class="q-icon">✓</span>
        </div>
      `;
    } else if (chosen === "BLANK" || chosen === "-" || !chosen) {
      return `
        <div class="q-chip q-blank" title="Questão ${qNum}: Em Branco (Gabarito: ${correct})">
          <span class="q-num">Q${qNum}</span>
          <span class="q-ans">Ø</span>
          <span class="q-key">(${correct})</span>
        </div>
      `;
    } else {
      return `
        <div class="q-chip q-wrong" title="Questão ${qNum}: Marcou ${chosen} (Gabarito: ${correct})">
          <span class="q-num">Q${qNum}</span>
          <span class="q-ans">${chosen}</span>
          <span class="q-icon">✗</span>
          <span class="q-key">(${correct})</span>
        </div>
      `;
    }
  }).join("");

  return `
    <div class="exam-answers-card">
      <div class="exam-answers-header">
        <strong>${examTitle}</strong>
        <span class="exam-answers-badge badge-graded">${correctCount} de ${numQuestions || results.length} acertos (${score !== null ? score.toFixed(1) : "-"} pts)</span>
      </div>
      <div class="questions-chips-grid">
        ${chipsHtml}
      </div>
    </div>
  `;
}

// Render Comparison Students Table with question answers toggle
function renderComparisonStudentsTable(students, filterQuery) {
  const tbody = document.getElementById("compare-students-tbody");
  if (!tbody) return;

  tbody.innerHTML = "";

  const q = (filterQuery || "").toLowerCase();
  const filtered = students.filter(st => {
    if (!q) return true;
    const nameMatch = (st.name || "").toLowerCase().includes(q);
    const regMatch = (st.registration || "").toLowerCase().includes(q);
    return nameMatch || regMatch;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 2rem; color: var(--text-secondary);">Nenhum estudante encontrado com o filtro informado.</td></tr>';
    return;
  }

  const ex1 = currentComparisonData && currentComparisonData.exam1 ? currentComparisonData.exam1 : { title: "Gabarito A", num_questions: 0 };
  const ex2 = currentComparisonData && currentComparisonData.exam2 ? currentComparisonData.exam2 : { title: "Gabarito B", num_questions: 0 };

  filtered.forEach((st, idx) => {
    const tr = document.createElement("tr");
    tr.className = "compare-student-row";
    tr.id = `comp-st-row-${idx}`;

    const hasScore1 = st.score1 !== null && st.score1 !== undefined;
    const hasScore2 = st.score2 !== null && st.score2 !== undefined;

    // Best exam badge
    let bestBadge = `<span style="color: var(--text-muted);">${st.best_exam || "-"}</span>`;
    if (st.best_exam && st.best_exam !== "-" && st.best_exam !== "Empate") {
      bestBadge = `<span class="badge-best-exam">${st.best_exam}</span>`;
    }

    tr.innerHTML = `
      <td>
        <div class="student-name-toggle-wrap">
          <svg class="chevron-toggle" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
          <div class="student-name-col">
            <strong class="student-name-text">${st.name}</strong>
            <span class="student-hint-text">Clique para ver acertos/erros</span>
          </div>
        </div>
      </td>
      <td style="text-align: center;">
        ${hasScore1 ? `
          <strong style="color: #2563eb; font-size: 0.95rem;">${st.score1.toFixed(1)}</strong>
          <span style="font-size: 0.72rem; color: var(--text-muted); display: block;">${st.correct1} acertos</span>
        ` : '<span style="color: var(--text-muted); font-size: 0.8rem;">Pendente</span>'}
      </td>
      <td style="text-align: center;">
        ${hasScore2 ? `
          <strong style="color: #059669; font-size: 0.95rem;">${st.score2.toFixed(1)}</strong>
          <span style="font-size: 0.72rem; color: var(--text-muted); display: block;">${st.correct2} acertos</span>
        ` : '<span style="color: var(--text-muted); font-size: 0.8rem;">Pendente</span>'}
      </td>
      <td style="text-align: center;">
        ${st.combined_avg !== null && st.combined_avg !== undefined ? `
          <strong style="font-size: 0.95rem; color: #0f172a;">${st.combined_avg.toFixed(1)}</strong>
        ` : '<span style="color: var(--text-muted);">-</span>'}
      </td>
      <td style="text-align: center;">${bestBadge}</td>
    `;

    // Detail Row for question-by-question toggle
    const detailTr = document.createElement("tr");
    detailTr.className = "compare-detail-row";
    detailTr.id = `comp-st-detail-${idx}`;
    detailTr.style.display = "none";

    const detailTd = document.createElement("td");
    detailTd.colSpan = 5;
    detailTd.className = "compare-detail-cell";

    const card1Html = buildExamChipsHtml(ex1.title, st.results1, hasScore1, st.score1, st.correct1, ex1.num_questions);
    const card2Html = buildExamChipsHtml(ex2.title, st.results2, hasScore2, st.score2, st.correct2, ex2.num_questions);

    detailTd.innerHTML = `
      <div class="student-answers-detail-grid">
        ${card1Html}
        ${card2Html}
      </div>
    `;
    detailTr.appendChild(detailTd);

    // Toggle event on student row click
    tr.addEventListener("click", () => {
      const isExpanded = detailTr.style.display !== "none";
      if (isExpanded) {
        detailTr.style.display = "none";
        tr.classList.remove("row-expanded");
      } else {
        detailTr.style.display = "table-row";
        tr.classList.add("row-expanded");
      }
    });

    tbody.appendChild(tr);
    tbody.appendChild(detailTr);
  });
}

// Backward compatibility alias for modal calls
const openReportModal = openClassroomReportPage;
const closeReportModal = closeClassroomReportPage;
const loadClassroomReport = loadClassroomReportPage;

function initSchoolBatchEventListeners() {
  // New School Modal triggers
  const btnOpenNewSchool = document.getElementById("btn-open-new-school-modal");
  const btnCloseNewSchool = document.getElementById("btn-close-new-school-modal");
  const btnCancelNewSchool = document.getElementById("btn-cancel-new-school");
  const formNewSchool = document.getElementById("new-school-form");

  if (btnOpenNewSchool) btnOpenNewSchool.addEventListener("click", openNewSchoolModal);
  if (btnCloseNewSchool) btnCloseNewSchool.addEventListener("click", closeNewSchoolModal);
  if (btnCancelNewSchool) btnCancelNewSchool.addEventListener("click", closeNewSchoolModal);

  if (formNewSchool) {
    formNewSchool.addEventListener("submit", async (e) => {
      e.preventDefault();
      const nameInput = document.getElementById("new-school-name-input");
      const inepInput = document.getElementById("new-school-inep-input");
      const name = nameInput ? nameInput.value.trim() : "";
      const inep = inepInput ? inepInput.value.trim() : "";

      if (!name) {
        showToast("Digite o nome da escola.", "error");
        return;
      }

      try {
        const res = await fetch("/api/schools", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...getAuthHeaders()
          },
          body: JSON.stringify({ name: name, inep_code: inep })
        });
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || "Erro ao criar escola.");
        }
        showToast("Escola cadastrada com sucesso!", "success");
        closeNewSchoolModal();
        await loadSchools();
      } catch (err) {
        showToast(err.message, "error");
      }
    });
  }

  // CSV Modal triggers
  const btnOpenCsv = document.getElementById("btn-open-csv-modal");
  const btnCloseCsv = document.getElementById("btn-close-csv-modal");
  const btnCancelCsv = document.getElementById("btn-cancel-csv");
  const csvDropzone = document.getElementById("csv-dropzone");
  const csvFileInput = document.getElementById("csv-file-input");
  const btnSubmitCsv = document.getElementById("btn-submit-csv");

  if (btnOpenCsv) btnOpenCsv.addEventListener("click", () => openCsvModal());
  if (btnCloseCsv) btnCloseCsv.addEventListener("click", closeCsvModal);
  if (btnCancelCsv) btnCancelCsv.addEventListener("click", closeCsvModal);

  if (csvDropzone && csvFileInput) {
    csvDropzone.addEventListener("click", () => csvFileInput.click());
    csvDropzone.addEventListener("dragover", (e) => {
      e.preventDefault();
      csvDropzone.classList.add("dragover");
    });
    csvDropzone.addEventListener("dragleave", () => csvDropzone.classList.remove("dragover"));
    csvDropzone.addEventListener("drop", (e) => {
      e.preventDefault();
      csvDropzone.classList.remove("dragover");
      if (e.dataTransfer.files.length > 0) {
        handleCsvFileSelected(e.dataTransfer.files[0]);
      }
    });

    csvFileInput.addEventListener("change", (e) => {
      if (e.target.files.length > 0) {
        handleCsvFileSelected(e.target.files[0]);
      }
    });
  }

  function handleCsvFileSelected(file) {
    selectedCsvFile = file;
    const fileInfo = document.getElementById("csv-file-info");
    const fileName = document.getElementById("csv-file-name");
    const submitBtn = document.getElementById("btn-submit-csv");
    if (fileInfo && fileName) {
      fileName.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
      fileInfo.style.display = "block";
    }
    if (submitBtn) submitBtn.disabled = false;
  }

  if (btnSubmitCsv) {
    btnSubmitCsv.addEventListener("click", async () => {
      if (!selectedCsvFile) return;
      const schoolSelect = document.getElementById("csv-school-select");
      const schoolId = schoolSelect ? schoolSelect.value : "";

      if (schoolsList.length > 0 && !schoolId) {
        showToast("Por favor, selecione a escola de destino para importar as turmas.", "error");
        return;
      }

      btnSubmitCsv.disabled = true;
      btnSubmitCsv.innerHTML = '<div class="spinner"></div><span>Importando...</span>';

      const formData = new FormData();
      formData.append("file", selectedCsvFile);
      if (schoolId) {
        formData.append("school_id", schoolId);
      }

      try {
        const res = await fetch("/api/students/import-csv", {
          method: "POST",
          headers: {
            ...getAuthHeaders()
          },
          body: formData
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Falha na importação do CSV.");

        showToast(`Sucesso! ${data.imported_students} alunos importados em ${data.classrooms_count} turma(s).`, "success");
        closeCsvModal();
        await loadSchools();
      } catch (err) {
        showToast(err.message, "error");
      } finally {
        btnSubmitCsv.disabled = false;
        btnSubmitCsv.innerHTML = "<span>Processar e Importar</span>";
      }
    });
  }

  // Batch Modal triggers
  const btnCloseBatch = document.getElementById("btn-close-batch-modal");
  const btnCancelBatch = document.getElementById("btn-cancel-batch");
  const btnConfirmBatch = document.getElementById("btn-confirm-batch-pdf");

  if (btnCloseBatch) btnCloseBatch.addEventListener("click", closeBatchModal);
  if (btnCancelBatch) btnCancelBatch.addEventListener("click", closeBatchModal);

  const batchExamSelectEl = document.getElementById("batch-exam-select");
  if (batchExamSelectEl) {
    batchExamSelectEl.addEventListener("change", updateBatchNotice);
  }

  document.querySelectorAll('input[name="batch-layout-radio"]').forEach(radio => {
    radio.addEventListener("change", updateBatchNotice);
  });

  if (btnConfirmBatch) {
    btnConfirmBatch.addEventListener("click", async () => {
      const examSelect = document.getElementById("batch-exam-select");
      if (!examSelect || !examSelect.value) {
        showToast("Esta turma não possui simulados vinculados. Vincule os simulados à turma antes de gerar os gabaritos.", "error");
        return;
      }

      const layoutRadio = document.querySelector('input[name="batch-layout-radio"]:checked');
      const layout = layoutRadio ? layoutRadio.value : "double";
      const examId = examSelect.value;

      const originalBtnHtml = btnConfirmBatch.innerHTML;
      btnConfirmBatch.disabled = true;
      btnConfirmBatch.innerHTML = '<div class="spinner"></div><span>Gerando Gabaritos...</span>';

      showToast("Gerando gabaritos nominais em lote... O download iniciará em instantes.", "info");

      const downloadUrl = `/api/classrooms/${activeBatchClassId}/exams/${examId}/batch-pdf?layout=${layout}`;

      let defaultFileName = "GABARITOS.pdf";
      if (activeBatchClassName && activeBatchSchoolName) {
        defaultFileName = `${activeBatchClassName} - GABARITOS - ${activeBatchSchoolName}.pdf`;
      } else if (activeBatchClassName) {
        defaultFileName = `${activeBatchClassName} - GABARITOS.pdf`;
      } else if (activeBatchSchoolName) {
        defaultFileName = `GABARITOS - ${activeBatchSchoolName}.pdf`;
      }

      try {
        const res = await fetch(downloadUrl, {
          headers: { ...getAuthHeaders() }
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || "Erro ao gerar gabaritos da turma.");
        }

        const blob = await res.blob();
        const blobUrl = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = blobUrl;
        link.download = defaultFileName;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        setTimeout(() => window.URL.revokeObjectURL(blobUrl), 2000);

        showToast("Download dos gabaritos iniciado com sucesso!", "success");
        closeBatchModal();
      } catch (err) {
        console.error(err);
        showToast(err.message, "error");
      } finally {
        btnConfirmBatch.disabled = false;
        btnConfirmBatch.innerHTML = originalBtnHtml;
      }
    });
  }

  // Classroom Report Page triggers
  const btnBackToSchools = document.getElementById("btn-back-to-schools");
  const pageRepExamSelect = document.getElementById("page-rep-exam-select");
  const compareSelectExam2 = document.getElementById("compare-select-exam2");
  const btnPageExportCsv = document.getElementById("btn-page-export-report-csv");
  const searchRankingInput = document.getElementById("report-ranking-search");

  if (btnBackToSchools) btnBackToSchools.addEventListener("click", closeClassroomReportPage);

  if (pageRepExamSelect) {
    pageRepExamSelect.addEventListener("change", () => {
      if (activeReportClassId && pageRepExamSelect.value) {
        const btnCompare = document.getElementById("btn-subnav-compare");
        const isCompareMode = btnCompare && btnCompare.classList.contains("active");
        if (isCompareMode) {
          const sel2 = document.getElementById("compare-select-exam2");
          if (sel2 && sel2.value) {
            loadClassroomComparison(activeReportClassId, pageRepExamSelect.value, sel2.value);
          }
        } else {
          loadClassroomReportPage(activeReportClassId, pageRepExamSelect.value);
        }
      }
    });
  }

  if (compareSelectExam2) {
    compareSelectExam2.addEventListener("change", () => {
      if (activeReportClassId && pageRepExamSelect && pageRepExamSelect.value && compareSelectExam2.value) {
        loadClassroomComparison(activeReportClassId, pageRepExamSelect.value, compareSelectExam2.value);
      }
    });
  }

  if (btnPageExportCsv) {
    btnPageExportCsv.addEventListener("click", () => {
      if (!activeReportClassId || !pageRepExamSelect || !pageRepExamSelect.value) return;
      window.open(`/api/classrooms/${activeReportClassId}/exams/${pageRepExamSelect.value}/report/csv`, "_blank");
    });
  }

  const btnExportCompareCsv = document.getElementById("btn-export-compare-csv");
  if (btnExportCompareCsv) {
    btnExportCompareCsv.addEventListener("click", () => {
      const sel1 = document.getElementById("page-rep-exam-select");
      const sel2 = document.getElementById("compare-select-exam2");
      if (!activeReportClassId || !sel1 || !sel2 || !sel1.value || !sel2.value) return;
      window.open(`/api/classrooms/${activeReportClassId}/compare/csv?exam1=${sel1.value}&exam2=${sel2.value}`, "_blank");
    });
  }

  if (searchRankingInput) {
    searchRankingInput.addEventListener("input", (e) => {
      if (currentReportData && currentReportData.students) {
        const maxScore = currentReportData.exam ? (currentReportData.exam.max_score || 10.0) : 10.0;
        renderRankingTable(currentReportData.students, maxScore, e.target.value.trim());
      }
    });
  }

  const searchCompareInput = document.getElementById("compare-students-search");

  if (searchCompareInput) {
    searchCompareInput.addEventListener("input", (e) => {
      if (currentComparisonData && currentComparisonData.students) {
        renderComparisonStudentsTable(currentComparisonData.students, e.target.value.trim());
      }
    });
  }

  // Modal legacy triggers (for any residual modal calls)
  const btnCloseReport = document.getElementById("btn-close-report-modal");
  if (btnCloseReport) btnCloseReport.addEventListener("click", closeClassroomReportPage);

  // Link Exams Modal triggers
  const btnCloseLinkExams = document.getElementById("btn-close-link-exams-modal");
  const btnCancelLinkExams = document.getElementById("btn-cancel-link-exams");
  const btnSaveLinkExams = document.getElementById("btn-save-link-exams");

  if (btnCloseLinkExams) btnCloseLinkExams.addEventListener("click", closeLinkExamsModal);
  if (btnCancelLinkExams) btnCancelLinkExams.addEventListener("click", closeLinkExamsModal);
  if (btnSaveLinkExams) btnSaveLinkExams.addEventListener("click", saveLinkedExams);

  // Edit Classroom Modal triggers
  const editGradeSelect = document.getElementById("edit-classroom-grade-select");
  const editGradeCustomWrap = document.getElementById("edit-classroom-grade-custom-wrap");
  if (editGradeSelect && editGradeCustomWrap) {
    editGradeSelect.addEventListener("change", () => {
      editGradeCustomWrap.style.display = editGradeSelect.value === "OUTRO" ? "block" : "none";
    });
  }

  const formEditClassroom = document.getElementById("edit-classroom-form");
  if (formEditClassroom) {
    formEditClassroom.addEventListener("submit", async (e) => {
      e.preventDefault();
      const idInput = document.getElementById("edit-classroom-id-input");
      const nameInput = document.getElementById("edit-classroom-name-input");
      const shiftSelect = document.getElementById("edit-classroom-shift-select");
      const gradeSelect = document.getElementById("edit-classroom-grade-select");
      const gradeCustomInput = document.getElementById("edit-classroom-grade-custom-input");

      const classId = idInput ? idInput.value : null;
      const name = nameInput ? nameInput.value.trim() : "";
      const shift = shiftSelect ? shiftSelect.value : "MANHÃ";
      let gradeYear = gradeSelect ? gradeSelect.value : "";
      if (gradeYear === "OUTRO" && gradeCustomInput) {
        gradeYear = gradeCustomInput.value.trim();
      }

      if (!classId) {
        showToast("ID da turma não encontrado.", "error");
        return;
      }
      if (!name) {
        showToast("Informe o nome da turma.", "error");
        return;
      }

      const btnSave = document.getElementById("btn-save-edit-classroom");
      if (btnSave) btnSave.disabled = true;

      try {
        const res = await fetch(`/api/classrooms/${classId}`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            ...getAuthHeaders()
          },
          body: JSON.stringify({ name, shift, grade_year: gradeYear })
        });
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || "Erro ao atualizar dados da turma.");
        }
        showToast("Turma atualizada com sucesso!", "success");
        closeEditClassroomModal();
        await loadSchools();
      } catch (err) {
        showToast(err.message, "error");
      } finally {
        if (btnSave) btnSave.disabled = false;
      }
    });
  }

  // Settings Modal triggers
  const btnOpenSettings = document.getElementById("btn-open-settings-modal");
  const btnCloseSettings = document.getElementById("btn-close-settings-modal");
  const btnCancelSettings = document.getElementById("btn-cancel-settings");
  const logoFileInput = document.getElementById("settings-logo-input");

  if (btnOpenSettings) btnOpenSettings.addEventListener("click", openSettingsModal);
  if (btnCloseSettings) btnCloseSettings.addEventListener("click", closeSettingsModal);
  if (btnCancelSettings) btnCancelSettings.addEventListener("click", closeSettingsModal);
  if (logoFileInput) {
    logoFileInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files[0]) {
        handleLogoUpload(e.target.files[0]);
      }
    });
  }

  // Year Report Modal triggers
  const btnOpenYearReport = document.getElementById("btn-open-year-report-modal");
  const btnOpenYearReportNav = document.getElementById("btn-open-year-report-nav");
  const btnCloseYearReport = document.getElementById("btn-close-year-report-modal");

  if (btnOpenYearReport) btnOpenYearReport.addEventListener("click", openYearReportModal);
  if (btnOpenYearReportNav) btnOpenYearReportNav.addEventListener("click", openYearReportModal);
  if (btnCloseYearReport) btnCloseYearReport.addEventListener("click", closeYearReportModal);

  const btnLoadYearReport = document.getElementById("btn-load-year-report");
  if (btnLoadYearReport) btnLoadYearReport.addEventListener("click", loadYearReportData);

  const yearRepSearchInput = document.getElementById("year-rep-search-input");
  if (yearRepSearchInput) {
    yearRepSearchInput.addEventListener("input", filterYearReportTable);
  }

  const yearRepGradeSelect = document.getElementById("year-rep-grade-select");
  if (yearRepGradeSelect) {
    yearRepGradeSelect.addEventListener("change", async () => {
      await updateYearReportExamsDropdown();
      await loadYearReportData();
    });
  }

  const yearRepSchoolSelect = document.getElementById("year-rep-school-select");
  if (yearRepSchoolSelect) {
    yearRepSchoolSelect.addEventListener("change", async () => {
      await updateYearReportExamsDropdown();
      await loadYearReportData();
    });
  }

  const yearRepExamSelect = document.getElementById("year-rep-exam-select");
  if (yearRepExamSelect) yearRepExamSelect.addEventListener("change", loadYearReportData);

  const yearReportModalEl = document.getElementById("year-report-modal");
  if (yearReportModalEl) {
    yearReportModalEl.addEventListener("click", (e) => {
      if (e.target === yearReportModalEl) closeYearReportModal();
    });
  }

  const exportReportModalEl = document.getElementById("modal-export-report");
  if (exportReportModalEl) {
    exportReportModalEl.addEventListener("click", (e) => {
      if (e.target === exportReportModalEl) closeExportReportModal();
    });
  }

  // Export Dropdown toggles
  const btnToggleExportClass = document.getElementById("btn-toggle-export-class");
  if (btnToggleExportClass) {
    btnToggleExportClass.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleExportDropdown("dropdown-menu-export-class");
    });
  }

  const btnToggleExportCompare = document.getElementById("btn-toggle-export-compare");
  if (btnToggleExportCompare) {
    btnToggleExportCompare.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleExportDropdown("dropdown-menu-export-compare");
    });
  }

  const btnToggleExportNetwork = document.getElementById("btn-toggle-export-network");
  if (btnToggleExportNetwork) {
    btnToggleExportNetwork.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleExportDropdown("dropdown-menu-export-network");
    });
  }
}

// Global click listener to close dropdowns when clicking outside
document.addEventListener("click", (e) => {
  if (!e.target.closest(".export-dropdown-wrapper")) {
    closeAllExportDropdowns();
  }
});

function toggleExportDropdown(menuId) {
  const menu = document.getElementById(menuId);
  if (!menu) return;
  const isShown = menu.style.display === "flex";
  closeAllExportDropdowns();
  if (!isShown) {
    menu.style.display = "flex";
  }
}

function closeAllExportDropdowns() {
  document.querySelectorAll(".report-dropdown-menu").forEach(menu => {
    menu.style.display = "none";
  });
}

// --- Multi-Format Report Exporter Helper ---
async function downloadReport(endpointUrl, defaultFilename) {
  showToast("Gerando relatório oficial... O download iniciará em instantes.", "info");
  try {
    const resp = await fetch(endpointUrl);
    if (!resp.ok) {
      const errJson = await resp.json().catch(() => ({}));
      throw new Error(errJson.detail || `Erro do servidor: ${resp.status}`);
    }

    let filename = defaultFilename;
    const disposition = resp.headers.get("content-disposition");
    if (disposition && disposition.indexOf("filename=") !== -1) {
      const filenameMatch = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
      if (filenameMatch && filenameMatch[1]) {
        filename = filenameMatch[1].replace(/['"]/g, "").trim();
      }
    }

    const blob = await resp.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.style.display = "none";
    link.href = blobUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    window.URL.revokeObjectURL(blobUrl);
    document.body.removeChild(link);
    showToast("Relatório emitido com sucesso!", "success");
  } catch (err) {
    showToast("Falha na emissão do relatório: " + err.message, "error");
  }
}

function getActiveClassNameClean() {
  const titleEl = document.getElementById("page-rep-class-title");
  let name = "";
  if (titleEl && titleEl.textContent) {
    name = titleEl.textContent.replace(/^Relat[óo]rio da Turma:?\s*/i, "").trim();
  }
  if (!name && currentReportData && currentReportData.classroom) {
    name = currentReportData.classroom.name || "";
  }
  if (!name && currentComparisonData && currentComparisonData.classroom) {
    name = currentComparisonData.classroom.name || "";
  }
  if (!name && activeReportClassId && typeof schoolsList !== "undefined" && Array.isArray(schoolsList)) {
    schoolsList.forEach(s => {
      (s.classrooms || []).forEach(c => {
        if (c.id === activeReportClassId) name = c.name;
      });
    });
  }
  if (!name) name = "Turma";
  return name
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-zA-Z0-9_-]/g, "_")
    .replace(/_+/g, "_")
    .replace(/^_+|_+$/g, "");
}

// --- Classroom Report Exports ---
function exportClassroomReport(format) {
  closeAllExportDropdowns();
  if (!activeReportClassId) {
    showToast("Nenhuma turma ativa selecionada.", "error");
    return;
  }
  const examSelect = document.getElementById("page-rep-exam-select");
  const examId = examSelect ? examSelect.value : "";
  const param = examId ? `?exam_id=${examId}&format=${format}` : `?format=${format}`;
  const clName = getActiveClassNameClean();
  downloadReport(`/api/reports/classroom/${activeReportClassId}${param}`, `Relatorio_Turma_${clName}.${format}`);
}

function exportClassroomDiagnostic(format) {
  closeAllExportDropdowns();
  if (!activeReportClassId) {
    showToast("Nenhuma turma ativa selecionada.", "error");
    return;
  }
  const examSelect = document.getElementById("page-rep-exam-select");
  const examId = examSelect ? examSelect.value : "";
  const param = examId ? `?exam_id=${examId}&format=${format}` : `?format=${format}`;
  const clName = getActiveClassNameClean();
  downloadReport(`/api/reports/diagnostic/${activeReportClassId}${param}`, `Diagnostico_Questoes_${clName}.${format}`);
}

// --- Comparison Report Exports ---
function getCompareSelectedExams() {
  const sel1 = document.getElementById("page-rep-exam-select") || document.getElementById("compare-select-exam1");
  const sel2 = document.getElementById("compare-select-exam2");

  let exam1Id = (sel1 && sel1.value) || (currentComparisonData && currentComparisonData.exam1 && currentComparisonData.exam1.id) || activeReportExamId || "";
  let exam2Id = (sel2 && sel2.value) || (currentComparisonData && currentComparisonData.exam2 && currentComparisonData.exam2.id) || "";

  // If sel2 is empty, pick the first option with a different ID
  if (!exam2Id && sel2 && sel2.options && sel2.options.length > 0) {
    for (let i = 0; i < sel2.options.length; i++) {
      if (sel2.options[i].value && sel2.options[i].value !== exam1Id) {
        exam2Id = sel2.options[i].value;
        sel2.selectedIndex = i;
        break;
      }
    }
  }

  return { exam1Id, exam2Id };
}

function exportCompareReport(format) {
  closeAllExportDropdowns();
  if (!activeReportClassId) {
    showToast("Nenhuma turma ativa selecionada.", "error");
    return;
  }
  const { exam1Id, exam2Id } = getCompareSelectedExams();
  if (!exam1Id || !exam2Id) {
    showToast("Selecione dois gabaritos para comparar.", "error");
    return;
  }
  if (exam1Id === exam2Id) {
    showToast("Selecione dois gabaritos diferentes para gerar o comparativo.", "warning");
    return;
  }
  const clName = getActiveClassNameClean();
  downloadReport(`/api/reports/compare/${activeReportClassId}?exam1=${exam1Id}&exam2=${exam2Id}&format=${format}`, `Comparativo_Gabaritos_${clName}.${format}`);
}

function exportCompareCsv() {
  closeAllExportDropdowns();
  if (!activeReportClassId) {
    showToast("Nenhuma turma ativa selecionada.", "error");
    return;
  }
  const { exam1Id, exam2Id } = getCompareSelectedExams();
  if (!exam1Id || !exam2Id) {
    showToast("Selecione dois gabaritos para comparar.", "error");
    return;
  }
  const clName = getActiveClassNameClean();
  downloadReport(`/api/classrooms/${activeReportClassId}/compare/csv?exam1=${exam1Id}&exam2=${exam2Id}`, `Comparativo_Gabaritos_${clName}.csv`);
}

function exportClassroomCsv() {
  closeAllExportDropdowns();
  if (!activeReportClassId) {
    showToast("Nenhuma turma ativa selecionada.", "error");
    return;
  }
  const examSelect = document.getElementById("page-rep-exam-select");
  const examId = (examSelect && examSelect.value) || activeReportExamId;
  if (!examId) {
    showToast("Selecione um simulado vinculado para exportar CSV.", "error");
    return;
  }
  const clName = getActiveClassNameClean();
  downloadReport(`/api/classrooms/${activeReportClassId}/exams/${examId}/report/csv`, `Relatorio_Turma_${clName}.csv`);
}

// --- Network Overview Exports ---
function exportNetworkReport(format) {
  closeAllExportDropdowns();
  downloadReport(`/api/reports/schools-overview?format=${format}`, `panoramico_rede_escolar.${format}`);
}

// --- Unified Report Export Modal Logic ---
let currentExportModalContext = "classroom";
let selectedExportModalReport = "class_summary";
let selectedExportModalFormat = "pdf";
let activeExportSchoolId = null;

function getActiveSchoolNameClean(schoolId) {
  let name = "Escola";
  if (schoolId && Array.isArray(schoolsList)) {
    const found = schoolsList.find(s => s.id === schoolId);
    if (found && found.name) name = found.name;
  }
  return name
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-zA-Z0-9_-]/g, "_")
    .replace(/_+/g, "_")
    .replace(/^_+|_+$/g, "");
}

function exportSchoolReport(format = "pdf") {
  closeAllExportDropdowns();
  if (!activeExportSchoolId) {
    showToast("Nenhuma escola selecionada para exportação.", "error");
    return;
  }
  const schName = getActiveSchoolNameClean(activeExportSchoolId);
  downloadReport(`/api/reports/school/${activeExportSchoolId}?format=${format}`, `Relatorio_Escola_${schName}.${format}`);
}

const EXPORT_REPORT_DEFINITIONS = {
  classroom: [
    {
      id: "class_summary",
      title: "Relatório da Turma",
      desc: "Médias, notas e lista de presença",
      icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>'
    },
    {
      id: "class_diagnostic",
      title: "Diagnóstico por Questão",
      desc: "Acertos item a item e habilidades",
      icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>'
    },
    {
      id: "class_compare",
      title: "Comparativo de Gabaritos",
      desc: "Evolução entre Gabarito A e B",
      icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>'
    }
  ],
  school: [
    {
      id: "school_performance",
      title: "Relatório da Escola",
      desc: "Turmas por prova, Quadro de Honra e Melhores por Série",
      icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>'
    }
  ],
  network: [
    {
      id: "network_overview",
      title: "Panorâmico da Rede",
      desc: "Escolas, turmas e matrículas",
      icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>'
    },
    {
      id: "year_performance",
      title: "Rendimento por Ano",
      desc: "Desempenho da rede do 1º ao 9º ano",
      icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20V10M18 20V4M6 20v-4"/></svg>'
    }
  ],
  year: [
    {
      id: "year_performance",
      title: "Rendimento por Ano",
      desc: "Desempenho da rede do 1º ao 9º ano",
      icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20V10M18 20V4M6 20v-4"/></svg>'
    }
  ]
};

function openExportReportModal(context, preferredReport, preferredFormat, targetId) {
  closeAllExportDropdowns();

  if (targetId) {
    activeExportSchoolId = targetId;
  }

  if (!context) {
    const pageClassroom = document.getElementById("page-classroom-report");
    if (pageClassroom && pageClassroom.style.display !== "none" && activeReportClassId) {
      context = "classroom";
    } else {
      context = "network";
    }
  }

  currentExportModalContext = context;

  // Set context subtitle
  const subEl = document.getElementById("export-modal-subtitle");
  if (subEl) {
    if (context === "classroom") {
      const titleEl = document.getElementById("page-rep-class-title");
      const schoolEl = document.getElementById("page-rep-school-subtitle");
      const rawTitle = titleEl ? titleEl.textContent.replace(/^Relat[óo]rio da Turma:?\s*/i, "").trim() : "Turma";
      const schTxt = schoolEl ? schoolEl.textContent : "";
      subEl.textContent = `${rawTitle} ${schTxt ? '• ' + schTxt : ''}`.trim();
    } else if (context === "school") {
      let schName = "Escola";
      if (activeExportSchoolId && Array.isArray(schoolsList)) {
        const found = schoolsList.find(s => s.id === activeExportSchoolId);
        if (found && found.name) schName = found.name;
      }
      subEl.textContent = `${schName} • Relatório de Desempenho`;
    } else if (context === "network") {
      subEl.textContent = "Rede Municipal • Lagoa da Canoa";
    } else if (context === "year") {
      subEl.textContent = "Rendimento por Ano Escolar";
    }
  }

  // Pre-select report
  if (preferredReport) {
    selectedExportModalReport = preferredReport;
  } else if (context === "classroom") {
    const btnCompare = document.getElementById("btn-subnav-compare");
    const isCompareActive = btnCompare && btnCompare.classList.contains("active");
    selectedExportModalReport = isCompareActive ? "class_compare" : "class_summary";
  } else if (context === "school") {
    selectedExportModalReport = "school_performance";
  } else if (context === "network") {
    selectedExportModalReport = "network_overview";
  } else if (context === "year") {
    selectedExportModalReport = "year_performance";
  }

  selectedExportModalFormat = preferredFormat || "pdf";

  renderExportReportTypes(context);
  selectExportModalFormat(selectedExportModalFormat);

  const modal = document.getElementById("modal-export-report");
  if (modal) {
    modal.style.display = "flex";
  }
}

function closeExportReportModal() {
  const modal = document.getElementById("modal-export-report");
  if (modal) {
    modal.style.display = "none";
  }
}

function renderExportReportTypes(context) {
  const container = document.getElementById("export-report-types-list");
  if (!container) return;

  const defs = EXPORT_REPORT_DEFINITIONS[context] || EXPORT_REPORT_DEFINITIONS.classroom;
  if (!defs.some(d => d.id === selectedExportModalReport)) {
    selectedExportModalReport = defs[0].id;
  }

  container.innerHTML = defs.map(d => {
    const isActive = d.id === selectedExportModalReport;
    return `
      <div class="export-report-card ${isActive ? 'active' : ''}" data-report="${d.id}" onclick="selectExportModalReport('${d.id}')">
        <div class="export-card-icon">${d.icon}</div>
        <div class="export-card-body">
          <div class="export-card-title">${escapeHtml(d.title)}</div>
          <div class="export-card-desc">${escapeHtml(d.desc)}</div>
        </div>
        <div class="export-radio-indicator">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.5">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
        </div>
      </div>
    `;
  }).join("");
}

function selectExportModalReport(reportId) {
  selectedExportModalReport = reportId;
  const cards = document.querySelectorAll("#export-report-types-list .export-report-card");
  cards.forEach(card => {
    if (card.getAttribute("data-report") === reportId) {
      card.classList.add("active");
    } else {
      card.classList.remove("active");
    }
  });
}

function selectExportModalFormat(format) {
  selectedExportModalFormat = format;
  const cards = document.querySelectorAll(".export-formats-grid .export-format-card");
  cards.forEach(card => {
    if (card.getAttribute("data-format") === format) {
      card.classList.add("active");
    } else {
      card.classList.remove("active");
    }
  });
}

function executeModalReportExport() {
  const r = selectedExportModalReport;
  const fmt = selectedExportModalFormat;

  closeExportReportModal();

  if (r === "class_summary") {
    if (fmt === "csv") {
      exportClassroomCsv();
    } else {
      exportClassroomReport(fmt);
    }
  } else if (r === "class_diagnostic") {
    if (fmt === "csv") {
      exportClassroomCsv();
    } else {
      exportClassroomDiagnostic(fmt);
    }
  } else if (r === "class_compare") {
    if (fmt === "csv") {
      exportCompareCsv();
    } else {
      exportCompareReport(fmt);
    }
  } else if (r === "school_performance") {
    exportSchoolReport(fmt);
  } else if (r === "network_overview") {
    exportNetworkReport(fmt);
  } else if (r === "year_performance") {
    exportYearPerformance(fmt);
  }
}

function escapeHtml(str) {
  if (str == null) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// --- Year Performance Interactive Report & Modal (R2) ---
let currentYearReportStudents = [];

async function openYearReportModal() {
  const modal = document.getElementById("year-report-modal");
  if (!modal) return;

  // Show modal immediately for responsive feedback
  modal.style.display = "flex";

  // Ensure schoolsList is loaded if opened directly from top navigation
  if (!schoolsList || schoolsList.length === 0) {
    try {
      const res = await fetch("/api/schools");
      if (res.ok) schoolsList = await res.json();
    } catch (e) {
      console.warn("Falha ao pré-carregar lista de escolas:", e);
    }
  }

  // Ensure examsList is loaded
  if (!examsList || examsList.length === 0) {
    try {
      const res = await fetch("/api/exams");
      if (res.ok) examsList = await res.json();
    } catch (e) {
      console.warn("Falha ao pré-carregar lista de gabaritos:", e);
    }
  }

  // Populate school select
  const schoolSelect = document.getElementById("year-rep-school-select");
  if (schoolSelect) {
    const currentVal = schoolSelect.value;
    schoolSelect.innerHTML = '<option value="">🌐 Toda a Rede Municipal</option>';
    if (Array.isArray(schoolsList) && schoolsList.length > 0) {
      schoolsList.forEach(s => {
        schoolSelect.innerHTML += `<option value="${s.id}">🏫 ${escapeHtml(s.name)}</option>`;
      });
    }
    if (currentVal) schoolSelect.value = currentVal;
  }

  // Populate exams filtered specifically for the selected school year / grade
  await updateYearReportExamsDropdown();

  await loadYearReportData();
}

async function updateYearReportExamsDropdown() {
  const gradeSel = document.getElementById("year-rep-grade-select");
  const schoolSel = document.getElementById("year-rep-school-select");
  const examSel = document.getElementById("year-rep-exam-select");
  if (!examSel) return;

  const grade = gradeSel ? gradeSel.value : "";
  const schoolId = schoolSel ? schoolSel.value : "";
  const previousSelectedExam = examSel.value;

  const params = new URLSearchParams();
  if (grade) params.append("grade_year", grade);
  if (schoolId) params.append("school_id", schoolId);

  examSel.innerHTML = '<option value="">Carregando simulados...</option>';

  try {
    const res = await fetch(`/api/reports/year-exams?${params.toString()}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const filteredExams = await res.json();

    const gradeLabel = grade || "Rede Geral";

    if (Array.isArray(filteredExams) && filteredExams.length > 0) {
      let html = `<option value="">Todos os simulados (${escapeHtml(gradeLabel)}) — Consolidado</option>`;
      let foundPrevious = false;
      filteredExams.forEach(e => {
        const qInfo = e.num_questions ? ` (${e.num_questions} questões)` : "";
        const isSelected = (previousSelectedExam && e.id === previousSelectedExam) ? "selected" : "";
        if (isSelected) foundPrevious = true;
        html += `<option value="${e.id}" ${isSelected}>📝 ${escapeHtml(e.title)}${qInfo}</option>`;
      });
      examSel.innerHTML = html;
      if (!foundPrevious && previousSelectedExam) {
        examSel.value = "";
      }
    } else {
      examSel.innerHTML = `<option value="">Nenhum simulado vinculado a este ano</option>`;
      examSel.value = "";
    }
  } catch (err) {
    console.warn("Erro ao buscar gabaritos vinculados por ano:", err);
    // Fallback using examsList
    examSel.innerHTML = '<option value="">Todos os simulados (Consolidado)</option>';
    if (Array.isArray(examsList)) {
      examsList.forEach(e => {
        examSel.innerHTML += `<option value="${e.id}">📝 ${escapeHtml(e.title)}</option>`;
      });
    }
  }
}

function closeYearReportModal() {
  const modal = document.getElementById("year-report-modal");
  if (modal) modal.style.display = "none";
}

async function loadYearReportData() {
  const gradeSel = document.getElementById("year-rep-grade-select");
  const schoolSel = document.getElementById("year-rep-school-select");
  const examSel = document.getElementById("year-rep-exam-select");
  const tbody = document.getElementById("year-rep-tbody");

  const grade = gradeSel ? gradeSel.value : "";
  const schoolId = schoolSel ? schoolSel.value : "";
  const examId = examSel ? examSel.value : "";

  if (tbody) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 2.5rem; color: var(--text-secondary);">Carregando dados de rendimento dos estudantes...</td></tr>';
  }

  const params = new URLSearchParams();
  if (grade) params.append("grade_year", grade);
  if (schoolId) params.append("school_id", schoolId);
  if (examId) params.append("exam_id", examId);
  params.append("format", "json");

  try {
    const res = await fetch(`/api/reports/year-performance?${params.toString()}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    // Update KPI summary cards
    const totalEl = document.getElementById("year-kpi-total");
    const gradedEl = document.getElementById("year-kpi-graded");
    const avgEl = document.getElementById("year-kpi-avg");
    const highestEl = document.getElementById("year-kpi-highest");
    const countEl = document.getElementById("year-rep-results-count");

    if (totalEl) totalEl.textContent = data.total_students || 0;
    if (gradedEl) gradedEl.textContent = data.graded_students || 0;
    if (avgEl) avgEl.textContent = (data.average_score != null ? data.average_score.toFixed(1) : "0.0") + " pts";
    if (highestEl) highestEl.textContent = (data.highest_score != null ? data.highest_score.toFixed(1) : "0.0") + " pts";
    if (countEl) countEl.textContent = `${data.total_students || 0} alunos`;

    currentYearReportStudents = data.students || [];
    renderYearReportTable(currentYearReportStudents);
  } catch (err) {
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 2rem; color: #dc2626;">Erro ao carregar relatório: ${escapeHtml(err.message)}</td></tr>`;
    }
  }
}

function renderYearReportTable(students) {
  const tbody = document.getElementById("year-rep-tbody");
  if (!tbody) return;

  if (!students || students.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 2.5rem; color: var(--text-secondary);">Nenhum estudante encontrado para os filtros selecionados.</td></tr>';
    return;
  }

  let html = "";
  students.forEach((s, idx) => {
    const isGraded = s.status === "CORRIGIDO" && s.score != null;
    let rankBadge = "";
    if (s.rank === 1) {
      rankBadge = '<span style="display: inline-flex; align-items: center; justify-content: center; width: 26px; height: 26px; border-radius: 50%; background: #fef08a; color: #854d0e; font-weight: 800; font-size: 0.78rem;">1º</span>';
    } else if (s.rank === 2) {
      rankBadge = '<span style="display: inline-flex; align-items: center; justify-content: center; width: 26px; height: 26px; border-radius: 50%; background: #e2e8f0; color: #475569; font-weight: 800; font-size: 0.78rem;">2º</span>';
    } else if (s.rank === 3) {
      rankBadge = '<span style="display: inline-flex; align-items: center; justify-content: center; width: 26px; height: 26px; border-radius: 50%; background: #fed7aa; color: #9a3412; font-weight: 800; font-size: 0.78rem;">3º</span>';
    } else {
      rankBadge = s.rank && s.rank !== "-" ? `<span style="font-weight: 700; color: #64748b;">${s.rank}º</span>` : '<span style="color: #94a3b8;">-</span>';
    }

    const scoreDisplay = isGraded 
      ? `<span style="font-weight: 800; font-size: 0.95rem; color: #0284c7;">${s.score.toFixed(1)}</span>`
      : '<span style="color: #94a3b8;">-</span>';

    const pctDisplay = isGraded && s.percentage != null
      ? `<span style="font-weight: 600;">${s.percentage.toFixed(1)}%</span>`
      : '<span style="color: #94a3b8;">-</span>';

    const statusBadge = isGraded
      ? '<span class="status-badge status-graded">Corrigido</span>'
      : '<span class="status-badge status-pending">Pendente</span>';

    html += `
      <tr style="${idx % 2 === 1 ? 'background: #f8fafc;' : ''}">
        <td style="text-align: center; vertical-align: middle;">${rankBadge}</td>
        <td style="font-weight: 600; color: #0f172a; vertical-align: middle;">${escapeHtml(s.name)}</td>
        <td style="color: #334155; font-size: 0.85rem; vertical-align: middle;">${escapeHtml(s.school_name || "-")}</td>
        <td style="text-align: center; vertical-align: middle;"><span class="badge badge-neutral" style="font-size: 0.75rem;">${escapeHtml(s.classroom_name || "-")}</span></td>
        <td style="text-align: center; vertical-align: middle;">${scoreDisplay}</td>
        <td style="text-align: center; vertical-align: middle;">${pctDisplay}</td>
        <td style="text-align: center; vertical-align: middle;">${statusBadge}</td>
      </tr>
    `;
  });

  tbody.innerHTML = html;
}

function filterYearReportTable() {
  const q = (document.getElementById("year-rep-search-input")?.value || "").trim().toLowerCase();
  if (!q) {
    renderYearReportTable(currentYearReportStudents);
    return;
  }
  const filtered = currentYearReportStudents.filter(s => 
    (s.name && s.name.toLowerCase().includes(q)) ||
    (s.school_name && s.school_name.toLowerCase().includes(q)) ||
    (s.classroom_name && s.classroom_name.toLowerCase().includes(q))
  );
  renderYearReportTable(filtered);
}

function exportYearPerformance(format) {
  const gradeSel = document.getElementById("year-rep-grade-select");
  const schoolSel = document.getElementById("year-rep-school-select");
  const examSel = document.getElementById("year-rep-exam-select");

  const grade = gradeSel ? gradeSel.value : "";
  const schoolId = schoolSel ? schoolSel.value : "";
  const examId = examSel ? examSel.value : "";

  const params = new URLSearchParams();
  if (grade) params.append("grade_year", grade);
  if (schoolId) params.append("school_id", schoolId);
  if (examId) params.append("exam_id", examId);
  params.append("format", format);

  const gradeSlug = grade ? grade.replace(/\s+/g, "_").toLowerCase() : "rede_geral";
  downloadReport(`/api/reports/year-performance?${params.toString()}`, `rendimento_${gradeSlug}.${format}`);
}

// --- Institutional System Settings & Coat of Arms (Brasão) ---
async function loadSystemSettings() {
  try {
    const res = await fetch("/api/settings");
    if (!res.ok) return;
    const settings = await res.json();
    if (settings) {
      if (document.getElementById("settings-prefeitura")) {
        document.getElementById("settings-prefeitura").value = settings.prefeitura_name || "";
      }
      if (document.getElementById("settings-secretaria")) {
        document.getElementById("settings-secretaria").value = settings.secretaria_name || "";
      }
      if (document.getElementById("settings-state")) {
        document.getElementById("settings-state").value = settings.state_name || "";
      }

      const ts = new Date().getTime();
      const hasLogo = !!settings.has_logo;
      const logoUrl = hasLogo ? `/api/settings/logo?t=${ts}` : null;

      // Settings modal preview
      const modalLogoImg = document.getElementById("settings-logo-img");
      if (modalLogoImg && logoUrl) {
        modalLogoImg.src = logoUrl;
      }

      // Header logo & fallback icon
      const headerBrandImg = document.getElementById("header-brand-img");
      const headerBrandFallback = document.getElementById("header-brand-fallback");
      if (headerBrandImg) {
        if (hasLogo && logoUrl) {
          headerBrandImg.src = logoUrl;
          headerBrandImg.style.display = "block";
          if (headerBrandFallback) headerBrandFallback.style.display = "none";
        } else {
          headerBrandImg.style.display = "none";
          if (headerBrandFallback) headerBrandFallback.style.display = "flex";
        }
      }

      // Header subtitle text
      const headerSubtitle = document.getElementById("header-brand-subtitle");
      if (headerSubtitle) {
        const sub = settings.secretaria_name || settings.prefeitura_name || "Sistema de Gestão & Avaliação";
        headerSubtitle.textContent = sub;
      }

      // Login screen branding updates
      const loginLogo = document.getElementById("login-brand-img") || document.getElementById("login-logo-img");
      if (loginLogo && hasLogo && logoUrl) {
        loginLogo.src = logoUrl;
        loginLogo.style.display = "block";
        const fallback = document.getElementById("login-brand-fallback");
        if (fallback) fallback.style.display = "none";
      }
      const loginCity = document.getElementById("login-city-name") || document.querySelector(".login-badge-city");
      if (loginCity && (settings.prefeitura_name || settings.state_name)) {
        loginCity.textContent = `${settings.prefeitura_name || "Lagoa da Canoa"} ${settings.state_name ? "— " + settings.state_name : ""}`;
      }
      const loginSub = document.getElementById("login-sub-text") || document.getElementById("login-sec-name");
      if (loginSub && (settings.secretaria_name || settings.prefeitura_name)) {
        loginSub.textContent = settings.secretaria_name || settings.prefeitura_name;
      }
    }
  } catch (e) {
    console.warn("Erro ao carregar configurações:", e);
  }
}

function openSettingsModal() {
  if (currentUserProfile && currentUserProfile.role === "professor") {
    showToast("Acesso restrito. Professores têm acesso exclusivo à Correção de Provas.", "warning");
    return;
  }
  loadSystemSettings();
  const modal = document.getElementById("settings-modal");
  if (modal) modal.style.display = "flex";
}

function closeSettingsModal() {
  const modal = document.getElementById("settings-modal");
  if (modal) modal.style.display = "none";
}

async function saveSystemSettings() {
  const prefeitura = document.getElementById("settings-prefeitura") ? document.getElementById("settings-prefeitura").value.trim() : "";
  const secretaria = document.getElementById("settings-secretaria") ? document.getElementById("settings-secretaria").value.trim() : "";
  const state = document.getElementById("settings-state") ? document.getElementById("settings-state").value.trim() : "";
  const newPwd = document.getElementById("settings-new-pwd") ? document.getElementById("settings-new-pwd").value : "";
  const confirmPwd = document.getElementById("settings-confirm-pwd") ? document.getElementById("settings-confirm-pwd").value : "";

  try {
    // Check if password change was requested
    if (newPwd) {
      if (newPwd !== confirmPwd) {
        throw new Error("A confirmação da nova senha não confere.");
      }
      if (newPwd.length < 4) {
        throw new Error("A nova senha deve ter no mínimo 4 caracteres.");
      }
      const pwdRes = await fetch("/api/auth/change-password", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...getAuthHeaders() },
        body: JSON.stringify({ new_password: newPwd })
      });
      const pwdData = await pwdRes.json();
      if (!pwdRes.ok) {
        throw new Error(pwdData.detail || "Erro ao atualizar senha de acesso.");
      }
      if (document.getElementById("settings-new-pwd")) document.getElementById("settings-new-pwd").value = "";
      if (document.getElementById("settings-confirm-pwd")) document.getElementById("settings-confirm-pwd").value = "";
    }

    const res = await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getAuthHeaders() },
      body: JSON.stringify({
        prefeitura_name: prefeitura,
        secretaria_name: secretaria,
        state_name: state
      })
    });
    if (!res.ok) throw new Error("Erro ao salvar configurações institucionais.");
    showToast("Configurações salvas com sucesso!", "success");
    await loadSystemSettings();
    closeSettingsModal();
  } catch (e) {
    showToast(e.message, "error");
  }
}

async function handleLogoUpload(file) {
  if (!file) return;
  const formData = new FormData();
  formData.append("file", file);

  try {
    showToast("Enviando Brasão oficial...", "info");
    const res = await fetch("/api/settings/logo", {
      method: "POST",
      headers: { ...getAuthHeaders() },
      body: formData
    });
    if (!res.ok) throw new Error("Erro no upload do arquivo do Brasão");
    
    const ts = new Date().getTime();
    const logoUrl = `/api/settings/logo?t=${ts}`;
    const modalLogoImg = document.getElementById("settings-logo-img");
    if (modalLogoImg) {
      modalLogoImg.src = logoUrl;
    }
    const headerBrandImg = document.getElementById("header-brand-img");
    const headerBrandFallback = document.getElementById("header-brand-fallback");
    if (headerBrandImg) {
      headerBrandImg.src = logoUrl;
      headerBrandImg.style.display = "block";
    }
    if (headerBrandFallback) {
      headerBrandFallback.style.display = "none";
    }

    showToast("Brasão institucional atualizado com sucesso!", "success");
  } catch (e) {
    showToast(e.message, "error");
  }
}

// Expose modal and page functions to global window for inline onclick handlers
window.openNewSchoolModal = openNewSchoolModal;
window.closeNewSchoolModal = closeNewSchoolModal;
window.deleteSchoolConfirm = deleteSchoolConfirm;
window.deleteClassroomConfirm = deleteClassroomConfirm;
window.openCsvModal = openCsvModal;
window.closeCsvModal = closeCsvModal;
window.openBatchModal = openBatchModal;
window.closeBatchModal = closeBatchModal;
window.openReportModal = openClassroomReportPage;
window.closeReportModal = closeClassroomReportPage;
window.openClassroomReportPage = openClassroomReportPage;
window.closeClassroomReportPage = closeClassroomReportPage;
window.loadClassroomReportPage = loadClassroomReportPage;
window.switchReportSubTab = switchReportSubTab;
window.loadClassroomComparison = loadClassroomComparison;
window.setupComparisonSelectors = setupComparisonSelectors;
window.openLinkExamsModal = openLinkExamsModal;
window.closeLinkExamsModal = closeLinkExamsModal;
window.saveLinkedExams = saveLinkedExams;
window.toggleStudentList = toggleStudentList;
window.openSettingsModal = openSettingsModal;
window.closeSettingsModal = closeSettingsModal;
window.saveSystemSettings = saveSystemSettings;
window.openYearReportModal = openYearReportModal;
window.closeYearReportModal = closeYearReportModal;
window.openEditClassroomModal = openEditClassroomModal;
window.closeEditClassroomModal = closeEditClassroomModal;
window.exportClassroomReport = exportClassroomReport;
window.exportClassroomDiagnostic = exportClassroomDiagnostic;
window.exportClassroomCsv = exportClassroomCsv;
window.exportCompareReport = exportCompareReport;
window.exportCompareCsv = exportCompareCsv;
window.exportNetworkReport = exportNetworkReport;
window.exportYearPerformance = exportYearPerformance;
window.exportSchoolReport = exportSchoolReport;
window.openExportReportModal = openExportReportModal;
window.closeExportReportModal = closeExportReportModal;
window.selectExportModalReport = selectExportModalReport;
window.selectExportModalFormat = selectExportModalFormat;
window.executeModalReportExport = executeModalReportExport;
window.updateYearReportExamsDropdown = updateYearReportExamsDropdown;
window.toggleExportDropdown = toggleExportDropdown;
window.clearSchoolsSearch = clearSchoolsSearch;
window.clearExamsSearch = clearExamsSearch;

// Real-time search listeners for Schools & Classrooms
const schoolsSearchInput = document.getElementById("schools-search-input");
const schoolsSearchClear = document.getElementById("schools-search-clear");
if (schoolsSearchInput) {
  schoolsSearchInput.addEventListener("input", (e) => {
    const term = e.target.value.trim();
    if (schoolsSearchClear) {
      schoolsSearchClear.style.display = term ? "flex" : "none";
    }
    renderSchoolsGrid(term);
  });

  schoolsSearchInput.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      clearSchoolsSearch();
      schoolsSearchInput.blur();
    }
  });
}
if (schoolsSearchClear) {
  schoolsSearchClear.addEventListener("click", clearSchoolsSearch);
}

// Real-time search listeners for Exams / Simulados
const examsSearchInput = document.getElementById("exams-search-input");
const examsSearchClear = document.getElementById("exams-search-clear");
const examsSearchKbd = document.getElementById("exams-search-kbd");

if (examsSearchInput) {
  examsSearchInput.addEventListener("input", (e) => {
    const term = e.target.value.trim();
    if (examsSearchClear) {
      examsSearchClear.style.display = term ? "flex" : "none";
    }
    if (examsSearchKbd) {
      examsSearchKbd.style.display = term ? "none" : "inline-flex";
    }
    renderExamsGrid(term);
  });

  examsSearchInput.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      clearExamsSearch();
      examsSearchInput.blur();
    }
  });
}
if (examsSearchClear) {
  examsSearchClear.addEventListener("click", clearExamsSearch);
}

// Global keyboard shortcut ('/' to focus search)
document.addEventListener("keydown", (e) => {
  if (e.key === "/" && !["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement?.tagName) && !document.activeElement?.isContentEditable) {
    const examsTab = document.getElementById("exams-tab");
    const schoolsTab = document.getElementById("schools-tab");

    if (examsTab && examsTab.classList.contains("active") && examsSearchInput) {
      e.preventDefault();
      examsSearchInput.focus();
      examsSearchInput.select();
    } else if (schoolsTab && schoolsTab.classList.contains("active") && schoolsSearchInput) {
      e.preventDefault();
      schoolsSearchInput.focus();
      schoolsSearchInput.select();
    }
  }
});

// =========================================================================
// AUTHENTICATION & ACCESS CONTROL MODULE
// =========================================================================
const AUTH_TOKEN_KEY = "semed_auth_token";

function getAuthToken() {
  return localStorage.getItem(AUTH_TOKEN_KEY) || sessionStorage.getItem(AUTH_TOKEN_KEY) || "";
}

function setAuthToken(token, remember = false) {
  if (remember) {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
    sessionStorage.removeItem(AUTH_TOKEN_KEY);
  } else {
    sessionStorage.setItem(AUTH_TOKEN_KEY, token);
    localStorage.removeItem(AUTH_TOKEN_KEY);
  }
}

function clearAuthToken() {
  localStorage.removeItem(AUTH_TOKEN_KEY);
  sessionStorage.removeItem(AUTH_TOKEN_KEY);
}

function getAuthHeaders() {
  const token = getAuthToken();
  return token ? {
    "Authorization": `Bearer ${token}`,
    "X-Auth-Token": token
  } : {};
}

let currentUserProfile = null;

function updateNavUserBadge(rawUser) {
  if (!rawUser) return;
  const user = rawUser.user ? rawUser.user : rawUser;
  currentUserProfile = user;
  
  const avatarEl = document.getElementById("nav-user-avatar");
  const nameEl = document.getElementById("nav-user-name");
  const roleEl = document.getElementById("nav-user-role");
  const legacyBadge = document.getElementById("nav-user-badge");
  
  const displayName = user.name || user.username || "admin";
  if (nameEl) nameEl.textContent = displayName;
  if (legacyBadge) legacyBadge.textContent = displayName;

  const parts = displayName.trim().split(/\s+/);
  let initials = "AD";
  if (parts.length >= 2 && parts[0] && parts[parts.length - 1]) {
    initials = (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  } else if (parts.length === 1 && parts[0].length > 0) {
    initials = parts[0].substring(0, Math.min(2, parts[0].length)).toUpperCase();
  }

  if (avatarEl) avatarEl.textContent = initials;

  const role = user.role || "admin";
  let roleText = "Operador";
  if (role === "admin") roleText = "SEMED (Admin)";
  else if (role === "coordenador") roleText = "Coordenação";
  else if (role === "professor") roleText = "Professor";
  const roleTextDisplay = user.role_display || roleText;
  if (roleEl) roleEl.textContent = roleTextDisplay;

  // Atualizar badges da navegação mobile (Header e Drawer)
  const mobHeaderAvatar = document.getElementById("mobile-header-avatar");
  const mobDrawerAvatar = document.getElementById("mobile-drawer-avatar");
  const mobDrawerName = document.getElementById("mobile-drawer-name");
  const mobDrawerRole = document.getElementById("mobile-drawer-role");

  if (mobHeaderAvatar) mobHeaderAvatar.textContent = initials;
  if (mobDrawerAvatar) mobDrawerAvatar.textContent = initials;
  if (mobDrawerName) mobDrawerName.textContent = displayName;
  if (mobDrawerRole) mobDrawerRole.textContent = roleTextDisplay;

  // Apply role-based access permissions to the entire UI
  applyRolePermissions(role);
}

function applyRolePermissions(role) {
  if (!role && currentUserProfile) role = currentUserProfile.role;
  if (!role) role = "admin";

  const newSchoolBtn = document.getElementById("btn-open-new-school-modal");
  const importCsvBtn = document.getElementById("btn-open-csv-modal");
  const adminDropdownWrap = document.getElementById("wrap-admin-dropdown");
  const backupMenuItem = document.getElementById("menu-item-backup");

  document.body.classList.remove("role-admin", "role-coordenador", "role-professor");

  if (role === "admin") {
    document.body.classList.add("role-admin");
    document.querySelectorAll('.tab-btn').forEach(btn => btn.style.display = "");
    if (adminDropdownWrap) adminDropdownWrap.style.display = "";
    if (backupMenuItem) backupMenuItem.style.display = "";
    if (newSchoolBtn) newSchoolBtn.style.display = "";
    if (importCsvBtn) importCsvBtn.style.display = "";
  } else if (role === "coordenador") {
    document.body.classList.add("role-coordenador");
    // Coordenador tem acesso a turmas, simulados e itens de gestão permitidos
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.style.display = (btn.dataset.tab === "backup-tab") ? "none" : "";
    });
    if (adminDropdownWrap) adminDropdownWrap.style.display = "";
    if (backupMenuItem) backupMenuItem.style.display = "none";
    if (newSchoolBtn) newSchoolBtn.style.display = "";
    if (importCsvBtn) importCsvBtn.style.display = "";

    const activeBtn = document.querySelector('.tab-btn.active');
    if (activeBtn && activeBtn.dataset.tab === "backup-tab") {
      switchTab("dashboard-tab");
    }
  } else {
    // Professor: acesso exclusivo à Correção de Provas (scanner-tab)
    document.body.classList.add("role-professor");
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.style.display = (btn.dataset.tab === "scanner-tab") ? "" : "none";
    });
    if (adminDropdownWrap) adminDropdownWrap.style.display = "none";
    if (newSchoolBtn) newSchoolBtn.style.display = "none";
    if (importCsvBtn) importCsvBtn.style.display = "none";

    // Aplicar restrição para itens exclusivos de admin em todo o sistema
    document.querySelectorAll(".admin-only-item").forEach(el => {
      el.style.display = (role === "admin") ? "" : "none";
    });

    // Se professor, oculta abas restritas na barra inferior e menu mobile
    if (role === "professor") {
      document.querySelectorAll('.bottom-nav-btn[data-tab]').forEach(btn => {
        btn.style.display = (btn.dataset.tab === "scanner-tab") ? "" : "none";
      });
      document.querySelectorAll('.mobile-drawer-item[data-tab]').forEach(btn => {
        btn.style.display = (btn.dataset.tab === "scanner-tab") ? "" : "none";
      });
      const quickAction = document.querySelector('.mobile-drawer-quick-action');
      if (quickAction) quickAction.style.display = "none";
    } else {
      document.querySelectorAll('.bottom-nav-btn, .mobile-drawer-item').forEach(btn => {
        if (!btn.classList.contains("admin-only-item") || role === "admin") {
          btn.style.display = "";
        }
      });
      const quickAction = document.querySelector('.mobile-drawer-quick-action');
      if (quickAction) quickAction.style.display = "";
    }

    // Se estiver em outra aba, força redirecionamento imediato para a tela de Correção
    const activeBtn = document.querySelector('.tab-btn.active');
    if (!activeBtn || activeBtn.dataset.tab !== "scanner-tab") {
      switchTab("scanner-tab");
    }
  }
}

function restoreActiveTab(user) {
  if (user && user.role === "professor") {
    switchTab("scanner-tab");
    return;
  }

  // Verificar se o usuário estava na subpágina de relatório de turma
  let subpage = null;
  try {
    const raw = localStorage.getItem("omr_active_subpage");
    if (raw) subpage = JSON.parse(raw);
  } catch (e) {}

  if (subpage && subpage.type === "classroom-report" && subpage.classId) {
    switchTab("schools-tab");
    setTimeout(async () => {
      if (!schoolsList || schoolsList.length === 0) {
        try {
          const res = await fetch("/api/schools");
          if (res.ok) schoolsList = await res.json();
        } catch (e) {}
      }
      openClassroomReportPage(subpage.classId, subpage.className, subpage.schoolName);
    }, 120);
    return;
  }

  let savedTab = null;
  try {
    savedTab = localStorage.getItem("omr_active_tab");
  } catch (e) {}

  const validTabs = ["dashboard-tab", "scanner-tab", "exams-tab", "schools-tab", "create-tab"];
  if (user && user.role === "admin") {
    validTabs.push("users-tab", "backup-tab");
  } else if (user && user.role === "coordenador") {
    validTabs.push("users-tab");
  }

  if (savedTab && validTabs.includes(savedTab)) {
    switchTab(savedTab);
  } else {
    switchTab("dashboard-tab");
  }
}

async function checkAuthStatus() {
  const token = getAuthToken();
  const loginScreen = document.getElementById("login-screen");

  if (!token) {
    if (loginScreen) {
      loginScreen.style.display = "flex";
      document.body.classList.add("login-locked");
    }
    return false;
  }

  try {
    const res = await fetch("/api/auth/me", {
      headers: { ...getAuthHeaders() }
    });
    if (res.ok) {
      const data = await res.json();
      const user = data.user || data;
      if (loginScreen) {
        loginScreen.style.display = "none";
        document.body.classList.remove("login-locked");
      }
      updateNavUserBadge(user);

      // Pouso inteligente: restaura exatamente a aba ou subpágina em que o usuário estava antes do refresh
      restoreActiveTab(user);
      checkPWAInstallPromptAfterLogin();
      return true;
    } else {
      clearAuthToken();
      if (loginScreen) {
        loginScreen.style.display = "flex";
        document.body.classList.add("login-locked");
      }
      return false;
    }
  } catch (err) {
    console.warn("Auth check error:", err);
    if (loginScreen) {
      loginScreen.style.display = "flex";
      document.body.classList.add("login-locked");
    }
    return false;
  }
}

async function handleLoginSubmit(e) {
  if (e && typeof e.preventDefault === "function") e.preventDefault();
  const usernameInput = document.getElementById("login-username");
  const passwordInput = document.getElementById("login-password");
  const rememberInput = document.getElementById("login-remember");
  const errorBox = document.getElementById("login-error-box") || document.getElementById("login-error");
  const errorMsg = document.getElementById("login-error-msg") || errorBox;
  const submitBtn = document.getElementById("login-submit-btn");

  const username = usernameInput ? usernameInput.value.trim() : "";
  const password = passwordInput ? passwordInput.value : "";
  const remember = rememberInput ? rememberInput.checked : false;

  if (errorBox) errorBox.style.display = "none";

  if (!username || !password) {
    if (errorBox) {
      if (errorMsg) errorMsg.textContent = "Por favor, informe o usuário e a senha de acesso.";
      errorBox.style.display = "flex";
    }
    return;
  }

  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="login-spinner"></span> Entrando...';
  }

  try {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || "Credenciais inválidas. Verifique o usuário e a senha.");
    }

    setAuthToken(data.token, remember);
    const user = data.user || data;
    updateNavUserBadge(user);

    const loginScreen = document.getElementById("login-screen");
    if (loginScreen) {
      loginScreen.style.display = "none";
      document.body.classList.remove("login-locked");
    }

    showToast(`Bem-vindo, ${user.name || user.username}!`, "success");
    if (passwordInput) passwordInput.value = "";

    if (user.role === "professor") {
      switchTab("scanner-tab");
    } else {
      restoreActiveTab(user);
    }
    checkPWAInstallPromptAfterLogin();
  } catch (err) {
    if (errorBox) {
      if (errorMsg) errorMsg.textContent = err.message;
      errorBox.style.display = "flex";
    }
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `<span>Entrar no Sistema</span><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/></svg>`;
    }
  }
}

function togglePasswordVisibility() {
  const pwdInput = document.getElementById("login-password");
  if (!pwdInput) return;
  const isPwd = pwdInput.type === "password";
  pwdInput.type = isPwd ? "text" : "password";
}

async function handleLogout() {
  if (!confirm("Deseja realmente sair da sua sessão?")) return;
  try {
    await fetch("/api/auth/logout", {
      method: "POST",
      headers: { ...getAuthHeaders() }
    });
  } catch (e) {
    // Continue local cleanup even on network disconnect
  }
  clearAuthToken();
  try {
    localStorage.removeItem("omr_active_tab");
    localStorage.removeItem("omr_active_subpage");
  } catch (e) {}
  const loginScreen = document.getElementById("login-screen");
  if (loginScreen) {
    loginScreen.style.display = "flex";
    document.body.classList.add("login-locked");
  }
  stopCamera();
  showToast("Sessão finalizada com sucesso.", "info");
}

// =========================================================================
// MACRO DASHBOARD MODULE
// =========================================================================
let dashSchoolsChartInstance = null;
let dashYearsChartInstance = null;
let currentDashboardData = null;

function populateDashboardExamFilter(selectedId) {
  const select = document.getElementById("dash-exam-filter");
  if (!select) return;

  const currentVal = selectedId !== undefined ? selectedId : select.value;
  select.innerHTML = '<option value="">Todas as Avaliações</option>';

  if (Array.isArray(examsList)) {
    examsList.forEach(ex => {
      const opt = document.createElement("option");
      opt.value = ex.id;
      opt.textContent = `${ex.title} (${ex.num_questions} Qs)`;
      if (String(ex.id) === String(currentVal)) {
        opt.selected = true;
      }
      select.appendChild(opt);
    });
  }
}

async function loadDashboardData(examId = null) {
  const filterSelect = document.getElementById("dash-exam-filter");
  const selectedId = examId !== null ? examId : (filterSelect ? filterSelect.value : "");

  populateDashboardExamFilter(selectedId);

  try {
    let url = "/api/reports/dashboard";
    if (selectedId) {
      url += `?exam_id=${encodeURIComponent(selectedId)}`;
    }
    const res = await fetch(url, { headers: { ...getAuthHeaders() } });
    if (!res.ok) throw new Error("Falha ao obter os dados consolidados.");
    const data = await res.json();
    currentDashboardData = data;
    renderDashboardUI(data);
  } catch (err) {
    console.error("Dashboard error:", err);
    showToast("Erro ao atualizar Dashboard: " + err.message, "error");
  }
}

function onDashboardExamChange() {
  const select = document.getElementById("dash-exam-filter");
  const examId = select ? select.value : "";
  loadDashboardData(examId);
}

function refreshDashboard() {
  const select = document.getElementById("dash-exam-filter");
  const examId = select ? select.value : "";
  loadDashboardData(examId);
  showToast("Dados do Dashboard atualizados!", "info");
}

function renderDashboardUI(data) {
  if (!data) return;
  const kpis = data.kpis || {};
  const totalGraded = Number(kpis.total_graded || 0);

  // 1. KPI Card 1: Média Geral da Rede
  const elAvg = document.getElementById("dash-kpi-avg");
  const elAvgBadge = document.getElementById("dash-kpi-avg-badge");
  const elAvgBar = document.getElementById("dash-kpi-avg-bar");
  const avg = Number(kpis.overall_avg_percent || kpis.overall_avg_pct || 0);

  if (elAvg) {
    if (totalGraded === 0) {
      elAvg.textContent = "0.0%";
      elAvg.className = "dash-kpi-main-val";
    } else {
      elAvg.textContent = `${avg.toFixed(1)}%`;
      elAvg.className = "dash-kpi-main-val " + (avg >= 70 ? "text-success" : avg >= 50 ? "text-warning" : "text-danger");
    }
  }
  if (elAvgBadge) {
    if (totalGraded === 0) {
      elAvgBadge.textContent = "Sem dados";
      elAvgBadge.className = "dash-kpi-badge badge-neutral";
      elAvgBadge.style.display = "inline-flex";
    } else if (avg >= 70) {
      elAvgBadge.textContent = "Excelente";
      elAvgBadge.className = "dash-kpi-badge badge-success";
      elAvgBadge.style.display = "inline-flex";
    } else if (avg >= 50) {
      elAvgBadge.textContent = "Na Média";
      elAvgBadge.className = "dash-kpi-badge badge-warning";
      elAvgBadge.style.display = "inline-flex";
    } else {
      elAvgBadge.textContent = "Abaixo";
      elAvgBadge.className = "dash-kpi-badge badge-danger";
      elAvgBadge.style.display = "inline-flex";
    }
  }
  if (elAvgBar) {
    elAvgBar.style.width = `${Math.min(avg, 100)}%`;
    elAvgBar.className = "dash-kpi-bar-fill " + (avg >= 70 ? "bar-green" : avg >= 50 ? "bar-amber" : "bar-rose");
  }

  // KPI Card 2: Provas Corrigidas
  const elGraded = document.getElementById("dash-kpi-graded");
  const elExamsCount = document.getElementById("dash-kpi-exams-count");
  if (elGraded) elGraded.textContent = totalGraded.toLocaleString("pt-BR");
  if (elExamsCount) {
    const exCount = Number(kpis.total_exams || (Array.isArray(examsList) ? examsList.length : 0));
    elExamsCount.textContent = `${exCount} simulado${exCount !== 1 ? "s" : ""}`;
  }

  // KPI Card 3: Taxa de Participação
  const elPart = document.getElementById("dash-kpi-participation") || document.getElementById("dash-kpi-rate");
  const elStudents = document.getElementById("dash-kpi-students-total") || document.getElementById("dash-kpi-students");
  const elPartBar = document.getElementById("dash-kpi-part-bar");
  const rate = Number(kpis.participation_rate || 0);

  if (elPart) elPart.textContent = `${rate.toFixed(1)}%`;
  if (elStudents) {
    const stCount = Number(kpis.total_students || 0);
    elStudents.textContent = `${stCount} alunos`;
  }
  if (elPartBar) {
    elPartBar.style.width = `${Math.min(rate, 100)}%`;
  }

  // KPI Card 4: Rede Escolar Ativa
  const elSchools = document.getElementById("dash-kpi-schools");
  const elClassrooms = document.getElementById("dash-kpi-classrooms");
  if (elSchools) elSchools.textContent = Number(kpis.total_schools || 0).toLocaleString("pt-BR");
  if (elClassrooms) {
    const clsCount = Number(kpis.total_classrooms || 0);
    elClassrooms.textContent = `${clsCount} turmas`;
  }

  // 2. Charts
  renderSchoolsChart(data.schools_comparison || data.schools_table || []);
  renderYearsChart(data.grade_years_comparison || data.years_data || []);

  // 3. Table
  renderExecutiveTable(data.schools_comparison || data.schools_table || []);

  // 4. Alerts
  renderAlertsGrid(data.alert_classrooms || data.alerts || []);
}

function renderSchoolsChart(schools) {
  const canvas = document.getElementById("dash-schools-chart") || document.getElementById("dash-chart-schools");
  if (!canvas || typeof Chart === "undefined") return;

  if (dashSchoolsChartInstance) {
    dashSchoolsChartInstance.destroy();
    dashSchoolsChartInstance = null;
  }

  if (!schools || schools.length === 0) {
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    return;
  }

  const sorted = [...schools].sort((a, b) => (b.avg_score_percent || 0) - (a.avg_score_percent || 0));
  const labels = sorted.map(s => (s.name || s.school_name || "").length > 20 ? (s.name || s.school_name || "").substring(0, 18) + "..." : (s.name || s.school_name || "Escola"));
  const values = sorted.map(s => Number((s.avg_score_percent || s.average_pct || 0).toFixed(1)));
  const allZero = values.every(v => v === 0);

  const bgColors = values.map(v => {
    if (allZero) return "rgba(226, 232, 240, 0.85)";
    return v >= 70 ? "rgba(37, 99, 235, 0.85)" : v >= 50 ? "rgba(245, 158, 11, 0.85)" : "rgba(239, 68, 68, 0.85)";
  });
  const borderColors = values.map(v => {
    if (allZero) return "#cbd5e1";
    return v >= 70 ? "#2563eb" : v >= 50 ? "#f59e0b" : "#ef4444";
  });

  dashSchoolsChartInstance = new Chart(canvas, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: "Média de Acertos (%)",
        data: values,
        backgroundColor: bgColors,
        borderColor: borderColors,
        borderWidth: 1.5,
        borderRadius: 6,
        maxBarThickness: 42
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => allZero ? " Sem provas corrigidas ainda" : ` Média: ${ctx.parsed.y}%`
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          ticks: {
            callback: (v) => `${v}%`,
            font: { family: "'Plus Jakarta Sans', sans-serif" }
          },
          grid: { color: "rgba(226, 232, 240, 0.6)" }
        },
        x: {
          ticks: {
            font: { family: "'Plus Jakarta Sans', sans-serif", size: 11 }
          },
          grid: { display: false }
        }
      }
    }
  });
}

function renderYearsChart(gradeYears) {
  const canvas = document.getElementById("dash-years-chart") || document.getElementById("dash-chart-years");
  if (!canvas || typeof Chart === "undefined") return;

  if (dashYearsChartInstance) {
    dashYearsChartInstance.destroy();
    dashYearsChartInstance = null;
  }

  if (!gradeYears || gradeYears.length === 0) {
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    return;
  }

  const labels = gradeYears.map(g => g.grade_name || g.grade_year);
  const values = gradeYears.map(g => Number((g.avg_score_percent || g.average_pct || 0).toFixed(1)));
  const counts = gradeYears.map(g => g.graded_count || 0);
  const allZeroYears = counts.every(c => c === 0);

  dashYearsChartInstance = new Chart(canvas, {
    type: "line",
    data: {
      labels: labels,
      datasets: [{
        label: "Média de Acertos (%)",
        data: values,
        borderColor: allZeroYears ? "#94a3b8" : "#10b981",
        backgroundColor: allZeroYears ? "rgba(148, 163, 184, 0.08)" : "rgba(16, 185, 129, 0.15)",
        fill: true,
        tension: 0.35,
        borderWidth: allZeroYears ? 2 : 3,
        pointBackgroundColor: allZeroYears ? "#cbd5e1" : "#10b981",
        pointBorderColor: "#ffffff",
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const idx = ctx.dataIndex;
              if (counts[idx] === 0) {
                return " Aguardando correções para este ano";
              }
              return [
                ` Média: ${ctx.parsed.y}%`,
                ` Provas computadas: ${counts[idx]}`
              ];
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          ticks: {
            callback: (v) => `${v}%`,
            font: { family: "'Plus Jakarta Sans', sans-serif" }
          },
          grid: { color: "rgba(226, 232, 240, 0.6)" }
        },
        x: {
          ticks: {
            font: { family: "'Plus Jakarta Sans', sans-serif", size: 11 }
          },
          grid: { display: false }
        }
      }
    }
  });
}

function renderExecutiveTable(schools) {
  const tbody = document.getElementById("dash-schools-tbody");
  if (!tbody) return;

  if (!schools || schools.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4" style="color: #64748b; padding: 2rem;">Nenhuma unidade escolar cadastrada na rede.</td></tr>`;
    return;
  }

  tbody.innerHTML = schools.map((s, idx) => {
    const graded = Number(s.graded_count || 0);
    const avg = Number((s.avg_score_percent || s.average_pct || 0).toFixed(1));
    const rate = Number((s.participation_rate || 0).toFixed(1));
    const inep = s.inep_code && s.inep_code !== "-" ? s.inep_code : "—";

    let badgeCls = "badge-neutral";
    let badgeLabel = "Sem dados";
    let avgDisplay = `<span style="color: #94a3b8; font-weight: 500;">—</span>`;

    if (graded > 0) {
      if (avg >= 70) {
        badgeCls = "badge-success";
        badgeLabel = "Excelente";
        avgDisplay = `<span style="color: #059669; font-weight: 700;">${avg}%</span>`;
      } else if (avg >= 50) {
        badgeCls = "badge-warning";
        badgeLabel = "Regular";
        avgDisplay = `<span style="color: #d97706; font-weight: 700;">${avg}%</span>`;
      } else {
        badgeCls = "badge-danger";
        badgeLabel = "Abaixo";
        avgDisplay = `<span style="color: #dc2626; font-weight: 700;">${avg}%</span>`;
      }
    }

    return `
      <tr>
        <!-- 1. Escola Municipal -->
        <td style="font-weight: 700; color: #1e293b;">
          <div style="display: flex; align-items: center; gap: 0.5rem;">
            <span style="display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 50%; background: #f1f5f9; font-size: 0.72rem; color: #64748b; font-weight: 700;">${idx + 1}</span>
            <span>${escapeHtml(s.name || s.school_name)}</span>
          </div>
        </td>
        <!-- 2. Código INEP -->
        <td class="text-center" style="font-family: monospace; font-size: 0.85rem; color: #64748b;">
          ${escapeHtml(inep)}
        </td>
        <!-- 3. Turmas -->
        <td class="text-center" style="font-weight: 600;">${s.classrooms_count || 0}</td>
        <!-- 4. Alunos Cadastrados -->
        <td class="text-center" style="font-weight: 600;">${s.total_students || s.students_count || 0}</td>
        <!-- 5. Provas Corrigidas -->
        <td class="text-center" style="font-weight: 700; color: ${graded > 0 ? '#0f172a' : '#94a3b8'};">
          ${graded}
        </td>
        <!-- 6. Taxa de Participação -->
        <td class="text-center">
          <div style="display: flex; align-items: center; justify-content: center; gap: 0.4rem;">
            <span style="font-weight: 600; min-width: 38px;">${rate}%</span>
            <div style="width: 48px; height: 6px; background: #e2e8f0; border-radius: 3px; overflow: hidden;">
              <div style="width: ${Math.min(rate, 100)}%; height: 100%; background: ${graded > 0 ? '#2563eb' : '#cbd5e1'}; border-radius: 3px;"></div>
            </div>
          </div>
        </td>
        <!-- 7. Média de Acertos -->
        <td class="text-center" style="font-size: 0.95rem;">
          ${avgDisplay}
        </td>
        <!-- 8. Classificação -->
        <td class="text-center">
          <span class="status-badge ${badgeCls}">${badgeLabel}</span>
        </td>
      </tr>
    `;
  }).join("");
}

function renderAlertsGrid(alerts) {
  const container = document.getElementById("dash-alerts-container");
  if (!container) return;

  if (!alerts || alerts.length === 0) {
    container.innerHTML = `
      <div style="grid-column: 1 / -1; padding: 1.5rem; text-align: center; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: var(--radius-md); color: #166534;">
        <span style="font-weight: 700; display: inline-flex; align-items: center; gap: 0.4rem;">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
          Excelente! Nenhuma turma com rendimento crítico (&lt; 50%) detectada na rede.
        </span>
      </div>
    `;
    return;
  }

  container.innerHTML = alerts.map(a => {
    const avg = Number((a.avg_percent || 0).toFixed(1));
    return `
      <div class="dash-alert-card">
        <div class="dash-alert-header">
          <div>
            <div class="dash-alert-class">${escapeHtml(a.classroom_name)}</div>
            <div class="dash-alert-school">${escapeHtml(a.school_name)}</div>
          </div>
          <span class="dash-alert-badge">${avg}%</span>
        </div>
        <div class="dash-alert-stats">
          <span>${a.grade_year ? escapeHtml(a.grade_year) : "Ano não inf."}</span>
          <span>•</span>
          <span>${a.graded_count} prova(s) corrigida(s)</span>
        </div>
      </div>
    `;
  }).join("");
}

// ==========================================================================
// GESTÃO DE USUÁRIOS E ACESSOS
// ==========================================================================
let allUsersList = [];

async function loadUsers() {
  const tbody = document.getElementById("users-tbody");
  if (!tbody) return;

  tbody.innerHTML = `
    <tr>
      <td colspan="6" style="text-align: center; padding: 2.5rem 1rem; color: #64748b;">
        <div style="display: inline-flex; align-items: center; gap: 0.6rem; font-weight: 600;">
          <div class="btn-spinner" style="border-color: #94a3b8; border-top-color: #2563eb; width: 18px; height: 18px;"></div>
          <span>Carregando lista de operadores e usuários...</span>
        </div>
      </td>
    </tr>
  `;

  try {
    const res = await fetch("/api/users", {
      headers: { ...getAuthHeaders() }
    });

    if (res.status === 401) {
      clearAuthToken();
      checkAuthStatus();
      return;
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Erro ao consultar usuários.");
    }

    allUsersList = await res.json();
    updateUsersKpis(allUsersList);
    filterUsersList();
  } catch (err) {
    console.error("loadUsers error:", err);
    tbody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align: center; padding: 2rem 1rem; color: #dc2626; font-weight: 600;">
          ❌ Falha ao carregar usuários: ${escapeHtml(err.message)}
        </td>
      </tr>
    `;
    showToast("Erro ao carregar usuários: " + err.message, "danger");
  }
}

function updateUsersKpis(users) {
  const totalEl = document.getElementById("users-kpi-total");
  const activePill = document.getElementById("users-kpi-active-pill");
  const adminsEl = document.getElementById("users-kpi-admins");
  const coordsEl = document.getElementById("users-kpi-coords");
  const teachersEl = document.getElementById("users-kpi-teachers");

  const total = users.length;
  const activeCount = users.filter(u => u.is_active).length;
  const admins = users.filter(u => u.role === "admin").length;
  const coords = users.filter(u => u.role === "coordenador").length;
  const teachers = users.filter(u => u.role === "professor").length;

  if (totalEl) totalEl.textContent = total;
  if (activePill) activePill.textContent = `${activeCount} ativos`;
  if (adminsEl) adminsEl.textContent = admins;
  if (coordsEl) coordsEl.textContent = coords;
  if (teachersEl) teachersEl.textContent = teachers;
}

function filterUsersList() {
  const searchInput = document.getElementById("users-search-input");
  const roleSelect = document.getElementById("users-role-filter");
  const clearBtn = document.getElementById("users-search-clear");

  const term = searchInput ? searchInput.value.trim().toLowerCase() : "";
  const role = roleSelect ? roleSelect.value : "";

  if (clearBtn) {
    clearBtn.style.display = term ? "flex" : "none";
  }

  let filtered = allUsersList;

  if (role) {
    filtered = filtered.filter(u => u.role === role);
  }

  if (term) {
    filtered = filtered.filter(u => {
      const name = (u.name || "").toLowerCase();
      const username = (u.username || "").toLowerCase();
      const email = (u.email || "").toLowerCase();
      return name.includes(term) || username.includes(term) || email.includes(term);
    });
  }

  renderUsersTable(filtered, term);
}

function clearUsersSearch() {
  const searchInput = document.getElementById("users-search-input");
  if (searchInput) {
    searchInput.value = "";
    searchInput.focus();
  }
  filterUsersList();
}

function renderUsersTable(users, searchTerm = "") {
  const tbody = document.getElementById("users-tbody");
  if (!tbody) return;

  if (!users || users.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align: center; padding: 2.5rem 1rem; color: #64748b;">
          ${searchTerm ? `Nenhum usuário encontrado para a busca "<strong>${escapeHtml(searchTerm)}</strong>".` : "Nenhum usuário cadastrado."}
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = users.map(u => {
    let roleBadge = "";
    if (u.role === "admin") {
      roleBadge = `<span class="role-badge role-badge-admin">🛡️ Admin SEMED</span>`;
    } else if (u.role === "coordenador") {
      roleBadge = `<span class="role-badge role-badge-coord">📚 Coord. Pedagógico</span>`;
    } else {
      roleBadge = `<span class="role-badge role-badge-prof">✏️ Professor</span>`;
    }

    const statusBadge = u.is_active 
      ? `<span class="status-badge status-badge-active">Ativo</span>`
      : `<span class="status-badge status-badge-inactive">Inativo</span>`;

    const toggleTitle = u.is_active ? "Desativar acesso deste usuário" : "Ativar acesso deste usuário";
    const toggleIcon = u.is_active 
      ? `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"></line></svg>`
      : `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>`;

    return `
      <tr>
        <td>
          <div style="font-weight: 700; color: #0f172a; font-size: 0.83rem;">${escapeHtml(u.name || u.username)}</div>
          ${u.last_login ? `<div style="font-size: 0.68rem; color: #94a3b8; margin-top: 2px;">Último acesso: ${new Date(u.last_login).toLocaleString('pt-BR')}</div>` : `<div style="font-size: 0.68rem; color: #94a3b8; margin-top: 2px;">Nunca acessou</div>`}
        </td>
        <td style="text-align: center;">
          <code style="background: #f1f5f9; padding: 2px 7px; border-radius: 4px; font-weight: 600; color: #334155; font-size: 0.76rem;">${escapeHtml(u.username)}</code>
        </td>
        <td style="color: #475569; font-size: 0.79rem;">
          ${u.email ? escapeHtml(u.email) : `<span style="color: #94a3b8; font-style: italic;">Não informado</span>`}
        </td>
        <td style="text-align: center;">
          ${roleBadge}
        </td>
        <td style="text-align: center;">
          ${statusBadge}
        </td>
        <td style="text-align: center;">
          <div class="users-actions-cell">
            <button type="button" class="btn-icon-action action-edit" onclick="openUserModal('${u.id}')" title="Editar dados do usuário">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
              </svg>
            </button>
            <button type="button" class="btn-icon-action action-toggle" onclick="toggleUserStatus('${u.id}', ${!u.is_active})" title="${toggleTitle}">
              ${toggleIcon}
            </button>
            ${currentUserProfile && currentUserProfile.role === "admin" ? `
            <button type="button" class="btn-icon-action action-delete" onclick="deleteUser('${u.id}')" title="Excluir usuário">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"></polyline>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
              </svg>
            </button>` : ''}
          </div>
        </td>
      </tr>
    `;
  }).join("");
}

function openUserModal(userId = null) {
  if (currentUserProfile && currentUserProfile.role === "professor") {
    showToast("Acesso restrito. Professores têm acesso exclusivo à Correção de Provas.", "warning");
    return;
  }
  const modal = document.getElementById("user-modal");
  const modalTitle = document.getElementById("user-modal-title");
  const errorBox = document.getElementById("user-form-error");
  const pwdHelp = document.getElementById("user-pwd-help");
  const pwdLabel = document.getElementById("user-form-pwd-label");
  const pwdConfirmLabel = document.getElementById("user-form-pwd-confirm-label");
  const pwdInput = document.getElementById("user-form-pwd");
  const pwdConfirmInput = document.getElementById("user-form-pwd-confirm");

  if (!modal) return;

  if (errorBox) {
    errorBox.style.display = "none";
    errorBox.textContent = "";
  }

  if (userId) {
    const user = allUsersList.find(u => String(u.id) === String(userId));
    if (!user) {
      showToast("Usuário não encontrado.", "warning");
      return;
    }
    if (modalTitle) modalTitle.textContent = "Editar Usuário: " + (user.name || user.username);
    document.getElementById("user-form-id").value = user.id;
    document.getElementById("user-form-name").value = user.name || "";
    document.getElementById("user-form-username").value = user.username || "";
    document.getElementById("user-form-email").value = user.email || "";
    document.getElementById("user-form-role").value = user.role || "coordenador";
    document.getElementById("user-form-active").checked = !!user.is_active;

    if (pwdInput) {
      pwdInput.value = "";
      pwdInput.required = false;
    }
    if (pwdConfirmInput) {
      pwdConfirmInput.value = "";
      pwdConfirmInput.required = false;
    }
    if (pwdLabel) pwdLabel.textContent = "Nova Senha (Opcional):";
    if (pwdConfirmLabel) pwdConfirmLabel.textContent = "Confirmar Nova Senha:";
    if (pwdHelp) pwdHelp.style.display = "block";
  } else {
    if (modalTitle) modalTitle.textContent = "Novo Usuário";
    document.getElementById("user-form-id").value = "";
    document.getElementById("user-form-name").value = "";
    document.getElementById("user-form-username").value = "";
    document.getElementById("user-form-email").value = "";
    document.getElementById("user-form-role").value = "coordenador";
    document.getElementById("user-form-active").checked = true;

    if (pwdInput) {
      pwdInput.value = "";
      pwdInput.required = true;
    }
    if (pwdConfirmInput) {
      pwdConfirmInput.value = "";
      pwdConfirmInput.required = true;
    }
    if (pwdLabel) pwdLabel.textContent = "Senha de Acesso: *";
    if (pwdConfirmLabel) pwdConfirmLabel.textContent = "Confirmar Senha: *";
    if (pwdHelp) pwdHelp.style.display = "none";
  }

  modal.style.display = "flex";
  const nameInput = document.getElementById("user-form-name");
  if (nameInput) setTimeout(() => nameInput.focus(), 50);
}

function closeUserModal() {
  const modal = document.getElementById("user-modal");
  if (modal) modal.style.display = "none";
}

async function saveUser(e) {
  if (e && typeof e.preventDefault === "function") e.preventDefault();

  const id = document.getElementById("user-form-id").value;
  const name = document.getElementById("user-form-name").value.trim();
  const username = document.getElementById("user-form-username").value.trim();
  const email = document.getElementById("user-form-email").value.trim();
  const role = document.getElementById("user-form-role").value;
  const password = document.getElementById("user-form-pwd").value;
  const passwordConfirm = document.getElementById("user-form-pwd-confirm").value;
  const isActive = document.getElementById("user-form-active").checked;
  const errorBox = document.getElementById("user-form-error");
  const saveBtn = document.getElementById("btn-save-user");

  if (errorBox) {
    errorBox.style.display = "none";
    errorBox.textContent = "";
  }

  if (!name || !username) {
    if (errorBox) {
      errorBox.textContent = "Por favor, preencha o nome completo e o usuário de login.";
      errorBox.style.display = "block";
    }
    return;
  }

  // Validate passwords
  if (!id && !password) {
    if (errorBox) {
      errorBox.textContent = "A senha de acesso é obrigatória para novos usuários.";
      errorBox.style.display = "block";
    }
    return;
  }

  if (password || passwordConfirm) {
    if (password.length < 4) {
      if (errorBox) {
        errorBox.textContent = "A senha deve conter pelo menos 4 caracteres.";
        errorBox.style.display = "block";
      }
      return;
    }
    if (password !== passwordConfirm) {
      if (errorBox) {
        errorBox.textContent = "A confirmação da senha não coincide com a senha digitada.";
        errorBox.style.display = "block";
      }
      return;
    }
  }

  const payload = {
    name,
    username,
    email: email || null,
    role,
    is_active: isActive
  };
  if (password) {
    payload.password = password;
  }

  if (saveBtn) {
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="login-spinner"></span> Salvando...';
  }

  try {
    let url = "/api/users";
    let method = "POST";
    if (id) {
      url = `/api/users/${id}`;
      method = "PUT";
    }

    const res = await fetch(url, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders()
      },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Erro ao salvar usuário.");
    }

    closeUserModal();
    showToast(id ? "Usuário atualizado com sucesso!" : "Usuário cadastrado com sucesso!", "success");
    await loadUsers();
  } catch (err) {
    if (errorBox) {
      errorBox.textContent = err.message;
      errorBox.style.display = "block";
    }
  } finally {
    if (saveBtn) {
      saveBtn.disabled = false;
      saveBtn.innerHTML = '<span>Salvar Usuário</span>';
    }
  }
}

async function toggleUserStatus(userId, newStatus) {
  try {
    const res = await fetch(`/api/users/${userId}/status`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders()
      },
      body: JSON.stringify({ is_active: newStatus })
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Erro ao alterar status do usuário.");
    }

    showToast(newStatus ? "Usuário ativado!" : "Usuário desativado!", "info");
    await loadUsers();
  } catch (err) {
    showToast(err.message, "danger");
  }
}

async function deleteUser(userId) {
  if (currentUserProfile && currentUserProfile.role !== "admin") {
    showToast("Apenas o Administrador SEMED tem permissão para excluir usuários.", "warning");
    return;
  }
  const user = allUsersList.find(u => String(u.id) === String(userId));
  const username = user ? (user.name || user.username) : "este usuário";

  if (!confirm(`Tem certeza que deseja excluir o usuário "${username}"?\nEsta ação não poderá ser desfeita.`)) {
    return;
  }

  try {
    const res = await fetch(`/api/users/${userId}`, {
      method: "DELETE",
      headers: { ...getAuthHeaders() }
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Erro ao excluir usuário.");
    }

    showToast("Usuário excluído com sucesso!", "success");
    await loadUsers();
  } catch (err) {
    showToast(err.message, "danger");
  }
}

// Global Window Exports for inline HTML handlers
window.handleLoginSubmit = handleLoginSubmit;
window.togglePasswordVisibility = togglePasswordVisibility;
window.handleLogout = handleLogout;
window.onDashboardExamChange = onDashboardExamChange;
window.refreshDashboard = refreshDashboard;
window.openSettingsModal = openSettingsModal;
window.closeSettingsModal = closeSettingsModal;
window.saveSystemSettings = saveSystemSettings;
window.loadDashboardData = loadDashboardData;
window.checkAuthStatus = checkAuthStatus;

// User Management Exports
window.loadUsers = loadUsers;
window.openUserModal = openUserModal;
window.closeUserModal = closeUserModal;
window.saveUser = saveUser;
window.filterUsersList = filterUsersList;
window.clearUsersSearch = clearUsersSearch;
window.toggleUserStatus = toggleUserStatus;
window.deleteUser = deleteUser;

/* ==========================================================================
   BACKUP & RESTAURAÇÃO DO SISTEMA (EXCLUSIVO ADMINISTRADOR)
   ========================================================================== */
let selectedBackupFile = null;

async function loadBackupStats() {
  try {
    const res = await fetch("/api/backup/stats", {
      headers: { ...getAuthHeaders() }
    });
    if (!res.ok) {
      if (res.status === 403) return; // Não é admin
      throw new Error("Erro ao carregar estatísticas do banco.");
    }
    const stats = await res.json();

    const setVal = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = Number(val || 0).toLocaleString("pt-BR");
    };

    setVal("backup-stat-schools", stats.schools);
    setVal("backup-stat-classrooms", stats.classrooms);
    setVal("backup-stat-students", stats.students);
    setVal("backup-stat-exams", stats.exams);
    setVal("backup-stat-submissions", stats.submissions);
    setVal("backup-stat-users", stats.users);
  } catch (err) {
    console.error("[Backup] Erro ao carregar estatísticas:", err);
  }
}

async function handleExportBackup() {
  const btn = document.getElementById("btn-export-backup");
  const btnText = document.getElementById("btn-export-text");
  const spinner = document.getElementById("export-spinner");
  const statusMsg = document.getElementById("export-status-msg");

  try {
    if (btn) btn.disabled = true;
    if (spinner) spinner.style.display = "inline-block";
    if (btnText) btnText.textContent = "Gerando Backup (.ZIP)...";
    if (statusMsg) statusMsg.textContent = "Compactando tabelas e arquivos institucionais...";

    const res = await fetch("/api/backup/export", {
      headers: { ...getAuthHeaders() }
    });

    if (!res.ok) {
      const errJson = await res.json().catch(() => ({}));
      throw new Error(errJson.detail || "Falha ao gerar arquivo de backup.");
    }

    // Extrair nome do arquivo do header ou usar padrão com timestamp
    let filename = "backup_omr_canoa.zip";
    const disposition = res.headers.get("Content-Disposition");
    if (disposition && disposition.indexOf("filename=") !== -1) {
      const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
      if (matches != null && matches[1]) {
        filename = matches[1].replace(/['"]/g, '');
      }
    }

    const blob = await res.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = downloadUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(downloadUrl);
    document.body.removeChild(a);

    showToast("Backup baixado com sucesso!", "success");
    if (statusMsg) statusMsg.textContent = `Último backup baixado: ${filename}`;
  } catch (err) {
    showToast(err.message, "danger");
    if (statusMsg) statusMsg.textContent = "Erro na exportação. Tente novamente.";
  } finally {
    if (btn) btn.disabled = false;
    if (spinner) spinner.style.display = "none";
    if (btnText) btnText.textContent = "Gerar e Baixar Backup (.ZIP)";
  }
}

function handleBackupFileSelect(files) {
  if (!files || files.length === 0) return;
  const file = files[0];

  if (!file.name.toLowerCase().endsWith(".zip")) {
    showToast("Por favor, selecione um arquivo válido com extensão .ZIP", "warning");
    clearSelectedBackupFile();
    return;
  }

  selectedBackupFile = file;

  const nameEl = document.getElementById("backup-selected-filename");
  const sizeEl = document.getElementById("backup-selected-filesize");
  const box = document.getElementById("backup-file-selected-box");
  const triggerBtn = document.getElementById("btn-trigger-restore");
  const statusMsg = document.getElementById("restore-status-msg");

  if (nameEl) nameEl.textContent = file.name;
  if (sizeEl) {
    const sizeKb = (file.size / 1024).toFixed(1);
    sizeEl.textContent = `(${sizeKb} KB)`;
  }
  if (box) box.style.display = "flex";
  if (triggerBtn) triggerBtn.disabled = false;
  if (statusMsg) statusMsg.textContent = "Arquivo pronto. Clique no botão acima para iniciar a restauração.";
}

function clearSelectedBackupFile(event) {
  if (event) event.stopPropagation();
  selectedBackupFile = null;

  const fileInput = document.getElementById("backup-file-input");
  if (fileInput) fileInput.value = "";

  const box = document.getElementById("backup-file-selected-box");
  if (box) box.style.display = "none";

  const triggerBtn = document.getElementById("btn-trigger-restore");
  if (triggerBtn) triggerBtn.disabled = true;

  const statusMsg = document.getElementById("restore-status-msg");
  if (statusMsg) statusMsg.textContent = "Selecione um arquivo .ZIP para habilitar a restauração.";
}

function openBackupConfirmModal() {
  if (!selectedBackupFile) {
    showToast("Nenhum arquivo de backup selecionado.", "warning");
    return;
  }

  const modal = document.getElementById("backup-confirm-modal");
  const modalFilename = document.getElementById("backup-modal-file-name");
  const checkbox = document.getElementById("backup-confirm-checkbox");
  const executeBtn = document.getElementById("btn-execute-restore");
  const progressBox = document.getElementById("backup-restore-progress");

  if (modalFilename) modalFilename.textContent = selectedBackupFile.name;
  if (checkbox) checkbox.checked = false;
  if (executeBtn) executeBtn.disabled = true;
  if (progressBox) progressBox.style.display = "none";

  if (modal) modal.style.display = "flex";
}

function closeBackupConfirmModal() {
  const modal = document.getElementById("backup-confirm-modal");
  if (modal) modal.style.display = "none";
}

function toggleRestoreExecuteBtn() {
  const checkbox = document.getElementById("backup-confirm-checkbox");
  const executeBtn = document.getElementById("btn-execute-restore");
  if (checkbox && executeBtn) {
    executeBtn.disabled = !checkbox.checked;
  }
}

async function executeBackupRestore() {
  if (!selectedBackupFile) return;

  const progressBox = document.getElementById("backup-restore-progress");
  const executeBtn = document.getElementById("btn-execute-restore");
  const cancelBtn = document.getElementById("btn-cancel-restore");

  if (progressBox) progressBox.style.display = "block";
  if (executeBtn) executeBtn.disabled = true;
  if (cancelBtn) cancelBtn.disabled = true;

  try {
    const formData = new FormData();
    formData.append("file", selectedBackupFile);

    const res = await fetch("/api/backup/import", {
      method: "POST",
      headers: {
        "X-Auth-Token": getAuthToken()
      },
      body: formData
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Erro ao restaurar arquivo de backup.");
    }

    closeBackupConfirmModal();
    clearSelectedBackupFile();

    showToast(data.message || "Backup restaurado com sucesso!", "success");

    // Recarregar contadores do backup e views principais
    await loadBackupStats();
    if (typeof loadSchools === "function") loadSchools();
    if (typeof loadExams === "function") loadExams(false);
    if (typeof loadDashboardData === "function") loadDashboardData();
  } catch (err) {
    showToast(err.message, "danger");
  } finally {
    if (progressBox) progressBox.style.display = "none";
    if (cancelBtn) cancelBtn.disabled = false;
    toggleRestoreExecuteBtn();
  }
}

// Inicializar Drag and Drop na zona de backup
document.addEventListener("DOMContentLoaded", () => {
  const dropzone = document.getElementById("backup-dropzone");
  if (dropzone) {
    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add("drag-over");
      }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove("drag-over");
      }, false);
    });

    dropzone.addEventListener("drop", (e) => {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (files && files.length > 0) {
        handleBackupFileSelect(files);
      }
    }, false);
  }
});

// Backup Window Exports
window.loadBackupStats = loadBackupStats;
window.handleExportBackup = handleExportBackup;
window.handleBackupFileSelect = handleBackupFileSelect;
window.clearSelectedBackupFile = clearSelectedBackupFile;
window.openBackupConfirmModal = openBackupConfirmModal;
window.closeBackupConfirmModal = closeBackupConfirmModal;
window.toggleRestoreExecuteBtn = toggleRestoreExecuteBtn;
window.executeBackupRestore = executeBackupRestore;

/* ==========================================================================
   MENU SUSPENSO: GESTÃO ADMINISTRATIVA
   ========================================================================== */
function toggleAdminDropdown(event) {
  if (event) {
    event.stopPropagation();
  }
  const menu = document.getElementById("admin-dropdown-menu");
  const wrap = document.getElementById("wrap-admin-dropdown");
  if (!menu) return;

  const isHidden = menu.style.display === "none" || !menu.classList.contains("show");
  if (isHidden) {
    menu.style.display = "flex";
    menu.classList.add("show");
    if (wrap) wrap.classList.add("open");
  } else {
    closeAdminDropdown();
  }
}

function closeAdminDropdown() {
  const menu = document.getElementById("admin-dropdown-menu");
  const wrap = document.getElementById("wrap-admin-dropdown");
  if (menu) {
    menu.style.display = "none";
    menu.classList.remove("show");
  }
  if (wrap) wrap.classList.remove("open");
}

// Fechar menu suspenso de gestão ao clicar fora
document.addEventListener("click", (e) => {
  const wrap = document.getElementById("wrap-admin-dropdown");
  if (wrap && !wrap.contains(e.target)) {
    closeAdminDropdown();
  }
  if (!e.target.closest(".cl-more-wrapper")) {
    closeAllClassroomMenus();
  }
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    closeAllClassroomMenus();
    closeAdminDropdown();
  }
});

function toggleClassroomMoreMenu(event, classId) {
  if (event) {
    event.stopPropagation();
  }
  const menu = document.getElementById(`cl-more-menu-${classId}`);
  if (!menu) return;
  const isShown = menu.style.display !== "none";
  closeAllClassroomMenus();
  if (!isShown) {
    menu.style.display = "flex";
  }
}

function closeAllClassroomMenus() {
  document.querySelectorAll(".cl-dropdown-menu").forEach(m => {
    m.style.display = "none";
  });
}

window.toggleAdminDropdown = toggleAdminDropdown;
window.closeAdminDropdown = closeAdminDropdown;
window.toggleClassroomMoreMenu = toggleClassroomMoreMenu;
window.closeAllClassroomMenus = closeAllClassroomMenus;

/* ========================================================================= */
/* 📱 CONTROLE DO MENU RESPONSIVO MOBILE (DRAWER & BACKDROP)                 */
/* ========================================================================= */
function toggleMobileMenu() {
  const drawer = document.getElementById("mobile-nav-drawer");
  const isOpen = drawer && drawer.classList.contains("open");
  if (isOpen) {
    closeMobileMenu();
  } else {
    openMobileMenu();
  }
}

function openMobileMenu() {
  const drawer = document.getElementById("mobile-nav-drawer");
  const backdrop = document.getElementById("mobile-nav-backdrop");
  const toggleBtn = document.getElementById("btn-mobile-menu-toggle");
  if (drawer) drawer.classList.add("open");
  if (backdrop) backdrop.classList.add("open");
  if (toggleBtn) toggleBtn.classList.add("active");
  document.body.classList.add("mobile-menu-open");
}

function closeMobileMenu() {
  const drawer = document.getElementById("mobile-nav-drawer");
  const backdrop = document.getElementById("mobile-nav-backdrop");
  const toggleBtn = document.getElementById("btn-mobile-menu-toggle");
  if (drawer) drawer.classList.remove("open");
  if (backdrop) backdrop.classList.remove("open");
  if (toggleBtn) toggleBtn.classList.remove("active");
  document.body.classList.remove("mobile-menu-open");
}

// Fechar com tecla Escape
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    closeMobileMenu();
    closeAdminDropdown();
    dismissPWAInstallModal();
  }
});

window.toggleMobileMenu = toggleMobileMenu;
window.openMobileMenu = openMobileMenu;
window.closeMobileMenu = closeMobileMenu;

// ==========================================
// PWA (PROGRESSIVE WEB APP) - PROVA CANOA
// ==========================================

let deferredPWAInstallPrompt = null;

// Captura o evento nativo de instalação do PWA (Android / Chrome / Edge)
window.addEventListener("beforeinstallprompt", (e) => {
  e.preventDefault();
  deferredPWAInstallPrompt = e;
  console.log("[PWA] Evento beforeinstallprompt capturado com sucesso.");
});

// Evento disparado quando o app é instalado com sucesso
window.addEventListener("appinstalled", () => {
  deferredPWAInstallPrompt = null;
  localStorage.setItem("pwa_installed", "true");
  dismissPWAInstallModal();
  if (typeof showToast === "function") {
    showToast("Aplicativo Prova Canoa instalado com sucesso!", "success");
  }
  console.log("[PWA] Prova Canoa instalado na tela inicial com sucesso.");
});

// Registro do Service Worker
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/sw.js")
      .then((reg) => {
        console.log("[PWA] Service Worker registrado em:", reg.scope);
      })
      .catch((err) => {
        console.warn("[PWA] Falha ao registrar Service Worker:", err);
      });
  });
}

// Verifica se o app já está instalado como PWA
function isPWAInstalled() {
  // 1. Já salvo no localStorage após instalação ou confirmação
  if (localStorage.getItem("pwa_installed") === "true") {
    return true;
  }
  // 2. Modo standalone nativo (Android/Chrome/Desktop)
  if (window.matchMedia("(display-mode: standalone)").matches) {
    localStorage.setItem("pwa_installed", "true");
    return true;
  }
  // 3. Modo standalone nativo no iOS Safari
  if (window.navigator.standalone === true) {
    localStorage.setItem("pwa_installed", "true");
    return true;
  }
  // 4. Acesso iniciado a partir de TWA ou atalho nativo
  if (document.referrer && document.referrer.includes("android-app://")) {
    localStorage.setItem("pwa_installed", "true");
    return true;
  }
  return false;
}

// Verifica se o dispositivo atual é celular (mobile)
function isMobileDevice() {
  const ua = navigator.userAgent || navigator.vendor || window.opera || "";
  const isMobileUA = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(ua);
  const isSmallTouch = window.innerWidth <= 768 && ("ontouchstart" in window || navigator.maxTouchPoints > 0);
  return isMobileUA || isSmallTouch;
}

// Verifica se é iOS (iPhone/iPad) para exibir instruções do Safari
function isIOSDevice() {
  const ua = navigator.userAgent || "";
  return /iPad|iPhone|iPod/.test(ua) && !window.MSStream;
}

// Verifica e aciona o alerta de instalação após o login, SOMENTE em celulares
function checkPWAInstallPromptAfterLogin() {
  try {
    // 1. Apenas se for celular
    if (!isMobileDevice()) {
      return;
    }

    // 2. Apenas se NÃO foi instalado ainda
    if (isPWAInstalled()) {
      return;
    }

    // 3. Se o usuário já dispensou nesta sessão recente (últimas 24h), evita ser invasivo
    const dismissedUntil = localStorage.getItem("pwa_prompt_dismissed_until");
    if (dismissedUntil && Date.now() < parseInt(dismissedUntil, 10)) {
      return;
    }

    // Aguarda a interface assentar após o login
    setTimeout(() => {
      showPWAInstallModal();
    }, 1200);
  } catch (err) {
    console.warn("[PWA] Erro ao verificar prompt de instalação:", err);
  }
}

// Exibe o modal de instalação
function showPWAInstallModal() {
  const modal = document.getElementById("pwa-install-modal");
  if (!modal) return;

  const androidArea = document.getElementById("pwa-android-install-area");
  const iosArea = document.getElementById("pwa-ios-install-area");

  if (isIOSDevice()) {
    // No iOS o Safari não permite prompt programático, exibe guia passo-a-passo
    if (androidArea) androidArea.style.display = "none";
    if (iosArea) iosArea.style.display = "block";
  } else {
    // No Android / Chrome / outros navegadores
    if (androidArea) androidArea.style.display = "block";
    if (iosArea) iosArea.style.display = "none";
  }

  modal.style.display = "flex";
  // Pequeno delay para acionar a transição de slide-up da sheet
  requestAnimationFrame(() => {
    modal.classList.add("active");
  });
}

// Fecha o modal de instalação
function dismissPWAInstallModal() {
  const modal = document.getElementById("pwa-install-modal");
  if (!modal) return;

  modal.classList.remove("active");
  setTimeout(() => {
    modal.style.display = "none";
  }, 250);

  // Lembra que foi dispensado por 24 horas para não incomodar no mesmo dia se recusado
  localStorage.setItem("pwa_prompt_dismissed_until", (Date.now() + 24 * 60 * 60 * 1000).toString());
}

// Aciona a instalação do PWA
async function triggerPWAInstallation() {
  if (deferredPWAInstallPrompt) {
    try {
      deferredPWAInstallPrompt.prompt();
      const choiceResult = await deferredPWAInstallPrompt.userChoice;
      if (choiceResult.outcome === "accepted") {
        localStorage.setItem("pwa_installed", "true");
        dismissPWAInstallModal();
        if (typeof showToast === "function") {
          showToast("Instalação do Prova Canoa iniciada!", "success");
        }
      }
      deferredPWAInstallPrompt = null;
    } catch (err) {
      console.warn("[PWA] Erro ao acionar prompt nativo:", err);
    }
  } else {
    // Se o evento nativo ainda não disparou ou o navegador não suporta prompt()
    if (typeof showToast === "function") {
      showToast("Toque no menu (⋮) do seu navegador e selecione 'Adicionar à tela inicial' ou 'Instalar aplicativo'.", "info", 5000);
    }
  }
}

// Exportações globais para os handlers inline
window.isPWAInstalled = isPWAInstalled;
window.isMobileDevice = isMobileDevice;
window.checkPWAInstallPromptAfterLogin = checkPWAInstallPromptAfterLogin;
window.showPWAInstallModal = showPWAInstallModal;
window.dismissPWAInstallModal = dismissPWAInstallModal;
window.triggerPWAInstallation = triggerPWAInstallation;




