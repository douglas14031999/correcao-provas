/**
 * Montador Ativo de Instrumento Avaliativo • SEMED Lagoa da Canoa
 * Design System: Educação Analítica (stitch_gerador_de_provas_e_exames)
 */

(function () {
  // Estado Global da Aplicação
  let currentExamId = null;
  let activeQuestionIndex = 0;
  let activeTextarea = null;
  let selectedColumns = 2;
  let isSaving = false;

  function createBlankQuestion(number = 1, altsCount = 4) {
    const targetAlts = altsCount === 5 ? 5 : 4;
    const alts = [];
    for (let i = 0; i < targetAlts; i++) {
      alts.push({
        letter: String.fromCharCode(65 + i),
        text: "",
        is_correct: i === 0,
        image_url: ""
      });
    }
    return {
      id: `q_${Date.now()}_${number}`,
      question_number: number,
      statement: "",
      points: 1.0,
      difficulty: "medio",
      skill: "",
      bncc_code: "",
      type: String(targetAlts),
      image_url: "",
      alternatives: alts
    };
  }

  // Questões Iniciais: Inicia limpa com Questão 01 em branco para o professor
  let questions = [
    createBlankQuestion(1, 4)
  ];

  // Presets de Margem em Centímetros (cm) com Padrão Oficial ABNT
  const MARGIN_PRESETS = {
    narrow: { top: 1.5, bottom: 1.5, left: 1.5, right: 1.5, label: "Econômica (1,5 cm)" },
    standard: { top: 3.0, bottom: 2.0, left: 3.0, right: 2.0, label: "Padrão ABNT (3x2 cm)" },
    wide: { top: 3.5, bottom: 2.5, left: 3.5, right: 2.5, label: "Ampla (3,5 cm)" }
  };

  // Elementos do DOM
  let examTitleInput, saveStatusText, statusDot, statusPill;
  let bannerGabaritoOutdated, btnBannerUpdateGabarito, badgeGabaritoOutdatedDot;
  let currentExamHasLinkedGabarito = false;
  let isGabaritoOutdated = false;
  let chipQuestionCount, chipTotalScore, chipDisciplineDisplay, chipMarginsDisplay;
  let questionsSidebarList, sidebarQuestionBadge, sidebarTotalScore;
  let editorQNumBadge, editorQTitle, editorQStatement, editorQStatementRich;
  let cfgExamAlternativesMode, btnModalAlt4, btnModalAlt5;
  let globalExamAlternativesMode = 4;
  let editorImagePreviewContainer, editorImagePreview, editorMathPreviewContainer, editorMathPreviewContent;
  let editorRealtimeCard, editorRealtimePreview;
  let modalMathEditor, visualMathField, modalMathLivePreview, modalSymbolsBar;
  let btnCloseMathModal, btnCancelMathModal, btnConfirmInsertMath, btnMathClearField, btnOpenMathVisualModal;
  let currentMathTarget = null;
  let editorAlternativesList, editorQPoints, editorQDifficulty, editorQSkill;
  let prevQuestionLabel, nextQuestionLabel, footerScoreRatio, footerConfiguredStatus;
  let modalMargins, modalPreview, modalGabarito, modalMyExams, modalEmitirProva;
  let cfgMarginTop, cfgMarginBottom, cfgMarginLeft, cfgMarginRight;
  let cfgInstitution, cfgSchool, cfgDiscipline, cfgTeacher, cfgGrade, cfgClassroom, cfgShift, cfgDate, cfgMaxScore;
  let btnCol1, btnCol2, chkAnswerSheet, chkIncludeHeader, boxInstitutionalFields, previewFrame;
  let modalBnccPicker, btnOpenBnccModal, btnCloseBnccModal, btnCancelBnccModal;
  let bnccFilterDiscipline, bnccFilterGrade, bnccSearchInput, bnccCardsList, bnccResultsCount, bnccAutocompleteList;

  // Variáveis do Sistema de Imagens
  let modalImageConfig, modalImgTitle, btnCloseImgModal, btnCancelImgModal, btnConfirmImgModal, btnConfirmImgModalText;
  let modalImgFileInput, modalImgUrlInput, modalImgPreviewBox, modalImgPreviewTag, modalImgDimensionsInfo, modalImgSizeLabel, modalImgWidthSlider, btnModalImgRemove;
  let btnOpenImgStatementHeader, btnInsertImageStatement;
  let currentImageTarget = null;
  let currentSelectedImgAlign = "center";
  let currentSelectedImgWidth = "220px";
  let currentSelectedImgUrl = "";

  const KATEX_MACROS = {};

  // =========================================================================
  // Autenticação & Compatibilidade de Dispositivos (PC Exclusivo)
  // =========================================================================
  const AUTH_TOKEN_KEY = "semed_auth_token";

  function getAuthToken() {
    return localStorage.getItem(AUTH_TOKEN_KEY) || sessionStorage.getItem(AUTH_TOKEN_KEY) || "";
  }

  function getAuthHeaders() {
    const token = getAuthToken();
    return token ? {
      "Authorization": `Bearer ${token}`,
      "X-Auth-Token": token
    } : {};
  }

  function clearAuthToken() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    sessionStorage.removeItem(AUTH_TOKEN_KEY);
  }

  function checkDeviceCompatibility() {
    const isMobile = window.innerWidth < 1024 || /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    const blocker = document.getElementById("mobile-device-blocker");
    if (isMobile) {
      if (blocker) {
        blocker.style.display = "flex";
        document.body.style.overflow = "hidden";
      }
      return false;
    } else {
      if (blocker) {
        blocker.style.display = "none";
        document.body.style.overflow = "";
      }
      return true;
    }
  }

  async function apiFetch(url, options = {}) {
    const headers = {
      ...getAuthHeaders(),
      ...(options.headers || {})
    };
    const res = await fetch(url, { ...options, headers });
    if (res.status === 401) {
      clearAuthToken();
      window.location.replace("/?redirect=" + encodeURIComponent(window.location.pathname + window.location.search));
      throw new Error("Sessão expirada. Redirecionando para login...");
    }
    return res;
  }

  let currentUser = null;

  async function checkAuth() {
    const token = getAuthToken();
    if (!token) {
      window.location.replace("/?redirect=" + encodeURIComponent(window.location.pathname + window.location.search));
      return false;
    }

    try {
      const res = await fetch("/api/auth/me", {
        headers: getAuthHeaders()
      });
      if (!res.ok) {
        clearAuthToken();
        window.location.replace("/?redirect=" + encodeURIComponent(window.location.pathname + window.location.search));
        return false;
      }
      const data = await res.json();
      currentUser = data.user || data;

      if (currentUser.role === "professor") {
        alert("Acesso restrito. Professores têm acesso exclusivo à Correção de Provas.");
        window.location.replace("/");
        return false;
      }

      updateUserUI(currentUser);
      return true;
    } catch (err) {
      console.warn("Erro ao validar sessão:", err);
      clearAuthToken();
      window.location.replace("/?redirect=" + encodeURIComponent(window.location.pathname + window.location.search));
      return false;
    }
  }

  function updateUserUI(user) {
    if (!user) return;
    const nameEl = document.getElementById("user-display-name");
    const roleEl = document.getElementById("user-display-role");
    const avatarEl = document.getElementById("user-avatar-badge");

    const displayName = user.name || user.username || "Usuário";
    if (nameEl) nameEl.textContent = displayName;

    const role = user.role || "admin";
    let roleText = "Operador SEMED";
    if (role === "admin") roleText = "SEMED (Admin)";
    else if (role === "coordenador") roleText = "Coordenação";
    else if (role === "professor") roleText = "Professor";
    if (roleEl) roleEl.textContent = user.role_display || roleText;

    const parts = displayName.trim().split(/\s+/);
    let initials = "AD";
    if (parts.length >= 2 && parts[0] && parts[parts.length - 1]) {
      initials = (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    } else if (parts.length === 1 && parts[0].length > 0) {
      initials = parts[0].substring(0, Math.min(2, parts[0].length)).toUpperCase();
    }
    if (avatarEl) avatarEl.textContent = initials;

    const logoutBtn = document.getElementById("btn-logout");
    if (logoutBtn) {
      logoutBtn.onclick = async () => {
        try {
          await apiFetch("/api/auth/logout", {
            method: "POST",
            headers: getAuthHeaders()
          });
        } catch (e) { }
        clearAuthToken();
        window.location.replace("/");
      };
    }
  }

  // =========================================================================
  // Escolas e Turmas da Rede Cadastradas (Integração SEMED)
  // =========================================================================
  let systemSchools = [];

  async function loadSystemSchools() {
    try {
      const res = await apiFetch("/api/schools");
      if (res.ok) {
        systemSchools = await res.json();
        populateSchoolsDatalist();
      }
    } catch (e) {
      console.warn("Aviso ao carregar escolas cadastradas:", e);
    }
  }

  function populateSchoolsDatalist() {
    const dlSchools = document.getElementById("cfg-datalist-schools");
    if (!dlSchools) return;
    dlSchools.innerHTML = "";
    systemSchools.forEach(sch => {
      if (sch && sch.name) {
        const opt = document.createElement("option");
        opt.value = sch.name;
        dlSchools.appendChild(opt);
      }
    });
  }

  function updateClassroomsDatalist(schoolName) {
    const dlClassrooms = document.getElementById("cfg-datalist-classrooms");
    const hint = document.getElementById("cfg-classroom-hint");
    if (!dlClassrooms) return;
    dlClassrooms.innerHTML = "";

    if (!schoolName || !schoolName.trim()) {
      if (hint) hint.textContent = "rede ou livre";
      return;
    }

    const cleanName = schoolName.trim().toLowerCase();
    const matched = systemSchools.find(s => (s.name || "").trim().toLowerCase() === cleanName);

    if (matched && Array.isArray(matched.classrooms) && matched.classrooms.length > 0) {
      if (hint) hint.textContent = `${matched.classrooms.length} turmas na rede`;
      matched.classrooms.forEach(c => {
        const opt = document.createElement("option");
        opt.value = c.name;
        dlClassrooms.appendChild(opt);
      });
    } else {
      if (hint) hint.textContent = "digitação livre";
    }
  }

  function autoDetectGradeFromClassroom(classroomName) {
    if (!classroomName || !cfgGrade) return;
    const upper = classroomName.toUpperCase();
    const m = upper.match(/(\d)[º°ªa-zA-Z\s]*([A-Z])/);
    if (m && m[1]) {
      cfgGrade.value = `${m[1]}º ANO`;
    }
  }

  function setSelectValueCaseInsensitive(selectEl, value) {
    if (!selectEl || !value) return;
    const target = value.trim().toLowerCase();
    for (let opt of selectEl.options) {
      if (opt.value.trim().toLowerCase() === target || opt.text.trim().toLowerCase() === target) {
        selectEl.value = opt.value;
        return;
      }
    }
    const newOpt = document.createElement("option");
    newOpt.value = value.trim().toUpperCase();
    newOpt.textContent = value.trim();
    selectEl.appendChild(newOpt);
    selectEl.value = newOpt.value;
  }

  // Inicialização
  document.addEventListener("DOMContentLoaded", async () => {
    checkDeviceCompatibility();
    window.addEventListener("resize", checkDeviceCompatibility);

    const isAuthed = await checkAuth();
    if (!isAuthed) return;
    cacheDomElements();
    loadSystemSchools();
    updateNetworkStatus();
    initDefaultDate();
    tryRestoreAutoSaveDraft();
    setupEventListeners();
    setupMarginsSystem();
    setupWordRibbon();
    setupVisualMathModal();
    setupImageSystem();
    setupBnccSystem();
    setupBankImportSystem();
    renderSidebarList();
    loadActiveQuestionToEditor();
    updateSummaryBars();
    checkUrlForExamLoad();

    ensureKaTeXLoaded(() => {
      loadActiveQuestionToEditor();
      updateRealtimeQuestionPreview();
    });
  });

  function checkUrlForExamLoad() {
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const targetId = urlParams.get("exam_id") || urlParams.get("id");
      if (targetId) {
        loadExamById(targetId);
      }
    } catch (e) {
      console.warn("Erro ao verificar parâmetro de exame na URL:", e);
    }
  }

  function ensureKaTeXLoaded(callback) {
    if (window.katex && window.renderMathInElement) {
      callback();
      return;
    }
    let checks = 0;
    const interval = setInterval(() => {
      checks++;
      if (window.katex && window.renderMathInElement) {
        clearInterval(interval);
        callback();
      } else if (checks > 40) {
        clearInterval(interval);
      }
    }, 100);
  }

  function cacheDomElements() {
    examTitleInput = document.getElementById("examTitleInput");
    saveStatusText = document.getElementById("save-status-text");
    statusDot = document.getElementById("status-dot");
    statusPill = document.getElementById("status-pill");

    bannerGabaritoOutdated = document.getElementById("banner-gabarito-outdated");
    btnBannerUpdateGabarito = document.getElementById("btn-banner-update-gabarito");
    badgeGabaritoOutdatedDot = document.getElementById("badge-gabarito-outdated-dot");

    chipQuestionCount = document.getElementById("chip-question-count");
    chipTotalScore = document.getElementById("chip-total-score");
    chipDisciplineDisplay = document.getElementById("chip-discipline-display");
    chipMarginsDisplay = document.getElementById("chip-margins-display");

    questionsSidebarList = document.getElementById("questions-sidebar-list");
    sidebarQuestionBadge = document.getElementById("sidebar-question-badge");
    sidebarTotalScore = document.getElementById("sidebar-total-score");

    editorQNumBadge = document.getElementById("editor-q-num-badge");
    editorQTitle = document.getElementById("editor-q-title");
    cfgExamAlternativesMode = document.getElementById("cfg-exam-alternatives-mode");
    btnModalAlt4 = document.getElementById("btn-modal-alt-4");
    btnModalAlt5 = document.getElementById("btn-modal-alt-5");
    editorQStatement = document.getElementById("editor-q-statement");
    editorQStatementRich = document.getElementById("editor-q-statement-rich");

    // Elementos do Modal e Controles de Imagem
    modalImageConfig = document.getElementById("modal-image-config");
    modalImgTitle = document.getElementById("modal-img-title");
    btnCloseImgModal = document.getElementById("btn-close-img-modal");
    btnCancelImgModal = document.getElementById("btn-cancel-img-modal");
    btnConfirmImgModal = document.getElementById("btn-confirm-img-modal");
    btnConfirmImgModalText = document.getElementById("btn-confirm-img-modal-text");
    modalImgFileInput = document.getElementById("modal-img-file-input");
    modalImgUrlInput = document.getElementById("modal-img-url-input");
    modalImgPreviewBox = document.getElementById("modal-img-preview-box");
    modalImgPreviewTag = document.getElementById("modal-img-preview-tag");
    modalImgDimensionsInfo = document.getElementById("modal-img-dimensions-info");
    modalImgSizeLabel = document.getElementById("modal-img-size-label");
    modalImgWidthSlider = document.getElementById("modal-img-width-slider");
    btnModalImgRemove = document.getElementById("btn-modal-img-remove");
    btnOpenImgStatementHeader = document.getElementById("btn-open-img-statement-header");
    btnInsertImageStatement = document.getElementById("btn-insert-image-statement");

    editorRealtimeCard = document.getElementById("editor-realtime-card");
    editorRealtimePreview = document.getElementById("editor-realtime-preview");

    modalMathEditor = document.getElementById("modal-math-editor");
    visualMathField = document.getElementById("visual-math-field");
    modalMathLivePreview = document.getElementById("modal-math-live-preview");
    modalSymbolsBar = document.getElementById("modal-symbols-bar");
    btnCloseMathModal = document.getElementById("btn-close-math-modal");
    btnCancelMathModal = document.getElementById("btn-cancel-math-modal");
    btnConfirmInsertMath = document.getElementById("btn-confirm-insert-math");
    btnMathClearField = document.getElementById("btn-math-clear-field");
    btnOpenMathVisualModal = document.getElementById("btn-open-math-visual-modal");

    editorAlternativesList = document.getElementById("editor-alternatives-list");
    editorQPoints = document.getElementById("editor-q-points");
    editorQDifficulty = document.getElementById("editor-q-difficulty");
    editorQSkill = document.getElementById("editor-q-skill");

    prevQuestionLabel = document.getElementById("prev-question-label");
    nextQuestionLabel = document.getElementById("next-question-label");
    footerScoreRatio = document.getElementById("footer-score-ratio");
    footerConfiguredStatus = document.getElementById("footer-configured-status");

    modalMargins = document.getElementById("modal-margins");
    modalPreview = document.getElementById("modal-preview");
    modalGabarito = document.getElementById("modal-gabarito");
    modalMyExams = document.getElementById("modal-my-exams");
    modalEmitirProva = document.getElementById("modal-emitir-prova");

    cfgMarginTop = document.getElementById("cfg-margin-top");
    cfgMarginBottom = document.getElementById("cfg-margin-bottom");
    cfgMarginLeft = document.getElementById("cfg-margin-left");
    cfgMarginRight = document.getElementById("cfg-margin-right");

    cfgInstitution = document.getElementById("cfg-institution");
    cfgSchool = document.getElementById("cfg-school");
    cfgDiscipline = document.getElementById("cfg-discipline");
    cfgTeacher = document.getElementById("cfg-teacher");
    cfgGrade = document.getElementById("cfg-grade");
    cfgClassroom = document.getElementById("cfg-classroom");
    cfgShift = document.getElementById("cfg-shift");
    cfgDate = document.getElementById("cfg-date");
    cfgMaxScore = document.getElementById("cfg-max-score");

    btnCol1 = document.getElementById("btn-col-1");
    btnCol2 = document.getElementById("btn-col-2");
    chkAnswerSheet = document.getElementById("chk-answer-sheet");
    chkIncludeHeader = document.getElementById("chk-include-header");
    boxInstitutionalFields = document.getElementById("box-institutional-fields");
    previewFrame = document.getElementById("preview-frame");

    if (chkIncludeHeader) {
      chkIncludeHeader.checked = false;
      if (boxInstitutionalFields) {
        boxInstitutionalFields.classList.toggle("opacity-40", true);
        boxInstitutionalFields.classList.toggle("pointer-events-none", true);
      }
    }

    // Elementos da BNCC
    modalBnccPicker = document.getElementById("modal-bncc-picker");
    btnOpenBnccModal = document.getElementById("btn-open-bncc-modal");
    btnCloseBnccModal = document.getElementById("btn-close-bncc-modal");
    btnCancelBnccModal = document.getElementById("btn-cancel-bncc-modal");
    bnccFilterDiscipline = document.getElementById("bncc-modal-filter-discipline");
    bnccFilterGrade = document.getElementById("bncc-modal-filter-grade");
    bnccSearchInput = document.getElementById("bncc-modal-search-input");
    bnccCardsList = document.getElementById("bncc-modal-cards-list");
    bnccResultsCount = document.getElementById("bncc-modal-results-count");
    bnccAutocompleteList = document.getElementById("bncc-autocomplete-list");
  }

  function updateGabaritoOutdatedBanner(isOutdated) {
    isGabaritoOutdated = Boolean(isOutdated);
    if (bannerGabaritoOutdated) {
      if (isGabaritoOutdated && currentExamHasLinkedGabarito) {
        bannerGabaritoOutdated.classList.remove("hidden");
      } else {
        bannerGabaritoOutdated.classList.add("hidden");
      }
    }
    if (badgeGabaritoOutdatedDot) {
      if (isGabaritoOutdated && currentExamHasLinkedGabarito) {
        badgeGabaritoOutdatedDot.classList.remove("hidden");
      } else {
        badgeGabaritoOutdatedDot.classList.add("hidden");
      }
    }
  }

  function initDefaultDate() {
    if (cfgDate && !cfgDate.value) {
      const today = new Date();
      const d = String(today.getDate()).padStart(2, "0");
      const m = String(today.getMonth() + 1).padStart(2, "0");
      const y = today.getFullYear();
      cfgDate.value = `${d}/${m}/${y}`;
    }
  }

  // ==========================================================================
  // Renderização da Lista de Questões (Sidebar Esquerda)
  // ==========================================================================
  function renderSidebarList() {
    if (!questionsSidebarList) return;
    questionsSidebarList.innerHTML = "";

    questions.forEach((q, idx) => {
      q.question_number = idx + 1;
      const isActive = (idx === activeQuestionIndex);

      const item = document.createElement("div");
      item.className = isActive
        ? "btn-press flex items-center justify-between p-2.5 rounded-xl bg-blue-50/90 border border-blue-400/80 text-blue-950 font-semibold shadow-2xs cursor-pointer transition-all"
        : "btn-press flex items-center justify-between p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200/80 text-slate-700 transition-all cursor-pointer";

      const numFormatted = String(q.question_number).padStart(2, "0");
      const typeLabel = `${(q.alternatives && q.alternatives.length) || globalExamAlternativesMode} Alternativas`;

      item.innerHTML = `
        <div class="flex items-center gap-2.5 min-w-0">
          <span class="w-6 h-6 rounded-md ${isActive ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-700'} flex items-center justify-center font-bold text-xs shrink-0">${numFormatted}</span>
          <span class="text-xs truncate ${isActive ? 'font-bold text-blue-950' : 'font-medium text-slate-700'}">${typeLabel}</span>
        </div>
        <div class="flex items-center gap-1.5 shrink-0">
          <span class="text-[11px] font-bold ${isActive ? 'text-blue-700' : 'text-slate-500'}">${parseFloat(q.points || 1).toFixed(1)} pt</span>
          <span class="material-symbols-outlined text-[15px] ${isActive ? 'text-blue-600' : 'text-slate-400'}">${isActive ? 'edit' : 'chevron_right'}</span>
        </div>
      `;

      item.addEventListener("click", () => {
        saveCurrentEditorState();
        activeQuestionIndex = idx;
        renderSidebarList();
        loadActiveQuestionToEditor();
      });

      questionsSidebarList.appendChild(item);
    });

    if (sidebarQuestionBadge) sidebarQuestionBadge.textContent = `${(questions || []).length} itens`;
    if (chipQuestionCount) chipQuestionCount.textContent = `${(questions || []).length} Questões`;
  }

  // ==========================================================================
  // Carregar Questão Ativa para o Editor Principal
  // ==========================================================================
  function loadActiveQuestionToEditor() {
    if (questions.length === 0) return;
    if (activeQuestionIndex >= questions.length) activeQuestionIndex = questions.length - 1;

    const q = questions[activeQuestionIndex] || {};
    const numFormatted = String(q.question_number || (activeQuestionIndex + 1)).padStart(2, "0");

    if (editorQNumBadge) editorQNumBadge.textContent = numFormatted;
    if (editorQTitle) editorQTitle.textContent = `Questão ${numFormatted}`;
    if (editorQStatement) editorQStatement.value = q.statement || "";
    if (editorQStatementRich) {
      deserializeWordEditor(q.statement || "", editorQStatementRich);
    }
    if (editorQPoints) editorQPoints.value = parseFloat(q.points || 1.0).toFixed(2);
    if (editorQDifficulty) editorQDifficulty.value = q.difficulty || "medio";
    if (editorQSkill) editorQSkill.value = q.bncc_code || q.skill || "";
    q.type = String(globalExamAlternativesMode || 4);

    // Imagem da Questão (migração transparente se houver image_url antiga)
    if (q.image_url && !(q.statement || "").includes(q.image_url)) {
      const legacyPos = q.image_position === "right" ? "right" : (q.image_position === "left" ? "left" : "center");
      const legacyW = q.image_width || "220px";
      q.statement = (q.statement || "") + `\n<img src="${q.image_url}" class="exam-img-figure align-${legacyPos}" style="width: ${legacyW};" data-src="${q.image_url}" data-align="${legacyPos}" data-width="${legacyW}" />\n`;
      if (editorQStatementRich) {
        deserializeWordEditor(q.statement, editorQStatementRich);
      }
    }

    // Atualiza a Prévia Oficial em Tempo Real
    try { updateRealtimeQuestionPreview(); } catch (e) { }

    // Alternativas
    try { renderEditorAlternatives(q); } catch (e) { console.warn("renderEditorAlternatives:", e); }

    // Labels de Próximo e Anterior
    const btnPrevQ = document.getElementById("btn-prev-question");
    if (activeQuestionIndex > 0) {
      if (prevQuestionLabel) prevQuestionLabel.textContent = `Questão Anterior (${String(activeQuestionIndex).padStart(2, "0")})`;
      if (btnPrevQ) btnPrevQ.classList.remove("opacity-40", "pointer-events-none");
    } else {
      if (prevQuestionLabel) prevQuestionLabel.textContent = "Primeira Questão";
      if (btnPrevQ) btnPrevQ.classList.add("opacity-40", "pointer-events-none");
    }

    if (activeQuestionIndex < questions.length - 1) {
      if (nextQuestionLabel) nextQuestionLabel.textContent = `Próxima Questão (${String(activeQuestionIndex + 2).padStart(2, "0")})`;
    } else {
      if (nextQuestionLabel) nextQuestionLabel.textContent = "Nova Questão (+)";
    }

    activeTextarea = editorQStatement;
  }

  // Renderiza as alternativas dentro do editor
  function renderEditorAlternatives(q) {
    if (!editorAlternativesList) return;
    editorAlternativesList.innerHTML = "";

    const targetCount = globalExamAlternativesMode === 4 ? 4 : 5;
    if (!q.alternatives) q.alternatives = [];
    if (q.alternatives.length > targetCount) {
      const wasCorrectRemoved = q.alternatives.slice(targetCount).some(a => a.is_correct);
      q.alternatives = q.alternatives.slice(0, targetCount);
      if (wasCorrectRemoved && q.alternatives.length > 0) {
        q.alternatives[0].is_correct = true;
      }
    } else {
      while (q.alternatives.length < targetCount) {
        const nextIdx = q.alternatives.length;
        q.alternatives.push({
          letter: String.fromCharCode(65 + nextIdx),
          text: "",
          is_correct: false
        });
      }
    }
    q.alternatives.forEach((a, i) => a.letter = String.fromCharCode(65 + i));

    const sectionAlts = document.getElementById("section-alternatives");
    if (sectionAlts) sectionAlts.classList.remove("hidden");

    (q.alternatives || []).forEach((alt, altIdx) => {
      if (!alt.image && alt.image_url) {
        alt.image = {
          url: alt.image_url,
          width: alt.image_width || "180px",
          align: alt.image_align || "center"
        };
      }
      const isCorrect = Boolean(alt.is_correct);
      const letter = alt.letter || String.fromCharCode(65 + altIdx);

      const row = document.createElement("div");
      row.className = isCorrect ? "alt-card-row is-correct" : "alt-card-row";

      const hasMath = alt.text && (alt.text.includes("$") || alt.text.includes("\\"));

      row.innerHTML = `
        <button type="button" class="alt-card-badge ${isCorrect ? 'is-correct' : ''}" title="${isCorrect ? 'Gabarito Oficial Selecionado' : 'Clique para marcar como gabarito correto'}">
          ${isCorrect ? '<span class="material-symbols-outlined text-[17px] text-white">check</span>' : letter}
        </button>
        <div class="flex-1 flex flex-col gap-1.5 min-w-0">
          <div class="flex items-center gap-2">
            <input type="text" class="alt-input-field ${isCorrect ? 'font-semibold text-emerald-950' : ''}" value="${escapeHtml(alt.text)}" placeholder="Texto da alternativa ${letter}...">
            <div class="flex items-center gap-1.5 shrink-0">
              <button type="button" class="btn-press btn-alt-image w-8 h-8 rounded-lg bg-emerald-50 hover:bg-emerald-600 text-emerald-700 hover:text-white border border-emerald-200 hover:border-emerald-600 transition-all flex items-center justify-center shrink-0 shadow-2xs" title="Inserir ou configurar imagem nesta Alternativa">
                <span class="material-symbols-outlined text-[19px]">add_photo_alternate</span>
              </button>
              <button type="button" class="btn-press btn-alt-math w-8 h-8 rounded-lg bg-blue-50 hover:bg-blue-600 text-blue-700 hover:text-white border border-blue-200 hover:border-blue-600 transition-all flex items-center justify-center shrink-0 shadow-2xs" title="Inserir Fórmula Matemática nesta Alternativa (MathType)">
                <span class="material-symbols-outlined text-[19px]">functions</span>
              </button>
            </div>
          </div>
          ${hasMath ? `<div class="alt-math-preview text-xs text-blue-900 bg-blue-50/90 px-3 py-1 rounded-lg border border-blue-200 w-fit cursor-pointer hover:bg-blue-100 transition-colors font-mono" title="Clique para editar visualmente no MathType">${escapeHtml(alt.text)}</div>` : ''}
          ${alt.image && alt.image.url ? `
            <div class="alt-image-card">
              <img src="${escapeHtml(alt.image.url)}" alt="Imagem alternativa ${letter}">
              <div class="alt-img-meta flex-1">
                <div class="flex items-center justify-between gap-2">
                  <span class="text-[11px] font-bold text-slate-700">Imagem (${alt.image.width || '180px'})</span>
                  <button type="button" class="btn-del-alt-img text-slate-400 hover:text-rose-600 p-0.5 rounded transition-colors" title="Remover Imagem">
                    <span class="material-symbols-outlined text-[16px]">delete</span>
                  </button>
                </div>
                <div class="flex items-center gap-1 mt-1 flex-wrap">
                  <button type="button" class="btn-alt-img-align inline-flex items-center justify-center w-6 h-5 rounded transition-colors ${alt.image.align === 'left' ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-700 hover:bg-slate-300'}" data-align="left" title="Alinhar à Esquerda">
                    <span class="material-symbols-outlined text-[14px] pointer-events-none">format_align_left</span>
                  </button>
                  <button type="button" class="btn-alt-img-align inline-flex items-center justify-center w-6 h-5 rounded transition-colors ${alt.image.align === 'center' ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-700 hover:bg-slate-300'}" data-align="center" title="Centralizar">
                    <span class="material-symbols-outlined text-[14px] pointer-events-none">format_align_center</span>
                  </button>
                  <button type="button" class="btn-alt-img-align inline-flex items-center justify-center w-6 h-5 rounded transition-colors ${alt.image.align === 'right' ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-700 hover:bg-slate-300'}" data-align="right" title="Alinhar à Direita">
                    <span class="material-symbols-outlined text-[14px] pointer-events-none">format_align_right</span>
                  </button>
                  <div class="w-px h-3.5 bg-slate-300 mx-0.5"></div>
                  <button type="button" class="btn-alt-img-size text-[10px] font-bold px-1.5 py-0.5 rounded transition-colors ${alt.image.width === '100px' ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-700 hover:bg-slate-300'}" data-size="100px" title="Pequeno (100px)">P</button>
                  <button type="button" class="btn-alt-img-size text-[10px] font-bold px-1.5 py-0.5 rounded transition-colors ${(alt.image.width === '180px' || !alt.image.width) ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-700 hover:bg-slate-300'}" data-size="180px" title="Médio (180px)">M</button>
                  <button type="button" class="btn-alt-img-size text-[10px] font-bold px-1.5 py-0.5 rounded transition-colors ${alt.image.width === '260px' ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-700 hover:bg-slate-300'}" data-size="260px" title="Grande (260px)">G</button>
                </div>
              </div>
            </div>
          ` : ''}
        </div>
        ${isCorrect ? '<span class="px-2.5 py-1 rounded-md bg-emerald-100 text-emerald-800 text-[11px] font-bold whitespace-nowrap shrink-0 border border-emerald-300">Gabarito Correto</span>' : ''}
      `;

      // Renderiza KaTeX na prévia da alternativa se houver
      const mathPrev = row.querySelector(".alt-math-preview");
      if (mathPrev && window.renderMathInElement) {
        renderMathInElement(mathPrev, {
          delimiters: [
            { left: "$$", right: "$$", display: true },
            { left: "$", right: "$", display: false },
            { left: "\\(", right: "\\)", display: false }
          ],
          macros: KATEX_MACROS,
          throwOnError: false
        });

        mathPrev.addEventListener("click", () => {
          const rawMath = (alt.text || "").replace(/\$/g, "").trim();
          openVisualMathModal(rawMath, { type: "alternative", altIndex: altIdx });
        });
      }

      // Botão com Símbolo de Matemática (MathType) na Alternativa
      const mathBtn = row.querySelector(".btn-alt-math");
      if (mathBtn) {
        mathBtn.addEventListener("click", () => {
          const rawMath = (alt.text && (alt.text.includes("$") || alt.text.includes("\\"))) ? alt.text.replace(/\$/g, "").trim() : "";
          openVisualMathModal(rawMath, { type: "alternative", altIndex: altIdx });
        });
      }

      // Botão de Imagem na Alternativa
      const imgBtn = row.querySelector(".btn-alt-image");
      if (imgBtn) {
        imgBtn.addEventListener("click", () => {
          const currentUrl = (alt.image && alt.image.url) ? alt.image.url : (alt.image_url || "");
          const currentAlign = (alt.image && alt.image.align) ? alt.image.align : (alt.image_align || "left");
          const currentWidth = (alt.image && alt.image.width) ? alt.image.width : (alt.image_width || "180px");
          openImageConfigModal({
            type: "alternative",
            altIndex: altIdx,
            url: currentUrl,
            align: currentAlign,
            width: currentWidth
          });
        });
      }

      // Remover Imagem da Alternativa
      const delAltImgBtn = row.querySelector(".btn-del-alt-img");
      if (delAltImgBtn) {
        delAltImgBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          delete alt.image;
          delete alt.image_url;
          delete alt.image_width;
          delete alt.image_align;
          renderEditorAlternatives(q);
          updateRealtimeQuestionPreview();
          updateLiveSheetPreview();
          markUnsaved();
          showToast("Imagem da alternativa removida.", "info");
        });
      }

      // Alinhamento rápido na Alternativa
      row.querySelectorAll(".btn-alt-img-align").forEach(b => {
        b.addEventListener("click", (e) => {
          e.stopPropagation();
          if (!alt.image && !alt.image_url) return;
          if (!alt.image) {
            alt.image = { url: alt.image_url, width: alt.image_width || "180px", align: "left" };
          }
          const newAlign = b.getAttribute("data-align");
          alt.image.align = newAlign;
          alt.image_align = newAlign;
          renderEditorAlternatives(q);
          updateRealtimeQuestionPreview();
          updateLiveSheetPreview();
          markUnsaved();
        });
      });

      // Tamanho rápido na Alternativa
      row.querySelectorAll(".btn-alt-img-size").forEach(b => {
        b.addEventListener("click", (e) => {
          e.stopPropagation();
          if (!alt.image && !alt.image_url) return;
          if (!alt.image) {
            alt.image = { url: alt.image_url, width: "180px", align: alt.image_align || "left" };
          }
          const newSize = b.getAttribute("data-size");
          alt.image.width = newSize;
          alt.image_width = newSize;
          renderEditorAlternatives(q);
          updateRealtimeQuestionPreview();
          updateLiveSheetPreview();
          markUnsaved();
        });
      });

      // Clique no badge marca como correto
      const checkBtn = row.querySelector(".alt-card-badge");
      checkBtn.addEventListener("click", () => {
        q.alternatives.forEach((a, i) => a.is_correct = (i === altIdx));
        renderEditorAlternatives(q);
        updateRealtimeQuestionPreview();
        markUnsaved();
      });

      // Digitação no input
      const altInput = row.querySelector("input");
      altInput.addEventListener("input", (e) => {
        alt.text = e.target.value;
        const prev = row.querySelector(".alt-math-preview");
        if (prev && window.renderMathInElement) {
          prev.textContent = e.target.value;
          renderMathInElement(prev, {
            delimiters: [
              { left: "$$", right: "$$", display: true },
              { left: "$", right: "$", display: false },
              { left: "\\(", right: "\\)", display: false }
            ],
            macros: KATEX_MACROS,
            throwOnError: false
          });
        }
        updateRealtimeQuestionPreview();
        markUnsaved();
      });

      editorAlternativesList.appendChild(row);
    });
  }

  // ==========================================================================
  // Salvamento do Estado do Editor
  // ==========================================================================
  function saveCurrentEditorState() {
    if (questions.length === 0 || activeQuestionIndex >= questions.length) return;
    const q = questions[activeQuestionIndex];

    if (editorQStatementRich) {
      q.statement = serializeWordEditor(editorQStatementRich);
      editorQStatement.value = q.statement;
    } else {
      q.statement = editorQStatement.value;
    }
    q.points = parseFloat(editorQPoints.value) || 1.0;
    q.difficulty = editorQDifficulty.value;
    const currentSkill = editorQSkill ? editorQSkill.value.trim() : "";
    q.skill = currentSkill;
    q.bncc_code = currentSkill;
    q.type = String(globalExamAlternativesMode);
  }

  // ==========================================================================
  // Atualização dos Sumários & Chips
  // ==========================================================================
  function updateSummaryBars() {
    let totalPoints = 0;
    (questions || []).forEach(q => {
      totalPoints += parseFloat(q.points || 1.0);
    });

    const totalStr = totalPoints.toFixed(1).replace(".", ",");

    if (chipTotalScore) chipTotalScore.textContent = `${totalStr} pts`;
    if (sidebarTotalScore) sidebarTotalScore.textContent = `Total: ${totalStr} pts`;
    if (footerScoreRatio) footerScoreRatio.textContent = `${totalStr} pts (${(questions || []).length} questões)`;

    const disc = cfgDiscipline?.value?.trim() || "MATEMÁTICA";
    const grade = cfgGrade?.value?.trim() || "9º ANO";
    if (chipDisciplineDisplay) chipDisciplineDisplay.textContent = `${disc} • ${grade}`;

    const configuredCount = (questions || []).filter(q => ((q && q.statement) ? String(q.statement).trim().length > 0 : false)).length;
    if (footerConfiguredStatus) footerConfiguredStatus.textContent = `${configuredCount} de ${(questions || []).length} questões configuradas`;
  }

  // ==========================================================================
  // Pré-visualização KaTeX & Folha A4 em Tempo Real (Split View)
  // ==========================================================================
  let liveSheetDebounceTimer = null;

  function updateRealtimeQuestionPreview() {
    clearTimeout(liveSheetDebounceTimer);
    liveSheetDebounceTimer = setTimeout(() => {
      updateLiveSheetPreview();
    }, 60);
  }

  function updateLiveSheetPreview() {
    const flowContainer = document.getElementById("sheet-questions-live-flow");
    if (!flowContainer) return;

    // Atualiza metadados do cabeçalho institucional da folha A4
    const lblSchool = document.getElementById("sheet-lbl-school");
    const lblTeacher = document.getElementById("sheet-lbl-teacher");
    const lblDiscipline = document.getElementById("sheet-lbl-discipline");
    const lblGrade = document.getElementById("sheet-lbl-grade");
    const lblDate = document.getElementById("sheet-lbl-date");
    const lblScore = document.getElementById("sheet-lbl-score");

    if (lblSchool && cfgSchool) lblSchool.textContent = cfgSchool.value.trim() || "Escola Municipal";
    if (lblTeacher && cfgTeacher) lblTeacher.textContent = cfgTeacher.value.trim() || "Professor(a)";
    if (lblDiscipline && cfgDiscipline) lblDiscipline.textContent = cfgDiscipline.value.trim() || "MATEMÁTICA";
    if (lblGrade && cfgGrade) lblGrade.textContent = cfgGrade.value.trim() || "9º ANO";
    if (lblDate && cfgDate) lblDate.textContent = cfgDate.value.trim() || "--/--/----";
    if (lblScore) {
      let totalPts = 0;
      questions.forEach(q => { totalPts += parseFloat(q.points || 1.0); });
      lblScore.textContent = `${totalPts.toFixed(1).replace(".", ",")} pts`;
    }

    // Sincroniza margens em centímetros no preview ao vivo
    const sheet = document.getElementById("live-a4-sheet");
    if (sheet && cfgMarginTop && cfgMarginBottom && cfgMarginLeft && cfgMarginRight) {
      const mt = parseFloat(cfgMarginTop.value) || 3.0;
      const mb = parseFloat(cfgMarginBottom.value) || 2.0;
      const ml = parseFloat(cfgMarginLeft.value) || 3.0;
      const mr = parseFloat(cfgMarginRight.value) || 2.0;
      sheet.style.paddingTop = `${mt}cm`;
      sheet.style.paddingBottom = `${mb}cm`;
      sheet.style.paddingLeft = `${ml}cm`;
      sheet.style.paddingRight = `${mr}cm`;
    }

    // Renderiza a lista de questões com layout oficial A4
    flowContainer.innerHTML = "";

    questions.forEach((q, qIdx) => {
      const isCurrentActive = (qIdx === activeQuestionIndex);
      const qNum = String(q.question_number || (qIdx + 1)).padStart(2, "0");
      const qPts = parseFloat(q.points || 1.0).toFixed(1).replace(".", ",");
      const item = document.createElement("div");
      item.className = `sheet-question-item transition-all ${isCurrentActive ? 'bg-blue-50/50 p-3 rounded-lg border border-blue-200/90 -mx-1' : ''}`;

      // Enunciado
      let statementHtml = q.statement || `<span class="text-slate-400 italic">Digite o enunciado da questão ${qNum}...</span>`;

      let imageHtml = "";
      if (q.image_url) {
        imageHtml = `<div class="my-2"><img src="${escapeHtml(q.image_url)}" class="max-h-36 rounded border border-slate-200"></div>`;
      }

      // Alternativas
      let altsHtml = "";
      if (q.type === "5" || q.type === "4") {
        altsHtml = `<div class="sheet-alt-list">`;
        (q.alternatives || []).forEach((alt, aIdx) => {
          const letter = alt.letter || String.fromCharCode(65 + aIdx);
          const altText = alt.text || "...";
          const isCorrect = Boolean(alt.is_correct);
          const altImg = alt.image || (alt.image_url ? { url: alt.image_url, align: alt.image_align || 'left', width: alt.image_width || '180px' } : null);
          let altImgHtml = "";
          if (altImg && altImg.url) {
            const align = altImg.align || alt.image_align || "left";
            const width = altImg.width || alt.image_width || "180px";
            altImgHtml = `<div class="alt-img-display align-${align}" style="width: ${width}; max-width: 100%; margin-top: 3px;"><img src="${escapeHtml(altImg.url)}" class="rounded" style="width: 100%;" /></div>`;
          }
          altsHtml += `
            <div class="sheet-alt-row items-start">
              <span class="sheet-alt-letter font-mono font-bold ${isCorrect ? 'text-emerald-700 font-extrabold' : 'text-slate-900'}">( ${letter} )</span>
              <div class="flex-1 flex flex-col">
                <span class="sheet-alt-text ${isCorrect ? 'font-semibold text-emerald-950' : 'text-slate-800'}">${escapeHtml(altText)}</span>
                ${altImgHtml}
              </div>
            </div>
          `;
        });
        altsHtml += `</div>`;
      } else if (q.type === "dissertativa") {
        altsHtml = `
          <div class="border-b border-dashed border-slate-300 h-6 my-1"></div>
          <div class="border-b border-dashed border-slate-300 h-6 my-1"></div>
          <div class="border-b border-dashed border-slate-300 h-6 my-1"></div>
        `;
      }

      item.innerHTML = `
        <div class="sheet-question-title flex items-center justify-between">
          <span class="flex items-center gap-1.5">
            <span>Questão ${qNum}</span>
            ${isCurrentActive ? '<span class="text-[9px] font-bold uppercase tracking-wider bg-blue-600 text-white px-1.5 py-0.2 rounded">Editando</span>' : ''}
          </span>
          <span class="text-[11px] font-semibold text-slate-500 font-sans">(${qPts} pt)</span>
        </div>
        <div class="sheet-question-statement">${statementHtml}</div>
        ${imageHtml}
        ${altsHtml}
      `;

      flowContainer.appendChild(item);
    });

    // Renderiza KaTeX em toda a folha ao vivo
    if (window.renderMathInElement) {
      try {
        renderMathInElement(flowContainer, {
          delimiters: [
            { left: "$$", right: "$$", display: true },
            { left: "$", right: "$", display: false },
            { left: "\\(", right: "\\)", display: false },
            { left: "\\[", right: "\\]", display: true }
          ],
          macros: KATEX_MACROS,
          throwOnError: false
        });
      } catch (e) { }
    }
  }

  function updateMathPreview(text) {
    if (!editorMathPreviewContainer || !editorMathPreviewContent) return;

    if (text && (text.includes("$") || text.includes("\\"))) {
      editorMathPreviewContent.innerHTML = escapeHtml(text);
      editorMathPreviewContainer.classList.remove("hidden");
      if (window.renderMathInElement) {
        renderMathInElement(editorMathPreviewContent, {
          delimiters: [
            { left: "$$", right: "$$", display: true },
            { left: "$", right: "$", display: false },
            { left: "\\(", right: "\\)", display: false },
            { left: "\\[", right: "\\]", display: true }
          ],
          throwOnError: false
        });
      }
    } else {
      editorMathPreviewContainer.classList.add("hidden");
      editorMathPreviewContent.innerHTML = "";
    }
  }

  // ==========================================================================
  // Configuração dos Eventos Gerais
  // ==========================================================================
  function setupEventListeners() {
    // Título da Prova
    examTitleInput.addEventListener("input", markUnsaved);

    // Inputs do Editor
    editorQStatement.addEventListener("input", (e) => {
      questions[activeQuestionIndex].statement = e.target.value;
      updateMathPreview(e.target.value);
      updateRealtimeQuestionPreview();
      markUnsaved();
    });

    editorQPoints.addEventListener("input", (e) => {
      questions[activeQuestionIndex].points = parseFloat(e.target.value) || 0;
      renderSidebarList();
      updateSummaryBars();
      markUnsaved();
    });

    editorQDifficulty.addEventListener("change", (e) => {
      questions[activeQuestionIndex].difficulty = e.target.value;
      markUnsaved();
    });

    editorQSkill.addEventListener("input", (e) => {
      questions[activeQuestionIndex].skill = e.target.value;
      markUnsaved();
    });

    function setGlobalExamAlternativesMode(mode) {
      globalExamAlternativesMode = parseInt(mode, 10) || 5;
      if (cfgExamAlternativesMode) cfgExamAlternativesMode.value = String(globalExamAlternativesMode);

      if (btnModalAlt4 && btnModalAlt5) {
        if (globalExamAlternativesMode === 4) {
          btnModalAlt4.className = "flex-1 py-1 rounded text-xs font-bold bg-primary-container text-on-primary shadow-sm transition-colors active";
          btnModalAlt5.className = "flex-1 py-1 rounded text-xs font-bold text-on-surface-variant transition-colors";
        } else {
          btnModalAlt5.className = "flex-1 py-1 rounded text-xs font-bold bg-primary-container text-on-primary shadow-sm transition-colors active";
          btnModalAlt4.className = "flex-1 py-1 rounded text-xs font-bold text-on-surface-variant transition-colors";
        }
      }

      // Aplica a quantidade oficial de alternativas em todas as questões da prova
      questions.forEach(q => {
        q.type = String(globalExamAlternativesMode);
        if (!q.alternatives) q.alternatives = [];
        if (globalExamAlternativesMode === 4 && q.alternatives.length > 4) {
          const wasCorrectE = q.alternatives[4] && q.alternatives[4].is_correct;
          q.alternatives = q.alternatives.slice(0, 4);
          if (wasCorrectE && q.alternatives.length > 0) {
            q.alternatives[0].is_correct = true;
          }
        } else if (globalExamAlternativesMode === 5 && q.alternatives.length === 4) {
          q.alternatives.push({ letter: "E", text: "", is_correct: false });
        }
      });

      const activeQ = questions[activeQuestionIndex];
      if (activeQ) renderEditorAlternatives(activeQ);
      renderSidebarList();
      updateRealtimeQuestionPreview();
      updateLiveSheetPreview();
      markUnsaved();
      showToast(`Prova configurada para ${globalExamAlternativesMode} Alternativas!`, "info");
    }

    if (cfgExamAlternativesMode) {
      cfgExamAlternativesMode.addEventListener("change", (e) => {
        setGlobalExamAlternativesMode(e.target.value);
      });
    }
    if (btnModalAlt4) {
      btnModalAlt4.addEventListener("click", () => setGlobalExamAlternativesMode(4));
    }
    if (btnModalAlt5) {
      btnModalAlt5.addEventListener("click", () => setGlobalExamAlternativesMode(5));
    }

    // Helper para registro seguro de eventos em botões/elementos
    function safeOn(id, event, handler) {
      const el = document.getElementById(id);
      if (el) el.addEventListener(event, handler);
    }

    // Adicionar Nova Questão
    safeOn("btn-add-question-side", "click", () => {
      addNewQuestion();
    });

    // Duplicar Questão
    safeOn("btn-duplicate-question", "click", () => {
      saveCurrentEditorState();
      const current = questions[activeQuestionIndex];
      const copy = JSON.parse(JSON.stringify(current));
      copy.id = "q_" + Date.now();
      copy.question_number = questions.length + 1;
      questions.splice(activeQuestionIndex + 1, 0, copy);
      activeQuestionIndex = activeQuestionIndex + 1;
      renderSidebarList();
      loadActiveQuestionToEditor();
      updateSummaryBars();
      showToast("Questão duplicada!", "success");
      markUnsaved();
    });

    // Excluir Questão
    safeOn("btn-delete-question", "click", async () => {
      if (questions.length <= 1) {
        showToast("A prova precisa ter ao menos uma questão.", "warning");
        return;
      }
      const qNum = String(questions[activeQuestionIndex].question_number).padStart(2, "0");
      const confirmed = await showConfirmModal({
        title: `Excluir a Questão ${qNum}?`,
        message: "Esta questão e todas as suas alternativas e configurações serão removidas permanentemente da avaliação.",
        confirmText: "Sim, Excluir",
        cancelText: "Cancelar",
        type: "danger"
      });
      if (confirmed) {
        questions.splice(activeQuestionIndex, 1);
        if (activeQuestionIndex >= questions.length) activeQuestionIndex = questions.length - 1;
        renderSidebarList();
        loadActiveQuestionToEditor();
        updateSummaryBars();
        showToast("Questão excluída.", "info");
        markUnsaved();
      }
    });

    // Navegação Anterior / Próxima
    safeOn("btn-prev-question", "click", () => {
      if (activeQuestionIndex > 0) {
        saveCurrentEditorState();
        activeQuestionIndex--;
        renderSidebarList();
        loadActiveQuestionToEditor();
      }
    });

    safeOn("btn-next-question", "click", () => {
      saveCurrentEditorState();
      if (activeQuestionIndex < questions.length - 1) {
        activeQuestionIndex++;
        renderSidebarList();
        loadActiveQuestionToEditor();
      } else {
        addNewQuestion();
      }
    });

    // Upload de Imagem
    safeOn("input-q-image", "change", async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      const formData = new FormData();
      formData.append("file", file);

      try {
        showToast("Enviando imagem...", "info");
        const res = await apiFetch("/api/exam-builder/upload-image", { method: "POST", body: formData });
        if (res.ok) {
          const data = await res.json();
          questions[activeQuestionIndex].image_url = data.url;
          editorImagePreview.src = data.url;
          editorImagePreviewContainer.classList.remove("hidden");
          showToast("Imagem anexada com sucesso!", "success");
          markUnsaved();
        } else {
          showToast("Falha no upload da imagem.", "error");
        }
      } catch (err) {
        showToast("Erro de rede no upload da imagem.", "error");
      }
    });

    // Remover Imagem
    safeOn("btn-remove-image", "click", () => {
      questions[activeQuestionIndex].image_url = "";
      editorImagePreviewContainer.classList.add("hidden");
      editorImagePreview.src = "";
      markUnsaved();
    });

    // Modal Margens
    safeOn("btn-open-margins-modal", "click", openMarginsModal);
    safeOn("btn-top-margins-chip", "click", openMarginsModal);
    safeOn("btn-footer-open-margins", "click", openMarginsModal);
    safeOn("btn-close-margins", "click", closeMarginsModal);
    safeOn("btn-save-margins-close", "click", closeMarginsModal);

    // Modal Pré-visualização
    safeOn("btn-header-preview", "click", openPreviewModal);
    safeOn("btn-quick-preview-student", "click", openPreviewModal);
    safeOn("btn-close-preview", "click", () => {
      modalPreview.classList.remove("active");
      previewFrame.src = "about:blank";
    });
    safeOn("btn-modal-refresh", "click", refreshPreview);
    safeOn("btn-modal-print", "click", () => {
      if (previewFrame.contentWindow) {
        previewFrame.contentWindow.focus();
        previewFrame.contentWindow.print();
      }
    });
    safeOn("btn-modal-download-pdf", "click", downloadPdf);

    // Modal Gabarito e Sincronização OMR Completa com Capas Oficiais
    safeOn("btn-header-gabarito", "click", openSyncGabaritoModal);
    safeOn("btn-banner-update-gabarito", "click", openSyncGabaritoModal);
    safeOn("btn-close-sync-gabarito", "click", closeSyncGabaritoModal);
    safeOn("btn-cancel-sync-gabarito", "click", closeSyncGabaritoModal);
    safeOn("btn-confirm-sync-gabarito", "click", handleConfirmSyncGabarito);
    safeOn("sync-success-btn-close", "click", () => {
      document.getElementById("modal-sync-gabarito-success")?.classList.remove("active");
    });

    const modalSyncGab = document.getElementById("modal-sync-gabarito");
    if (modalSyncGab) {
      modalSyncGab.addEventListener("click", (e) => {
        if (e.target === modalSyncGab) closeSyncGabaritoModal();
      });
    }
    const modalSyncSuccess = document.getElementById("modal-sync-gabarito-success");
    if (modalSyncSuccess) {
      modalSyncSuccess.addEventListener("click", (e) => {
        if (e.target === modalSyncSuccess) modalSyncSuccess.classList.remove("active");
      });
    }

    document.querySelectorAll('input[name="sync_cover_model"]').forEach(r => {
      r.addEventListener("change", updateCoverRadiosVisual);
    });

    // Modal Minhas Provas
    safeOn("btn-open-my-exams", "click", openMyExamsModal);
    safeOn("btn-close-my-exams", "click", () => modalMyExams.classList.remove("active"));

    // Ações de Download e Exportação (Emitir Prova)
    safeOn("btn-header-download-pdf", "click", openEmitirProvaModal);
    safeOn("btn-close-emitir-modal", "click", closeEmitirProvaModal);
    safeOn("btn-cancel-emitir-modal", "click", closeEmitirProvaModal);
    safeOn("btn-confirm-emitir-download", "click", confirmEmitirDownload);
    safeOn("card-fmt-pdf", "click", () => selectEmitirFormat("pdf"));
    safeOn("card-fmt-docx", "click", () => selectEmitirFormat("docx"));

    // Controles do Painel de Pré-visualização A4 em Tempo Real
    const btnZoomToggle = document.getElementById("btn-zoom-toggle");
    if (btnZoomToggle) {
      btnZoomToggle.addEventListener("click", () => {
        const sheet = document.getElementById("live-a4-sheet");
        if (!sheet) return;
        const currentScale = sheet.style.transform || "";
        if (currentScale.includes("0.85") || currentScale.includes("0.8")) {
          sheet.style.transform = "scale(1)";
          btnZoomToggle.innerHTML = '<i class="fa-solid fa-magnifying-glass-minus text-xs"></i> 100%';
        } else {
          sheet.style.transform = "scale(0.85)";
          btnZoomToggle.innerHTML = '<i class="fa-solid fa-magnifying-glass-plus text-xs"></i> 85%';
        }
      });
    }

    const btnPreviewExpand = document.getElementById("btn-preview-expand");
    if (btnPreviewExpand) {
      btnPreviewExpand.addEventListener("click", openPreviewModal);
    }

    // Inputs de Cabeçalho Institucional - sincronização em tempo real com a folha A4
    [cfgSchool, cfgTeacher, cfgDiscipline, cfgGrade, cfgDate, examTitleInput].forEach(inp => {
      if (inp) {
        inp.addEventListener("input", () => {
          updateSummaryBars();
          updateLiveSheetPreview();
          markUnsaved();
        });
        inp.addEventListener("change", () => {
          updateSummaryBars();
          updateLiveSheetPreview();
          markUnsaved();
        });
      }
    });

    cfgSchool?.addEventListener("input", (e) => updateClassroomsDatalist(e.target.value));
    cfgSchool?.addEventListener("change", (e) => updateClassroomsDatalist(e.target.value));
    cfgClassroom?.addEventListener("change", (e) => autoDetectGradeFromClassroom(e.target.value));

    // Detecção de Conexão Online/Offline
    window.addEventListener("online", () => {
      updateNetworkStatus();
      showToast("Conexão restabelecida! Sincronizando com o sistema...", "info");
    });
    window.addEventListener("offline", () => {
      updateNetworkStatus();
      showToast("Você está offline. As alterações continuarão salvas no seu dispositivo.", "warning");
    });
  }

  function addNewQuestion() {
    saveCurrentEditorState();
    const newId = "q_" + Date.now();
    const altsCount = globalExamAlternativesMode === 4 ? 4 : 5;
    const alts = Array.from({ length: altsCount }, (_, i) => ({
      letter: String.fromCharCode(65 + i),
      text: "",
      is_correct: false
    }));
    questions.push({
      id: newId,
      question_number: questions.length + 1,
      statement: "",
      points: 1.0,
      difficulty: "medio",
      skill: "",
      bncc_code: "",
      type: String(altsCount),
      image_url: "",
      alternatives: alts
    });
    activeQuestionIndex = questions.length - 1;
    renderSidebarList();
    loadActiveQuestionToEditor();
    updateSummaryBars();
    markUnsaved();
    editorQStatement.focus();
    showToast("Nova questão adicionada!", "success");
  }

  // ==========================================================================
  // Sistema de Margens e Presets (A4 PDF)
  // ==========================================================================
  function setupMarginsSystem() {
    document.querySelectorAll(".canoa-preset-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const key = btn.getAttribute("data-preset");
        if (MARGIN_PRESETS[key]) {
          const p = MARGIN_PRESETS[key];
          cfgMarginTop.value = p.top;
          cfgMarginBottom.value = p.bottom;
          cfgMarginLeft.value = p.left;
          cfgMarginRight.value = p.right;

          document.querySelectorAll(".canoa-preset-btn").forEach(b => {
            b.classList.remove("bg-primary-container", "text-on-primary", "active");
            b.classList.add("bg-surface-container-lowest");
          });
          btn.classList.add("bg-primary-container", "text-on-primary", "active");
          btn.classList.remove("bg-surface-container-lowest");

          if (chipMarginsDisplay) chipMarginsDisplay.textContent = `Margens: ${p.label}`;
          markUnsaved();
        }
      });
    });

    [cfgMarginTop, cfgMarginBottom, cfgMarginLeft, cfgMarginRight].forEach(inp => {
      inp.addEventListener("input", () => {
        let val = parseFloat(inp.value);
        if (isNaN(val)) val = (inp === cfgMarginTop || inp === cfgMarginLeft) ? 3.0 : 2.0;
        if (val < 0.4) val = 0.4;
        if (val > 4.0) val = 4.0;
        inp.value = val;

        syncMarginsPresetButtons();
        updateLiveSheetPreview();
        markUnsaved();
      });
    });

    // Colunas
    if (btnCol1) {
      btnCol1.addEventListener("click", () => {
        selectedColumns = 1;
        btnCol1.classList.add("bg-primary-container", "text-on-primary", "shadow-sm", "active");
        if (btnCol2) {
          btnCol2.classList.remove("bg-primary-container", "text-on-primary", "shadow-sm", "active");
          btnCol2.classList.add("text-on-surface-variant");
        }
        markUnsaved();
      });
    }

    if (btnCol2) {
      btnCol2.addEventListener("click", () => {
        selectedColumns = 2;
        btnCol2.classList.add("bg-primary-container", "text-on-primary", "shadow-sm", "active");
        if (btnCol1) {
          btnCol1.classList.remove("bg-primary-container", "text-on-primary", "shadow-sm", "active");
          btnCol1.classList.add("text-on-surface-variant");
        }
        markUnsaved();
      });
    }

    if (chkAnswerSheet) chkAnswerSheet.addEventListener("change", markUnsaved);

    if (chkIncludeHeader) {
      chkIncludeHeader.addEventListener("change", () => {
        if (boxInstitutionalFields) {
          boxInstitutionalFields.classList.toggle("opacity-40", !chkIncludeHeader.checked);
          boxInstitutionalFields.classList.toggle("pointer-events-none", !chkIncludeHeader.checked);
        }
        markUnsaved();
      });
    }
  }

  function syncMarginsPresetButtons() {
    if (!cfgMarginTop || !cfgMarginBottom || !cfgMarginLeft || !cfgMarginRight) return;
    let t = parseFloat(cfgMarginTop.value);
    let b = parseFloat(cfgMarginBottom.value);
    let l = parseFloat(cfgMarginLeft.value);
    let r = parseFloat(cfgMarginRight.value);

    if (isNaN(t)) t = 3.0;
    if (isNaN(b)) b = 2.0;
    if (isNaN(l)) l = 3.0;
    if (isNaN(r)) r = 2.0;

    // Converte automaticamente se vier em mm (> 4.0)
    if (t > 4.0) { t = +(t / 10).toFixed(1); cfgMarginTop.value = t; }
    if (b > 4.0) { b = +(b / 10).toFixed(1); cfgMarginBottom.value = b; }
    if (l > 4.0) { l = +(l / 10).toFixed(1); cfgMarginLeft.value = l; }
    if (r > 4.0) { r = +(r / 10).toFixed(1); cfgMarginRight.value = r; }

    let matched = null;
    for (const [key, p] of Object.entries(MARGIN_PRESETS)) {
      if (Math.abs(p.top - t) < 0.05 && Math.abs(p.bottom - b) < 0.05 && Math.abs(p.left - l) < 0.05 && Math.abs(p.right - r) < 0.05) {
        matched = key;
        break;
      }
    }

    document.querySelectorAll(".canoa-preset-btn").forEach(btn => {
      if (matched && btn.getAttribute("data-preset") === matched) {
        btn.classList.add("bg-primary-container", "text-on-primary", "active");
        btn.classList.remove("bg-surface-container-lowest");
        if (chipMarginsDisplay) chipMarginsDisplay.textContent = `Margens: ${MARGIN_PRESETS[matched].label}`;
      } else {
        btn.classList.remove("bg-primary-container", "text-on-primary", "active");
        btn.classList.add("bg-surface-container-lowest");
      }
    });

    if (!matched && chipMarginsDisplay) {
      chipMarginsDisplay.textContent = `Margens: ${t.toFixed(1)} cm / ${b.toFixed(1)} cm`;
    }
  }

  function openMarginsModal() {
    modalMargins.classList.add("active");
  }

  function closeMarginsModal() {
    modalMargins.classList.remove("active");
    syncMarginsPresetButtons();
    updateSummaryBars();
  }

  // ==========================================================================
  function setupWordRibbon() {
    // 1. Formatação de texto (Negrito, Itálico, Sublinhado, Listas, Limpar)
    const btnBold = document.getElementById("btn-format-bold");
    if (btnBold) btnBold.addEventListener("click", () => formatRichText("bold"));

    const btnItalic = document.getElementById("btn-format-italic");
    if (btnItalic) btnItalic.addEventListener("click", () => formatRichText("italic"));

    const btnUnderline = document.getElementById("btn-format-underline");
    if (btnUnderline) btnUnderline.addEventListener("click", () => formatRichText("underline"));

    const btnUl = document.getElementById("btn-format-ul");
    if (btnUl) btnUl.addEventListener("click", () => formatRichText("insertUnorderedList"));

    const btnOl = document.getElementById("btn-format-ol");
    if (btnOl) btnOl.addEventListener("click", () => formatRichText("insertOrderedList"));

    const btnClear = document.getElementById("btn-format-clear");
    if (btnClear) btnClear.addEventListener("click", () => formatRichText("removeFormat"));

    // 2. Delegação de eventos no editor rich text
    if (editorQStatementRich) {
      editorQStatementRich.addEventListener("input", () => {
        saveCurrentEditorState();
        updateRealtimeQuestionPreview();
        markUnsaved();
      });
    }
  }

  function formatRichText(cmd) {
    if (!editorQStatementRich) return;
    editorQStatementRich.focus();
    document.execCommand(cmd, false, null);
    editorQStatementRich.dispatchEvent(new Event("input", { bubbles: true }));
  }

  function insertTextOrSymbolAtCaret(text) {
    if (!editorQStatementRich) return;
    editorQStatementRich.focus();
    document.execCommand("insertText", false, text);
    editorQStatementRich.dispatchEvent(new Event("input", { bubbles: true }));
  }

  function insertWordTable() {
    if (!editorQStatementRich) return;
    editorQStatementRich.focus();
    const tableHtml = `
      <table class="exam-data-table" contenteditable="true" style="margin: 8px 0; border-collapse: collapse; border: 1px solid #cbd5e1; font-size: 0.9rem;">
        <thead>
          <tr style="background-color: #f1f5f9;">
            <th style="border: 1px solid #cbd5e1; padding: 6px 12px; font-weight: bold;">Item</th>
            <th style="border: 1px solid #cbd5e1; padding: 6px 12px; font-weight: bold;">Descrição</th>
            <th style="border: 1px solid #cbd5e1; padding: 6px 12px; font-weight: bold;">Valor</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style="border: 1px solid #cbd5e1; padding: 6px 12px;">1</td>
            <td style="border: 1px solid #cbd5e1; padding: 6px 12px;">Dado A</td>
            <td style="border: 1px solid #cbd5e1; padding: 6px 12px;">10</td>
          </tr>
          <tr>
            <td style="border: 1px solid #cbd5e1; padding: 6px 12px;">2</td>
            <td style="border: 1px solid #cbd5e1; padding: 6px 12px;">Dado B</td>
            <td style="border: 1px solid #cbd5e1; padding: 6px 12px;">20</td>
          </tr>
        </tbody>
      </table><p><br></p>
    `;
    document.execCommand("insertHTML", false, tableHtml);
    editorQStatementRich.dispatchEvent(new Event("input", { bubbles: true }));
  }

  // ==========================================================================
  // Modal de Edição Matemática Visual (Estilo MathType / Word Equation)
  // Baseado na arquitetura visual do Math-Editor / MathLive
  // ==========================================================================
  function registerMathLiveMacros() {
    const customMacros = {};
    if (window.MathfieldElement) {
      try {
        window.MathfieldElement.macros = Object.assign({}, window.MathfieldElement.macros || {}, customMacros);
      } catch (e) { }
    }
    if (visualMathField) {
      try {
        visualMathField.macros = Object.assign({}, visualMathField.macros || {}, customMacros);
      } catch (e) { }
    }
  }

  function setupVisualMathModal() {
    if (!modalMathEditor) modalMathEditor = document.getElementById("modal-math-editor");
    if (!visualMathField) visualMathField = document.getElementById("visual-math-field");
    if (!modalMathLivePreview) modalMathLivePreview = document.getElementById("modal-math-live-preview");
    if (!modalSymbolsBar) modalSymbolsBar = document.getElementById("modal-symbols-bar");
    if (!btnCloseMathModal) btnCloseMathModal = document.getElementById("btn-close-math-modal");
    if (!btnCancelMathModal) btnCancelMathModal = document.getElementById("btn-cancel-math-modal");
    if (!btnConfirmInsertMath) btnConfirmInsertMath = document.getElementById("btn-confirm-insert-math");
    if (!btnMathClearField) btnMathClearField = document.getElementById("btn-math-clear-field");
    if (!btnOpenMathVisualModal) btnOpenMathVisualModal = document.getElementById("btn-open-math-visual-modal");

    if (!modalMathEditor) return;
    registerMathLiveMacros();

    // 1. Preenche a barra de símbolos rápidos do modal
    if (modalSymbolsBar) {
      modalSymbolsBar.innerHTML = "";
      const QUICK_MODAL_SYMBOLS = [
        '±', '×', '÷', '≤', '≥', '≠', '≈', 'π', '°', 'Δ', 'α', 'β', 'θ', 'λ', 'μ', 'Ω', '∞', '→', '²', '³', '√', '∈', '∑', '∫'
      ];
      QUICK_MODAL_SYMBOLS.forEach(sym => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "px-2.5 py-1 rounded bg-white hover:bg-blue-50 hover:text-blue-600 text-xs font-bold border border-slate-200 transition-colors shrink-0 text-slate-800 shadow-2xs";
        btn.textContent = sym;
        btn.title = `Inserir ${sym}`;
        btn.addEventListener("mousedown", (e) => e.preventDefault());
        btn.addEventListener("click", (e) => {
          e.preventDefault();
          insertIntoMathField(sym);
        });
        modalSymbolsBar.appendChild(btn);
      });
    }

    // 2. Botões de Estruturas Matemáticas dentro do Modal
    document.querySelectorAll(".btn-math-insert-struct").forEach(btn => {
      btn.addEventListener("mousedown", (e) => e.preventDefault());
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        const cmd = btn.getAttribute("data-cmd");

        if (cmd === "frac") {
          insertIntoMathField("\\frac{a}{b}");
        } else if (cmd === "sqrt") {
          insertIntoMathField("\\sqrt{x}");
        } else if (cmd === "sqrtn") {
          insertIntoMathField("\\sqrt[n]{x}");
        } else if (cmd === "pow") {
          insertIntoMathField("x^{2}");
        } else if (cmd === "sub") {
          insertIntoMathField("x_{1}");
        }
      });
    });

    // 3. Atualização contínua da prévia do modal conforme digitação visual
    if (visualMathField) {
      visualMathField.addEventListener("input", () => {
        const val = (typeof visualMathField.getValue === "function" ? visualMathField.getValue() : visualMathField.value) || "";
        updateModalMathPreview(val);
      });
    }

    // 4. Limpar Campo
    if (btnMathClearField) {
      btnMathClearField.addEventListener("click", () => {
        if (!visualMathField) visualMathField = document.getElementById("visual-math-field");
        if (visualMathField) {
          if (typeof visualMathField.setValue === "function") {
            visualMathField.setValue("");
          } else {
            visualMathField.value = "";
          }
          updateModalMathPreview("");
          try { visualMathField.focus(); } catch (e) { }
        }
      });
    }

    // 6. Fechar / Cancelar
    if (btnCloseMathModal) btnCloseMathModal.addEventListener("click", closeVisualMathModal);
    if (btnCancelMathModal) btnCancelMathModal.addEventListener("click", closeVisualMathModal);
    if (modalMathEditor) {
      modalMathEditor.addEventListener("click", (e) => {
        if (e.target === modalMathEditor) closeVisualMathModal();
      });
    }

    // 7. Confirmar Inserção
    if (btnConfirmInsertMath) {
      btnConfirmInsertMath.addEventListener("click", confirmMathModalInsertion);
    }

    // 8. Botão da Ribbon "Abrir Editor Visual (MathType)"
    if (btnOpenMathVisualModal) {
      btnOpenMathVisualModal.addEventListener("click", () => {
        openVisualMathModal("", { type: "statement" });
      });
    }
  }

  function insertIntoMathField(latex) {
    if (!visualMathField) visualMathField = document.getElementById("visual-math-field");
    if (!visualMathField) return;
    registerMathLiveMacros();

    let inserted = false;
    if (typeof visualMathField.insert === "function") {
      try {
        visualMathField.insert(latex, { selectionMode: "placeholder", focus: true });
        inserted = true;
      } catch (err) {
        console.warn("MathLive.insert com placeholder falhou:", err);
        try {
          visualMathField.insert(latex);
          inserted = true;
        } catch (err2) {
          console.warn("MathLive.insert simples falhou:", err2);
        }
      }
    }

    if (!inserted) {
      try {
        const cur = (typeof visualMathField.getValue === "function" ? visualMathField.getValue() : visualMathField.value) || "";
        const nextVal = cur ? `${cur} ${latex}` : latex;
        if (typeof visualMathField.setValue === "function") {
          visualMathField.setValue(nextVal, { mode: "math" });
        } else {
          visualMathField.value = nextVal;
        }
      } catch (err) {
        visualMathField.value = (visualMathField.value ? visualMathField.value + " " : "") + latex;
      }
    }

    try {
      visualMathField.focus();
    } catch (e) { }

    const curVal = (typeof visualMathField.getValue === "function" ? visualMathField.getValue() : visualMathField.value) || "";
    updateModalMathPreview(curVal);
  }

  function updateModalMathPreview(latex) {
    if (!modalMathLivePreview) modalMathLivePreview = document.getElementById("modal-math-live-preview");
    if (!modalMathLivePreview) return;
    if (!latex || !latex.trim()) {
      modalMathLivePreview.innerHTML = `<span class="text-xs text-slate-400 italic">Digite acima para ver a prévia fiel em tempo real</span>`;
      return;
    }

    if (window.katex) {
      try {
        window.katex.render(latex, modalMathLivePreview, {
          throwOnError: false,
          displayMode: true,
          macros: KATEX_MACROS
        });
      } catch (err) {
        modalMathLivePreview.textContent = latex;
      }
    } else {
      modalMathLivePreview.textContent = latex;
    }
  }

  function openVisualMathModal(initialLatex = "", target = { type: "statement" }) {
    if (!modalMathEditor) return;
    registerMathLiveMacros();

    // Salva a seleção atual do editor se estiver focada
    const sel = window.getSelection();
    if (sel && sel.rangeCount > 0 && editorQStatementRich && editorQStatementRich.contains(sel.getRangeAt(0).commonAncestorContainer)) {
      target.savedRange = sel.getRangeAt(0).cloneRange();
    }

    currentMathTarget = target;
    const latexToSet = initialLatex || "";

    if (visualMathField) {
      visualMathField.value = latexToSet;
    }
    updateModalMathPreview(latexToSet);

    modalMathEditor.classList.add("active");
    setTimeout(() => {
      if (visualMathField) {
        visualMathField.focus();
      }
    }, 80);
  }

  function closeVisualMathModal() {
    if (modalMathEditor) modalMathEditor.classList.remove("active");
    currentMathTarget = null;
  }

  function confirmMathModalInsertion() {
    if (!visualMathField) visualMathField = document.getElementById("visual-math-field");
    if (!visualMathField) return;
    const latex = (
      (typeof visualMathField.getValue === "function" ? visualMathField.getValue() : visualMathField.value) || ""
    ).trim();

    if (!latex) {
      showToast("Nenhuma fórmula digitada.", "warning");
      closeVisualMathModal();
      return;
    }

    if (!currentMathTarget) {
      currentMathTarget = { type: "statement" };
    }

    if (currentMathTarget) {
      if (currentMathTarget.type === "statement") {
        if (currentMathTarget.chipEl) {
          // Atualiza chip existente
          currentMathTarget.chipEl.setAttribute("data-latex", latex);
          const rendered = currentMathTarget.chipEl.querySelector(".chip-rendered");
          if (rendered && window.katex) {
            try {
              window.katex.render(latex, rendered, {
                throwOnError: false,
                displayMode: currentMathTarget.isDisplay || false
              });
            } catch (e) {
              rendered.textContent = latex;
            }
          }
          if (editorQStatementRich) {
            editorQStatementRich.dispatchEvent(new Event("input", { bubbles: true }));
          }
        } else {
          // Cria novo chip visual e insere no texto
          const chip = createMathChipElement(latex, currentMathTarget.isDisplay || false);
          insertMathChipIntoStatement(chip, currentMathTarget.savedRange);
        }
      } else if (currentMathTarget.type === "alternative") {
        const q = questions[activeQuestionIndex];
        if (q && q.alternatives && q.alternatives[currentMathTarget.altIndex] !== undefined) {
          const alt = q.alternatives[currentMathTarget.altIndex];
          alt.text = (alt.text ? alt.text + " " : "") + `$${latex}$`;
          renderEditorAlternatives(q);
          markUnsaved();
        }
      }
    }

    closeVisualMathModal();
    saveCurrentEditorState();
    updateRealtimeQuestionPreview();
    markUnsaved();
    showToast("Fórmula matemática inserida visualmente!", "success");
  }

  // ==========================================================================
  // Chips de Equações Matemáticas (100% Visual, Sem Código)
  // ==========================================================================
  function createMathChipElement(latex, isDisplay = false) {
    const chip = document.createElement("span");
    chip.className = "math-eq-chip";
    chip.contentEditable = "false";
    chip.setAttribute("data-latex", latex);
    chip.setAttribute("data-display", isDisplay ? "true" : "false");
    chip.title = "Fórmula Matemática (Clique duas vezes ou no lápis para editar no MathType)";

    const rendered = document.createElement("span");
    rendered.className = "chip-rendered";

    if (window.katex) {
      try {
        window.katex.render(latex, rendered, {
          throwOnError: false,
          displayMode: isDisplay,
          macros: KATEX_MACROS
        });
      } catch (err) {
        rendered.textContent = latex;
      }
    } else {
      rendered.textContent = latex;
    }

    const actions = document.createElement("span");
    actions.className = "chip-actions";
    actions.innerHTML = `
      <button type="button" class="chip-action-btn chip-edit-btn" title="Editar Fórmula no Editor Visual (MathType)">✎</button>
      <button type="button" class="chip-action-btn chip-del-btn" title="Remover Fórmula">✕</button>
    `;

    // Ações de clique
    chip.addEventListener("click", (e) => {
      if (e.target.closest(".chip-del-btn")) {
        e.stopPropagation();
        chip.remove();
        if (editorQStatementRich) {
          editorQStatementRich.dispatchEvent(new Event("input", { bubbles: true }));
        }
        return;
      }
      e.stopPropagation();
      openVisualMathModal(chip.getAttribute("data-latex") || "", {
        type: "statement",
        chipEl: chip,
        isDisplay: chip.getAttribute("data-display") === "true"
      });
    });

    chip.appendChild(rendered);
    chip.appendChild(actions);
    return chip;
  }

  function insertMathChipIntoStatement(chip, savedRange) {
    if (!editorQStatementRich) return;
    editorQStatementRich.focus();

    let range = savedRange;
    if (!range) {
      const sel = window.getSelection();
      if (sel && sel.rangeCount > 0 && editorQStatementRich.contains(sel.getRangeAt(0).commonAncestorContainer)) {
        range = sel.getRangeAt(0);
      }
    }

    if (range && editorQStatementRich.contains(range.commonAncestorContainer)) {
      range.deleteContents();
      range.insertNode(chip);
      // Insere espaço após o chip para permitir continuar digitando texto normal
      const spaceNode = document.createTextNode(" ");
      if (chip.nextSibling) {
        chip.parentNode.insertBefore(spaceNode, chip.nextSibling);
      } else {
        chip.parentNode.appendChild(spaceNode);
      }
      const newRange = document.createRange();
      newRange.setStartAfter(spaceNode);
      newRange.collapse(true);
      const sel = window.getSelection();
      sel.removeAllRanges();
      sel.addRange(newRange);
    } else {
      editorQStatementRich.appendChild(chip);
      editorQStatementRich.appendChild(document.createTextNode(" "));
    }

    editorQStatementRich.dispatchEvent(new Event("input", { bubbles: true }));
  }

  // ==========================================================================
  // Sistema de Imagens (Enunciado e Alternativas com Tamanho e Alinhamento)
  // ==========================================================================
  function setupImageSystem() {
    // 1. Botão no cabeçalho do Enunciado
    if (btnOpenImgStatementHeader) {
      btnOpenImgStatementHeader.addEventListener("click", () => {
        openImageConfigModal({ type: "statement" });
      });
    }

    // 2. Botão na Barra de Ferramentas (Ribbon) do Enunciado
    if (btnInsertImageStatement) {
      btnInsertImageStatement.addEventListener("click", () => {
        openImageConfigModal({ type: "statement" });
      });
    }

    // 3. Fechar Modal de Imagem
    if (btnCloseImgModal) btnCloseImgModal.addEventListener("click", closeImageConfigModal);
    if (btnCancelImgModal) btnCancelImgModal.addEventListener("click", closeImageConfigModal);

    // 4. Upload de Imagem do Computador
    if (modalImgFileInput) {
      modalImgFileInput.addEventListener("change", async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);

        try {
          showToast("Enviando imagem...", "info");
          const res = await apiFetch("/api/exam-builder/upload-image", { method: "POST", body: formData });
          if (res.ok) {
            const data = await res.json();
            currentSelectedImgUrl = data.url;
            if (modalImgUrlInput) modalImgUrlInput.value = data.url;
            updateModalImagePreview(data.url);
            showToast("Imagem carregada com sucesso!", "success");
          } else {
            showToast("Falha ao enviar imagem.", "error");
          }
        } catch (err) {
          showToast("Erro de rede no upload da imagem.", "error");
        }
      });
    }

    // 5. Input de URL manual
    if (modalImgUrlInput) {
      modalImgUrlInput.addEventListener("input", (e) => {
        const url = e.target.value.trim();
        currentSelectedImgUrl = url;
        updateModalImagePreview(url);
      });
    }

    // 6. Botões de Alinhamento no Modal
    document.querySelectorAll(".btn-modal-img-align").forEach(btn => {
      btn.addEventListener("click", () => {
        const align = btn.getAttribute("data-align");
        currentSelectedImgAlign = align;
        document.querySelectorAll(".btn-modal-img-align").forEach(b => {
          const isActive = (b === btn);
          b.className = isActive
            ? "btn-press btn-modal-img-align active flex items-center justify-center gap-1.5 py-2 px-2.5 rounded-xl border border-blue-600 text-xs font-bold text-white bg-blue-600 shadow-2xs transition-all"
            : "btn-press btn-modal-img-align flex items-center justify-center gap-1.5 py-2 px-2.5 rounded-xl border border-slate-200 text-xs font-bold text-slate-700 bg-white hover:bg-slate-50 transition-all";
        });
      });
    });

    // 7. Presets de Tamanho no Modal (P, M, G, 100%)
    document.querySelectorAll(".btn-modal-img-preset").forEach(btn => {
      btn.addEventListener("click", () => {
        const size = btn.getAttribute("data-size");
        setImageModalWidth(size);
        document.querySelectorAll(".btn-modal-img-preset").forEach(b => {
          const isActive = (b === btn);
          b.className = isActive
            ? "btn-press btn-modal-img-preset active py-1.5 px-2 rounded-lg border border-blue-600 text-xs font-bold text-white bg-blue-600 shadow-2xs transition-all text-center"
            : "btn-press btn-modal-img-preset py-1.5 px-2 rounded-lg border border-slate-200 text-xs font-bold text-slate-700 bg-white hover:bg-slate-50 transition-all text-center";
        });
      });
    });

    // 8. Slider de Largura
    if (modalImgWidthSlider) {
      modalImgWidthSlider.addEventListener("input", (e) => {
        const width = `${e.target.value}px`;
        setImageModalWidth(width, false);
      });
    }

    // 9. Confirmar Inserção
    if (btnConfirmImgModal) {
      btnConfirmImgModal.addEventListener("click", confirmImageModalAction);
    }

    // 10. Remover Imagem (se já existente)
    if (btnModalImgRemove) {
      btnModalImgRemove.addEventListener("click", removeImageFromTarget);
    }
  }

  function setImageModalWidth(widthStr, updateSlider = true) {
    currentSelectedImgWidth = widthStr;
    if (modalImgSizeLabel) modalImgSizeLabel.textContent = widthStr;
    if (modalImgDimensionsInfo) modalImgDimensionsInfo.textContent = `Largura: ${widthStr}`;
    if (modalImgPreviewTag) modalImgPreviewTag.style.width = widthStr === "100%" ? "100%" : widthStr;

    if (updateSlider && modalImgWidthSlider && widthStr.endsWith("px")) {
      const num = parseInt(widthStr, 10);
      if (!isNaN(num)) modalImgWidthSlider.value = num;
    }
  }

  function updateModalImagePreview(url) {
    if (!url || !url.trim()) {
      if (modalImgPreviewBox) modalImgPreviewBox.classList.add("hidden");
      if (modalImgPreviewTag) modalImgPreviewTag.src = "";
      return;
    }
    if (modalImgPreviewTag) {
      modalImgPreviewTag.src = url;
      modalImgPreviewTag.style.width = currentSelectedImgWidth === "100%" ? "100%" : currentSelectedImgWidth;
    }
    if (modalImgPreviewBox) modalImgPreviewBox.classList.remove("hidden");
  }

  function openImageConfigModal(target = { type: "statement" }) {
    if (!modalImageConfig) return;

    // Salva seleção no editor se aplicável
    const sel = window.getSelection();
    if (sel && sel.rangeCount > 0 && editorQStatementRich && editorQStatementRich.contains(sel.getRangeAt(0).commonAncestorContainer)) {
      target.savedRange = sel.getRangeAt(0).cloneRange();
    }

    currentImageTarget = target;
    const isEdit = Boolean(target.existingChip || (target.type === "alternative" && target.url));
    const url = target.url || "";
    const align = target.align || "center";
    const width = target.width || "220px";

    currentSelectedImgUrl = url;
    currentSelectedImgAlign = align;
    currentSelectedImgWidth = width;

    if (modalImgTitle) {
      modalImgTitle.textContent = isEdit
        ? "Configurar Imagem"
        : (target.type === "alternative" ? `Inserir Imagem na Alternativa ${String.fromCharCode(65 + target.altIndex)}` : "Inserir Imagem na Questão");
    }

    const modalImgSubtitle = document.getElementById("modal-img-subtitle");
    if (modalImgSubtitle) {
      modalImgSubtitle.textContent = target.type === "alternative"
        ? `Defina o tamanho e alinhamento da imagem para a alternativa (${String.fromCharCode(65 + target.altIndex)})`
        : "Defina o tamanho, alinhamento e origem da ilustração";
    }

    if (btnConfirmImgModalText) {
      btnConfirmImgModalText.textContent = isEdit ? "Salvar Alterações" : "Inserir na Questão";
    }

    if (modalImgUrlInput) modalImgUrlInput.value = url;
    if (modalImgFileInput) modalImgFileInput.value = "";

    // Atualiza botões de alinhamento
    document.querySelectorAll(".btn-modal-img-align").forEach(b => {
      const isActive = (b.getAttribute("data-align") === align);
      b.className = isActive
        ? "btn-press btn-modal-img-align active flex items-center justify-center gap-1.5 py-2 px-2.5 rounded-xl border border-blue-600 text-xs font-bold text-white bg-blue-600 shadow-2xs transition-all"
        : "btn-press btn-modal-img-align flex items-center justify-center gap-1.5 py-2 px-2.5 rounded-xl border border-slate-200 text-xs font-bold text-slate-700 bg-white hover:bg-slate-50 transition-all";
    });

    // Atualiza botões de tamanho
    setImageModalWidth(width, true);
    document.querySelectorAll(".btn-modal-img-preset").forEach(b => {
      const isActive = (b.getAttribute("data-size") === width);
      b.className = isActive
        ? "btn-press btn-modal-img-preset active py-1.5 px-2 rounded-lg border border-blue-600 text-xs font-bold text-white bg-blue-600 shadow-2xs transition-all text-center"
        : "btn-press btn-modal-img-preset py-1.5 px-2 rounded-lg border border-slate-200 text-xs font-bold text-slate-700 bg-white hover:bg-slate-50 transition-all text-center";
    });

    updateModalImagePreview(url);

    if (btnModalImgRemove) {
      if (isEdit) btnModalImgRemove.classList.remove("hidden");
      else btnModalImgRemove.classList.add("hidden");
    }

    modalImageConfig.classList.add("active");
  }

  function closeImageConfigModal() {
    if (modalImageConfig) modalImageConfig.classList.remove("active");
    currentImageTarget = null;
  }

  function confirmImageModalAction() {
    if (!currentSelectedImgUrl || !currentSelectedImgUrl.trim()) {
      showToast("Por favor, selecione um arquivo ou informe a URL da imagem.", "warning");
      return;
    }

    const url = currentSelectedImgUrl.trim();
    const align = currentSelectedImgAlign || "center";
    const width = currentSelectedImgWidth || "220px";

    if (!currentImageTarget) {
      closeImageConfigModal();
      return;
    }

    if (currentImageTarget.type === "statement") {
      if (currentImageTarget.existingChip) {
        // Atualiza chip existente
        const chip = currentImageTarget.existingChip;
        chip.className = `exam-img-chip align-${align}`;
        chip.setAttribute("data-src", url);
        chip.setAttribute("data-align", align);
        chip.setAttribute("data-width", width);
        const img = chip.querySelector("img");
        if (img) {
          img.src = url;
          img.style.width = width;
        }
        chip.querySelectorAll(".btn-img-align").forEach(b => b.classList.toggle("active", b.getAttribute("data-align") === align));
        chip.querySelectorAll(".btn-img-size").forEach(b => b.classList.toggle("active", b.getAttribute("data-size") === width));
      } else {
        // Cria novo chip interativo
        const newChip = createImageChipElement(url, align, width);
        insertImageChipIntoStatement(newChip, currentImageTarget.savedRange);
      }
      if (editorQStatementRich) editorQStatementRich.dispatchEvent(new Event("input", { bubbles: true }));
      showToast("Imagem inserida no enunciado!", "success");
    } else if (currentImageTarget.type === "alternative") {
      const q = questions[activeQuestionIndex];
      const altIdx = currentImageTarget.altIndex;
      if (q && q.alternatives && q.alternatives[altIdx]) {
        q.alternatives[altIdx].image = { url, align, width };
        q.alternatives[altIdx].image_url = url;
        q.alternatives[altIdx].image_width = width;
        q.alternatives[altIdx].image_align = align;
        renderEditorAlternatives(q);
        updateRealtimeQuestionPreview();
        updateLiveSheetPreview();
        markUnsaved();
        showToast(`Imagem inserida na Alternativa ${String.fromCharCode(65 + altIdx)}!`, "success");
      }
    }

    closeImageConfigModal();
  }

  function removeImageFromTarget() {
    if (!currentImageTarget) return;

    if (currentImageTarget.type === "statement" && currentImageTarget.existingChip) {
      currentImageTarget.existingChip.remove();
      if (editorQStatementRich) editorQStatementRich.dispatchEvent(new Event("input", { bubbles: true }));
      showToast("Imagem removida do enunciado.", "info");
    } else if (currentImageTarget.type === "alternative") {
      const q = questions[activeQuestionIndex];
      const altIdx = currentImageTarget.altIndex;
      if (q && q.alternatives && q.alternatives[altIdx]) {
        delete q.alternatives[altIdx].image;
        delete q.alternatives[altIdx].image_url;
        delete q.alternatives[altIdx].image_width;
        delete q.alternatives[altIdx].image_align;
        renderEditorAlternatives(q);
        updateRealtimeQuestionPreview();
        updateLiveSheetPreview();
        markUnsaved();
        showToast("Imagem removida da alternativa.", "info");
      }
    }

    closeImageConfigModal();
  }

  // ==========================================================================
  // Chips de Imagens Interativas (com Alinhamento e Redimensionamento)
  // ==========================================================================
  function createImageChipElement(url, align = "center", width = "220px") {
    const chip = document.createElement("figure");
    chip.className = `exam-img-chip align-${align}`;
    chip.contentEditable = "false";
    chip.setAttribute("data-src", url);
    chip.setAttribute("data-align", align);
    chip.setAttribute("data-width", width);
    chip.title = "Clique para alterar alinhamento ou tamanho da imagem";

    const inner = document.createElement("div");
    inner.className = "exam-img-inner";

    const img = document.createElement("img");
    img.src = url;
    img.alt = "Ilustração da Questão";
    img.style.width = width;
    img.style.maxWidth = "100%";

    const controls = document.createElement("div");
    controls.className = "exam-img-controls-bar";
    controls.innerHTML = `
      <button type="button" class="btn-img-align ${align === 'left' ? 'active' : ''}" data-align="left" title="Alinhar à Esquerda (texto ao redor)">
        <span class="material-symbols-outlined text-[15px]">format_align_left</span>
      </button>
      <button type="button" class="btn-img-align ${align === 'center' ? 'active' : ''}" data-align="center" title="Centralizado">
        <span class="material-symbols-outlined text-[15px]">format_align_center</span>
      </button>
      <button type="button" class="btn-img-align ${align === 'right' ? 'active' : ''}" data-align="right" title="Alinhar à Direita (texto ao redor)">
        <span class="material-symbols-outlined text-[15px]">format_align_right</span>
      </button>
      <span class="bar-divider"></span>
      <button type="button" class="btn-img-size ${width === '120px' ? 'active' : ''}" data-size="120px" title="Pequeno (120px)">P</button>
      <button type="button" class="btn-img-size ${width === '220px' ? 'active' : ''}" data-size="220px" title="Médio (220px)">M</button>
      <button type="button" class="btn-img-size ${width === '360px' ? 'active' : ''}" data-size="360px" title="Grande (360px)">G</button>
      <button type="button" class="btn-img-size ${width === '100%' ? 'active' : ''}" data-size="100%" title="Largura Total">100%</button>
      <span class="bar-divider"></span>
      <button type="button" class="btn-img-edit" title="Abrir Configurações da Imagem">
        <span class="material-symbols-outlined text-[15px]">tune</span>
      </button>
      <button type="button" class="btn-img-delete" title="Remover Imagem">
        <span class="material-symbols-outlined text-[15px]">delete</span>
      </button>
    `;

    // Previne que cliques nos controles roubem o foco ou interfiram no contenteditable
    controls.addEventListener("mousedown", (e) => {
      e.preventDefault();
      e.stopPropagation();
    });

    // Eventos da barra rápida
    controls.querySelectorAll(".btn-img-align").forEach(btn => {
      btn.addEventListener("mousedown", (e) => {
        e.preventDefault();
        e.stopPropagation();
      });
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        const newAlign = btn.getAttribute("data-align");
        chip.className = `exam-img-chip align-${newAlign}`;
        chip.setAttribute("data-align", newAlign);
        controls.querySelectorAll(".btn-img-align").forEach(b => b.classList.toggle("active", b === btn));
        if (editorQStatementRich) editorQStatementRich.dispatchEvent(new Event("input", { bubbles: true }));
        saveCurrentEditorState();
        updateRealtimeQuestionPreview();
        markUnsaved();
      });
    });

    controls.querySelectorAll(".btn-img-size").forEach(btn => {
      btn.addEventListener("mousedown", (e) => {
        e.preventDefault();
        e.stopPropagation();
      });
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        const newSize = btn.getAttribute("data-size");
        img.style.width = newSize;
        chip.setAttribute("data-width", newSize);
        controls.querySelectorAll(".btn-img-size").forEach(b => b.classList.toggle("active", b === btn));
        if (editorQStatementRich) editorQStatementRich.dispatchEvent(new Event("input", { bubbles: true }));
        saveCurrentEditorState();
        updateRealtimeQuestionPreview();
        markUnsaved();
      });
    });

    const btnEdit = controls.querySelector(".btn-img-edit");
    if (btnEdit) {
      btnEdit.addEventListener("mousedown", (e) => {
        e.preventDefault();
        e.stopPropagation();
      });
      btnEdit.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        openImageConfigModal({
          type: "statement",
          existingChip: chip,
          url: chip.getAttribute("data-src"),
          align: chip.getAttribute("data-align"),
          width: chip.getAttribute("data-width")
        });
      });
    }

    const btnDel = controls.querySelector(".btn-img-delete");
    if (btnDel) {
      btnDel.addEventListener("mousedown", (e) => {
        e.preventDefault();
        e.stopPropagation();
      });
      btnDel.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        chip.remove();
        if (editorQStatementRich) editorQStatementRich.dispatchEvent(new Event("input", { bubbles: true }));
        saveCurrentEditorState();
        updateRealtimeQuestionPreview();
        markUnsaved();
      });
    }

    chip.addEventListener("click", (e) => {
      if (!e.target.closest(".exam-img-controls-bar")) {
        chip.classList.toggle("selected");
      }
    });

    inner.appendChild(img);
    inner.appendChild(controls);
    chip.appendChild(inner);
    return chip;
  }

  function insertImageChipIntoStatement(chip, savedRange) {
    if (!editorQStatementRich) return;
    editorQStatementRich.focus();

    let range = savedRange;
    if (!range) {
      const sel = window.getSelection();
      if (sel && sel.rangeCount > 0 && editorQStatementRich.contains(sel.getRangeAt(0).commonAncestorContainer)) {
        range = sel.getRangeAt(0);
      }
    }

    if (range && editorQStatementRich.contains(range.commonAncestorContainer)) {
      range.deleteContents();
      range.insertNode(chip);
      const spaceNode = document.createTextNode(" ");
      if (chip.nextSibling) {
        chip.parentNode.insertBefore(spaceNode, chip.nextSibling);
      } else {
        chip.parentNode.appendChild(spaceNode);
      }
    } else {
      editorQStatementRich.appendChild(chip);
      editorQStatementRich.appendChild(document.createTextNode(" "));
    }

    editorQStatementRich.dispatchEvent(new Event("input", { bubbles: true }));
  }

  // Transforma texto com LaTeX e Imagens em elementos visuais (o usuário NUNCA vê código)
  function deserializeWordEditor(rawHtml, container) {
    if (!container) return;
    container.innerHTML = "";
    if (!rawHtml || !rawHtml.trim()) return;

    // Regex para capturar $$...$$ (bloco), $...$ (inline) OU tags <img ...>
    const regex = /(\$\$[\s\S]+?\$\$|\$[^$\n]+?\$|<img\s+[^>]*src=["'][^"']+["'][^>]*>)/gi;
    let lastIndex = 0;
    let match;

    while ((match = regex.exec(rawHtml)) !== null) {
      const textBefore = rawHtml.substring(lastIndex, match.index);
      if (textBefore) {
        appendPlainTextToContainer(textBefore, container);
      }

      const rawMatch = match[0];
      if (rawMatch.toLowerCase().startsWith("<img")) {
        const parser = document.createElement("div");
        parser.innerHTML = rawMatch;
        const imgEl = parser.querySelector("img");
        if (imgEl) {
          const src = imgEl.getAttribute("data-src") || imgEl.getAttribute("src") || "";
          let align = imgEl.getAttribute("data-align");
          if (!align) {
            if (imgEl.classList.contains("align-left")) align = "left";
            else if (imgEl.classList.contains("align-right")) align = "right";
            else align = "center";
          }
          let width = imgEl.getAttribute("data-width") || imgEl.style.width || "220px";
          const imgChip = createImageChipElement(src, align, width);
          container.appendChild(imgChip);
        }
      } else {
        const isDisplay = rawMatch.startsWith("$$");
        const latex = isDisplay ? rawMatch.slice(2, -2).trim() : rawMatch.slice(1, -1).trim();
        const chip = createMathChipElement(latex, isDisplay);
        container.appendChild(chip);
      }

      lastIndex = regex.lastIndex;
    }

    const remainingText = rawHtml.substring(lastIndex);
    if (remainingText) {
      appendPlainTextToContainer(remainingText, container);
    }
  }

  function appendPlainTextToContainer(text, container) {
    const lines = text.split("\n");
    lines.forEach((line, i) => {
      if (i > 0) {
        container.appendChild(document.createElement("br"));
      }
      if (line) {
        container.appendChild(document.createTextNode(line));
      }
    });
  }

  // Serializa os elementos do editor rich text de volta para LaTeX e tags HTML padrão
  function serializeWordEditor(container) {
    if (!container) return "";
    let result = "";

    function traverse(node) {
      if (node.nodeType === Node.TEXT_NODE) {
        result += node.textContent;
      } else if (node.nodeType === Node.ELEMENT_NODE) {
        if (node.classList.contains("math-eq-chip")) {
          const latex = node.getAttribute("data-latex") || "";
          const isDisplay = node.getAttribute("data-display") === "true";
          result += isDisplay ? `$$${latex}$$` : `$${latex}$`;
        } else if (node.classList.contains("exam-img-chip") || node.tagName === "FIGURE") {
          const src = node.getAttribute("data-src") || (node.querySelector("img") ? node.querySelector("img").src : "");
          const align = node.getAttribute("data-align") || "center";
          const width = node.getAttribute("data-width") || "220px";
          if (src) {
            result += `\n<img src="${src}" class="exam-img-figure align-${align}" style="width: ${width};" data-src="${src}" data-align="${align}" data-width="${width}" />\n`;
          }
        } else if (node.tagName === "IMG" && !node.closest(".exam-img-chip")) {
          const src = node.src;
          const align = node.getAttribute("data-align") || "center";
          const width = node.getAttribute("data-width") || node.style.width || "220px";
          result += `\n<img src="${src}" class="exam-img-figure align-${align}" style="width: ${width};" data-src="${src}" data-align="${align}" data-width="${width}" />\n`;
        } else if (node.tagName === "BR") {
          result += "\n";
        } else if (node.tagName === "P" || node.tagName === "DIV") {
          if (result && !result.endsWith("\n")) result += "\n";
          node.childNodes.forEach(traverse);
          if (!result.endsWith("\n")) result += "\n";
        } else if (node.tagName === "TABLE") {
          result += "\n" + node.outerHTML + "\n";
        } else {
          node.childNodes.forEach(traverse);
        }
      }
    }

    container.childNodes.forEach(traverse);
    return result.trim();
  }

  function formatStatementPreview(text) {
    if (!text) return "";
    const div = document.createElement("div");
    div.innerHTML = text;
    div.querySelectorAll("script, iframe, object, embed").forEach(el => el.remove());
    return div.innerHTML;
  }

  // ==========================================================================
  // Atualização em Tempo Real da Prévia Oficial da Questão (A4)
  // ==========================================================================
  function updateRealtimeQuestionPreview() {
    if (!editorRealtimePreview) return;
    const q = questions[activeQuestionIndex];
    if (!q) {
      editorRealtimePreview.innerHTML = `<span class="text-slate-400 italic text-xs">Nenhuma questão selecionada</span>`;
      return;
    }

    const statementText = editorQStatementRich ? serializeWordEditor(editorQStatementRich) : (q.statement || "");
    const numFormatted = String(q.question_number || (activeQuestionIndex + 1)).padStart(2, "0");

    let altsHtml = "";
    if (q.type === "4" || q.type === "5") {
      altsHtml = `
        <div class="mt-2.5 flex flex-col gap-1.5 pl-2 border-l-2 border-slate-200">
          ${(q.alternatives || []).map((a, idx) => {
        const letter = a.letter || String.fromCharCode(65 + idx);
        const isCorrect = Boolean(a.is_correct);
        const altImg = a.image || (a.image_url ? { url: a.image_url } : null);
        let altImgHtml = "";
        if (altImg && altImg.url) {
          const align = altImg.align || "left";
          const width = altImg.width || "180px";
          altImgHtml = `<div class="alt-img-display align-${align}" style="width: ${width}; max-width: 100%; margin-top: 4px;"><img src="${escapeHtml(altImg.url)}" class="rounded shadow-2xs" style="width: 100%;" /></div>`;
        }
        return `
              <div class="flex items-start gap-2 text-xs text-slate-800 ${isCorrect ? 'font-semibold text-emerald-800' : ''}">
                <span class="font-bold text-slate-600 ${isCorrect ? 'text-emerald-700' : ''}">(${letter})</span>
                <div class="flex-1 flex flex-col">
                  <span class="preview-alt-text">${escapeHtml(a.text || "")}</span>
                  ${altImgHtml}
                </div>
                ${isCorrect ? '<span class="text-[10px] px-1.5 py-0.2 rounded bg-emerald-100 text-emerald-800 font-bold ml-1">Gabarito</span>' : ''}
              </div>
            `;
      }).join("")}
        </div>
      `;
    }

    editorRealtimePreview.innerHTML = `
      <div class="flex flex-col gap-1">
        <div class="flex items-center gap-2 mb-1">
          <span class="font-bold text-blue-700 text-xs">Questão ${numFormatted}</span>
          <span class="text-[11px] text-slate-400">• ${parseFloat(q.points || 1).toFixed(1)} pt</span>
        </div>
        <div class="preview-statement-body text-sm leading-relaxed text-slate-900 whitespace-pre-wrap">${formatStatementPreview(statementText)}</div>
        ${altsHtml}
      </div>
    `;

    // Renderiza KaTeX no cartão de prévia oficial em tempo real
    if (window.renderMathInElement) {
      renderMathInElement(editorRealtimePreview, {
        delimiters: [
          { left: "$$", right: "$$", display: true },
          { left: "$", right: "$", display: false },
          { left: "\\(", right: "\\)", display: false },
          { left: "\\[", right: "\\]", display: true }
        ],
        macros: KATEX_MACROS,
        throwOnError: false
      });
    }
  }

  function wrapSelection(textarea, before, after) {
    if (!textarea) return;
    const start = textarea.selectionStart || 0;
    const end = textarea.selectionEnd || 0;
    const text = textarea.value;
    const sel = text.substring(start, end) || "texto";
    textarea.value = text.substring(0, start) + before + sel + after + text.substring(end);
    textarea.selectionStart = start + before.length;
    textarea.selectionEnd = start + before.length + sel.length;
    textarea.dispatchEvent(new Event("input"));
    textarea.focus();
  }

  function insertAtCursor(textarea, snippet) {
    if (!textarea) return;
    const start = textarea.selectionStart || 0;
    const end = textarea.selectionEnd || 0;
    const text = textarea.value;
    textarea.value = text.substring(0, start) + snippet + text.substring(end);
    textarea.selectionStart = textarea.selectionEnd = start + snippet.length;
    textarea.dispatchEvent(new Event("input"));
    textarea.focus();
  }

  // ==========================================================================
  // Montagem do Payload para API
  // ==========================================================================
  function buildExamPayload() {
    saveCurrentEditorState();
    return {
      title: examTitleInput.value.trim() || "AVALIAÇÃO BIMESTRAL",
      institution: cfgInstitution.value.trim(),
      school_name: cfgSchool.value.trim(),
      discipline: cfgDiscipline.value.trim(),
      teacher_name: cfgTeacher.value.trim(),
      grade: cfgGrade.value.trim(),
      classroom: cfgClassroom.value.trim(),
      shift: cfgShift.value.trim(),
      exam_date: cfgDate.value.trim(),
      max_score: questions.reduce((sum, q) => sum + (parseFloat(q.points) || 1.0), 0) || (questions.length * 1.0) || 10.0,
      footer_text: "Boa Prova! Leia com atenção cada questão antes de assinalar a resposta.",
      columns: selectedColumns,
      include_answer_sheet: chkAnswerSheet.checked,
      header_style: (chkIncludeHeader && chkIncludeHeader.checked) ? "standard" : "title_only",
      include_header: chkIncludeHeader ? chkIncludeHeader.checked : false,
      show_answers: false,
      margin_top: parseFloat(cfgMarginTop.value) || 3.0,
      margin_bottom: parseFloat(cfgMarginBottom.value) || 2.0,
      margin_left: parseFloat(cfgMarginLeft.value) || 3.0,
      margin_right: parseFloat(cfgMarginRight.value) || 2.0,
      questions: questions.map((q, idx) => ({
        id: q.id,
        question_number: idx + 1,
        statement: q.statement,
        points: parseFloat(q.points) || 1.0,
        bncc_code: (q.bncc_code || q.skill || "").trim(),
        skill: (q.skill || q.bncc_code || "").trim(),
        difficulty: q.difficulty || "medio",
        type: q.type || String(globalExamAlternativesMode || 4),
        image_url: q.image_url || "",
        image_position: "after_statement",
        image_width: "50%",
        image_caption: "",
        alternatives: (q.alternatives || []).map((a, aIdx) => {
          const imgUrl = (a.image && a.image.url) || a.image_url || "";
          const imgWidth = (a.image && a.image.width) || a.image_width || "180px";
          const imgAlign = (a.image && a.image.align) || a.image_align || "center";
          return {
            letter: a.letter || String.fromCharCode(65 + aIdx),
            text: a.text || "",
            is_correct: Boolean(a.is_correct),
            image_url: imgUrl,
            image_width: imgWidth,
            image_align: imgAlign,
            image: imgUrl ? { url: imgUrl, width: imgWidth, align: imgAlign } : null
          };
        })
      }))
    };
  }

  // ==========================================================================
  // Salvamento no Servidor & Auto-Save Automático
  // ==========================================================================
  let autoSaveTimer = null;

  function updateNetworkStatus() {
    if (!saveStatusText) return;
    const isOnline = navigator.onLine;
    if (!isOnline) {
      saveStatusText.textContent = "Usuario offline";
      if (statusDot) {
        statusDot.className = "w-1.5 h-1.5 rounded-full bg-slate-400";
      }
      if (statusPill) {
        statusPill.className = "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-slate-200 text-slate-600 text-xs font-semibold";
      }
    } else {
      if (saveStatusText.textContent === "Usuario offline" || saveStatusText.textContent === "Usuário offline") {
        saveStatusText.textContent = "Salvo no sistema";
        if (statusDot) {
          statusDot.className = "w-1.5 h-1.5 rounded-full bg-tertiary-container animate-pulse";
        }
        if (statusPill) {
          statusPill.className = "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-surface-container-high text-on-surface-variant text-xs";
        }
        saveExamToServer({ isAuto: true });
      }
    }
  }

  // Verificação contínua a cada 1.5 segundos
  setInterval(updateNetworkStatus, 1500);

  async function saveExamToServer(options = {}) {
    const isAuto = Boolean(options.isAuto);
    if (isSaving) {
      if (isAuto) return;
      let attempts = 0;
      while (isSaving && attempts < 25) {
        await new Promise(r => setTimeout(r, 100));
        attempts++;
      }
    }

    // Salva sempre no localStorage de imediato como backup offline
    saveCurrentEditorState();
    const payload = buildExamPayload();
    try {
      localStorage.setItem("elaborador_draft_auto", JSON.stringify(payload));
    } catch (e) { }

    if (!navigator.onLine) {
      if (saveStatusText) saveStatusText.textContent = "Usuario offline";
      if (statusDot) {
        statusDot.className = "w-1.5 h-1.5 rounded-full bg-slate-400";
      }
      return;
    }

    isSaving = true;

    if (saveStatusText) {
      saveStatusText.textContent = isAuto ? "Salvando automaticamente..." : "Salvando no sistema...";
    }
    if (statusDot) {
      statusDot.classList.add("bg-amber-400");
      statusDot.classList.remove("bg-tertiary-container", "bg-slate-400");
    }

    const url = currentExamId ? `/api/exam-builder/exams/${currentExamId}` : "/api/exam-builder/exams";
    const method = currentExamId ? "PUT" : "POST";

    try {
      const res = await apiFetch(url, {
        method: method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const data = await res.json();
        if (data.id) currentExamId = data.id;
        const now = new Date();
        const timeStr = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}:${String(now.getSeconds()).padStart(2, "0")}`;
        if (saveStatusText) {
          saveStatusText.textContent = `Salvo no sistema às ${timeStr}`;
        }
        if (statusDot) {
          statusDot.classList.remove("bg-amber-400", "bg-slate-400");
          statusDot.classList.add("bg-tertiary-container", "animate-pulse");
        }
        if (!isAuto) {
          showToast("Avaliação salva com sucesso!", "success");
        }
        return currentExamId;
      } else {
        if (saveStatusText) saveStatusText.textContent = "Usuario offline";
        if (statusDot) {
          statusDot.classList.remove("bg-amber-400", "bg-tertiary-container", "animate-pulse");
          statusDot.classList.add("bg-slate-400");
        }
        if (!isAuto) {
          showToast("Erro ao sincronizar com servidor, salvo localmente.", "warning");
        }
        return null;
      }
    } catch (e) {
      if (saveStatusText) saveStatusText.textContent = "Usuario offline";
      if (statusDot) {
        statusDot.classList.remove("bg-amber-400", "bg-tertiary-container", "animate-pulse");
        statusDot.classList.add("bg-slate-400");
      }
      if (!isAuto) {
        showToast("Falha de rede ao salvar no servidor. Rascunho mantido offline.", "warning");
      }
      return null;
    } finally {
      isSaving = false;
    }
  }

  function markUnsaved() {
    if (!navigator.onLine) {
      if (saveStatusText) saveStatusText.textContent = "Usuario offline";
      if (statusDot) {
        statusDot.classList.remove("bg-amber-400", "bg-tertiary-container", "animate-pulse");
        statusDot.classList.add("bg-slate-400");
      }
    } else {
      if (saveStatusText) saveStatusText.textContent = "Alterações pendentes...";
      if (statusDot) {
        statusDot.classList.add("bg-amber-400");
        statusDot.classList.remove("bg-tertiary-container", "bg-slate-400");
      }
    }

    if (currentExamHasLinkedGabarito) {
      updateGabaritoOutdatedBanner(true);
    }

    // Salva cópia local no localStorage instantaneamente
    try {
      const snap = buildExamPayload();
      localStorage.setItem("elaborador_draft_auto", JSON.stringify(snap));
    } catch (e) { }

    // Debounce de 1.2 segundos para salvar de forma automática no servidor
    if (navigator.onLine) {
      clearTimeout(autoSaveTimer);
      autoSaveTimer = setTimeout(() => {
        saveExamToServer({ isAuto: true });
      }, 1200);
    }
  }

  function tryRestoreAutoSaveDraft() {
    try {
      const urlParams = new URLSearchParams(window.location.search);
      if (urlParams.get("exam_id")) return; // Se for edição de ID específico, mantém fluxo padrão

      const saved = localStorage.getItem("elaborador_draft_auto");
      if (saved) {
        const data = JSON.parse(saved);
        if (data && Array.isArray(data.questions) && data.questions.length > 0) {
          questions = data.questions.map((q, idx) => ({
            ...q,
            bncc_code: q.bncc_code || q.skill || "",
            skill: q.bncc_code || q.skill || "",
            points: typeof q.points === "number" ? q.points : (parseFloat(q.points) || 1.0),
            alternatives: (q.alternatives || []).map((a, aIdx) => {
              const imgObj = a.image || (a.image_url ? { url: a.image_url, width: a.image_width || '180px', align: a.image_align || 'center' } : null);
              return {
                ...a,
                letter: a.letter || String.fromCharCode(65 + aIdx),
                text: a.text || "",
                is_correct: Boolean(a.is_correct),
                image: imgObj,
                image_url: (imgObj && imgObj.url) ? imgObj.url : (a.image_url || ""),
                image_width: (imgObj && imgObj.width) ? imgObj.width : (a.image_width || "180px"),
                image_align: (imgObj && imgObj.align) ? imgObj.align : (a.image_align || "center")
              };
            })
          }));
          if (data.id) currentExamId = data.id;
          if (data.title && examTitleInput) examTitleInput.value = data.title;
          if (data.institution && cfgInstitution) cfgInstitution.value = data.institution;
          if (data.school && cfgSchool) cfgSchool.value = data.school;
          if (data.discipline && cfgDiscipline) cfgDiscipline.value = data.discipline;
          if (data.teacher && cfgTeacher) cfgTeacher.value = data.teacher;
          if (data.grade && cfgGrade) cfgGrade.value = data.grade;
          if (data.classroom && cfgClassroom) cfgClassroom.value = data.classroom;
          if (data.shift && cfgShift) cfgShift.value = data.shift;
          if (data.date && cfgDate) cfgDate.value = data.date;
          if (data.max_score && cfgMaxScore) cfgMaxScore.value = data.max_score;
          if (chkIncludeHeader) {
            const hasHdr = Boolean(data.include_header) && (data.header_style === "standard" || !data.header_style);
            chkIncludeHeader.checked = hasHdr;
            if (boxInstitutionalFields) {
              boxInstitutionalFields.classList.toggle("opacity-40", !hasHdr);
              boxInstitutionalFields.classList.toggle("pointer-events-none", !hasHdr);
            }
          }
          let mt = data.margin_top ?? data.margins?.top;
          let mb = data.margin_bottom ?? data.margins?.bottom;
          let ml = data.margin_left ?? data.margins?.left;
          let mr = data.margin_right ?? data.margins?.right;
          if (mt != null) {
            let v = parseFloat(mt);
            if (v > 4.0) v = +(v / 10).toFixed(1);
            if (cfgMarginTop) cfgMarginTop.value = v;
          }
          if (mb != null) {
            let v = parseFloat(mb);
            if (v > 4.0) v = +(v / 10).toFixed(1);
            if (cfgMarginBottom) cfgMarginBottom.value = v;
          }
          if (ml != null) {
            let v = parseFloat(ml);
            if (v > 4.0) v = +(v / 10).toFixed(1);
            if (cfgMarginLeft) cfgMarginLeft.value = v;
          }
          if (mr != null) {
            let v = parseFloat(mr);
            if (v > 4.0) v = +(v / 10).toFixed(1);
            if (cfgMarginRight) cfgMarginRight.value = v;
          }

          if (data.layout && data.layout.columns) {
            selectedColumns = data.layout.columns;
          }

          const has5 = questions.some(q => q.alternatives && q.alternatives.length >= 5);
          globalExamAlternativesMode = has5 ? 5 : 4;
          if (btnModalAlt4 && btnModalAlt5) {
            if (globalExamAlternativesMode === 4) {
              btnModalAlt4.className = "flex-1 py-1 rounded text-xs font-bold bg-primary-container text-on-primary shadow-sm transition-colors active";
              btnModalAlt5.className = "flex-1 py-1 rounded text-xs font-bold text-on-surface-variant transition-colors";
            } else {
              btnModalAlt5.className = "flex-1 py-1 rounded text-xs font-bold bg-primary-container text-on-primary shadow-sm transition-colors active";
              btnModalAlt4.className = "flex-1 py-1 rounded text-xs font-bold text-on-surface-variant transition-colors";
            }
          }
        }
      }
    } catch (e) {
      console.warn("Aviso ao carregar rascunho automático do localStorage:", e);
    }
  }

  // ==========================================================================
  // Pré-visualização da Prova
  // ==========================================================================
  async function openPreviewModal() {
    modalPreview.classList.add("active");
    refreshPreview();
  }

  async function refreshPreview() {
    const payload = buildExamPayload();
    try {
      const res = await apiFetch("/api/exam-builder/preview-html", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const html = await res.text();
        previewFrame.srcdoc = html;
      }
    } catch (err) {
      showToast("Erro ao carregar pré-visualização.", "error");
    }
  }

  // ==========================================================================
  // Emitir Prova (Modal de Escolha: PDF ou Word DOCX)
  // ==========================================================================
  let selectedEmitirFormat = "pdf";

  function openEmitirProvaModal() {
    if (modalEmitirProva) {
      modalEmitirProva.classList.add("active");
      selectEmitirFormat("pdf");
    }
  }

  function closeEmitirProvaModal() {
    if (modalEmitirProva) {
      modalEmitirProva.classList.remove("active");
    }
  }

  function selectEmitirFormat(fmt) {
    selectedEmitirFormat = fmt;
    const cardPdf = document.getElementById("card-fmt-pdf");
    const cardDocx = document.getElementById("card-fmt-docx");
    const btnConfirmText = document.getElementById("btn-confirm-emitir-text");
    const btnConfirmIcon = document.getElementById("emitir-download-icon");

    if (fmt === "pdf") {
      if (cardPdf) {
        cardPdf.classList.add("active", "border-blue-600", "bg-blue-50/60");
        cardPdf.classList.remove("border-slate-200", "bg-white");
        const radio = cardPdf.querySelector(".format-radio-icon span");
        if (radio) {
          radio.textContent = "check_circle";
          radio.className = "material-symbols-outlined text-blue-600 text-[20px]";
        }
      }
      if (cardDocx) {
        cardDocx.classList.remove("active", "border-blue-600", "bg-blue-50/60");
        cardDocx.classList.add("border-slate-200", "bg-white");
        const radio = cardDocx.querySelector(".format-radio-icon span");
        if (radio) {
          radio.textContent = "radio_button_unchecked";
          radio.className = "material-symbols-outlined text-slate-300 text-[20px]";
        }
      }
      if (btnConfirmText) btnConfirmText.textContent = "Baixar em PDF";
      if (btnConfirmIcon) btnConfirmIcon.textContent = "picture_as_pdf";
    } else {
      if (cardDocx) {
        cardDocx.classList.add("active", "border-blue-600", "bg-blue-50/60");
        cardDocx.classList.remove("border-slate-200", "bg-white");
        const radio = cardDocx.querySelector(".format-radio-icon span");
        if (radio) {
          radio.textContent = "check_circle";
          radio.className = "material-symbols-outlined text-blue-600 text-[20px]";
        }
      }
      if (cardPdf) {
        cardPdf.classList.remove("active", "border-blue-600", "bg-blue-50/60");
        cardPdf.classList.add("border-slate-200", "bg-white");
        const radio = cardPdf.querySelector(".format-radio-icon span");
        if (radio) {
          radio.textContent = "radio_button_unchecked";
          radio.className = "material-symbols-outlined text-slate-300 text-[20px]";
        }
      }
      if (btnConfirmText) btnConfirmText.textContent = "Baixar em Word (.docx)";
      if (btnConfirmIcon) btnConfirmIcon.textContent = "description";
    }
  }

  async function confirmEmitirDownload() {
    closeEmitirProvaModal();
    if (selectedEmitirFormat === "docx") {
      await downloadDocx();
    } else {
      await downloadPdf();
    }
  }

  // ==========================================================================
  // Helper Seguro de Download de Blobs (PDF / Word)
  // ==========================================================================
  function triggerFileDownload(rawBlob, defaultFilename, dispositionHeader = null, mimeType = "application/pdf") {
    let resolvedFilename = defaultFilename || "Avaliacao.pdf";

    // 1. Tenta extrair o nome do arquivo enviado pelo servidor no Content-Disposition
    if (dispositionHeader) {
      if (dispositionHeader.includes("filename*=UTF-8''")) {
        try {
          const parts = dispositionHeader.split("filename*=UTF-8''");
          if (parts[1]) {
            resolvedFilename = decodeURIComponent(parts[1].split(";")[0].replace(/['"]/g, "").trim());
          }
        } catch (e) { }
      } else if (dispositionHeader.includes('filename="')) {
        try {
          const parts = dispositionHeader.split('filename="');
          if (parts[1]) {
            resolvedFilename = parts[1].split('"')[0].trim();
          }
        } catch (e) { }
      } else if (dispositionHeader.includes('filename=')) {
        try {
          const parts = dispositionHeader.split('filename=');
          if (parts[1]) {
            resolvedFilename = parts[1].split(';')[0].replace(/['"]/g, "").trim();
          }
        } catch (e) { }
      }
    }

    // 2. Remove caracteres ilegais para nomes de arquivo
    resolvedFilename = resolvedFilename.replace(/[/\\?%*:|"<>]/g, "_").trim();

    // 3. Garante a extensão correta
    const isDocx = (mimeType.includes("word") || defaultFilename.toLowerCase().endsWith(".docx"));
    const requiredExt = isDocx ? ".docx" : ".pdf";
    if (!resolvedFilename.toLowerCase().endsWith(requiredExt)) {
      resolvedFilename += requiredExt;
    }

    // 4. Cria Blob com tipo MIME explícito
    const typedBlob = (rawBlob instanceof Blob && rawBlob.type === mimeType)
      ? rawBlob
      : new Blob([rawBlob], { type: mimeType });

    const blobUrl = window.URL.createObjectURL(typedBlob);
    const downloadLink = document.createElement("a");
    downloadLink.style.display = "none";
    downloadLink.href = blobUrl;
    downloadLink.download = resolvedFilename;

    document.body.appendChild(downloadLink);
    downloadLink.click();

    // 5. IMPORTANTE: Não revogar o ObjectURL de imediato!
    // Revogar imediatamente impede o navegador de processar o download da Blob URL,
    // fazendo com que o Chrome salve o arquivo como UUID sem extensão.
    setTimeout(() => {
      try {
        if (downloadLink.parentNode) {
          document.body.removeChild(downloadLink);
        }
        window.URL.revokeObjectURL(blobUrl);
      } catch (err) { }
    }, 15000);
  }

  // ==========================================================================
  // Baixar Word (.docx) Oficial
  // ==========================================================================
  async function downloadDocx() {
    const payload = buildExamPayload();
    showToast("Gerando documento Word (.docx) estruturado...", "info");

    try {
      const res = await apiFetch("/api/exam-builder/generate-docx", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const disposition = res.headers.get("Content-Disposition");
        const blob = await res.blob();
        const rawTitle = (examTitleInput && examTitleInput.value.trim()) || payload.title || "Avaliacao";
        const fallbackName = rawTitle.replace(/[/\\?%*:|"<>]/g, "_") + ".docx";
        triggerFileDownload(blob, fallbackName, disposition, "application/vnd.openxmlformats-officedocument.wordprocessingml.document");
        showToast("Documento Word (.docx) baixado com sucesso!", "success");
      } else {
        const err = await res.json().catch(() => ({}));
        showToast("Erro ao gerar Word: " + (err.detail || "Falha na compilação"), "error");
      }
    } catch (err) {
      showToast("Falha na conexão ao compilar arquivo Word.", "error");
    }
  }

  // ==========================================================================
  // Baixar PDF Oficial
  // ==========================================================================
  async function downloadPdf() {
    const payload = buildExamPayload();
    showToast("Gerando PDF com margens milimétricas...", "info");

    try {
      const res = await apiFetch("/api/exam-builder/generate-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const disposition = res.headers.get("Content-Disposition");
        const blob = await res.blob();
        const rawTitle = (examTitleInput && examTitleInput.value.trim()) || payload.title || "Avaliacao";
        const fallbackName = rawTitle.replace(/[/\\?%*:|"<>]/g, "_") + ".pdf";
        triggerFileDownload(blob, fallbackName, disposition, "application/pdf");
        showToast("PDF baixado com sucesso!", "success");
      } else {
        showToast("Falha na compilação do PDF.", "error");
      }
    } catch (err) {
      showToast("Erro ao conectar com gerador de PDF.", "error");
    }
  }

  // ==========================================================================
  // Modal de Gabarito Oficial OMR e Sincronização com Capas Oficiais
  // ==========================================================================
  const COVER_NAMES = {
    "opcao_4_azul_nautico_lagoa": "Opção 4: Lagoa Serena & Náutico Real",
    "opcao_1_montanhas_canoa": "Opção 1: Montanhas de Canoa",
    "opcao_2_rio_verde_petroleo": "Opção 2: Rio São Francisco",
    "opcao_3_por_do_sol_solar": "Opção 3: Pôr do Sol Solar"
  };

  function updateCoverRadiosVisual() {
    const selected = document.querySelector('input[name="sync_cover_model"]:checked')?.value;
    document.querySelectorAll('.cover-card-label').forEach(card => {
      const radio = card.querySelector('input[name="sync_cover_model"]');
      if (radio && radio.value === selected) {
        card.classList.add('border-emerald-500', 'bg-emerald-50/40', 'ring-2', 'ring-emerald-500/20');
        card.classList.remove('border-slate-200', 'bg-white');
      } else {
        card.classList.remove('border-emerald-500', 'bg-emerald-50/40', 'ring-2', 'ring-emerald-500/20');
        card.classList.add('border-slate-200', 'bg-white');
      }
    });
  }

  function normalizeShift(val) {
    if (!val) return "MANHÃ";
    const s = String(val).trim().toUpperCase();
    if (s.includes("MAT") || s.includes("MANH")) return "MANHÃ";
    if (s.includes("VESP") || s.includes("TARD")) return "TARDE";
    if (s.includes("NOT") || s.includes("NOIT")) return "NOITE";
    if (s.includes("INTEG")) return "INTEGRAL";
    return "MANHÃ";
  }

  async function openSyncGabaritoModal() {
    saveCurrentEditorState();

    if (!questions || questions.length === 0) {
      showToast("Adicione ao menos uma questão à prova antes de gerar o gabarito oficial.", "warning");
      return;
    }

    const modal = document.getElementById("modal-sync-gabarito");
    const titleInput = document.getElementById("sync-gabarito-input-title");
    const subtitleInput = document.getElementById("sync-gabarito-input-subtitle");
    const schoolInput = document.getElementById("sync-gabarito-input-school");
    const classroomInput = document.getElementById("sync-gabarito-input-classroom");
    const shiftSelect = document.getElementById("sync-gabarito-select-shift");
    const coverTitleInput = document.getElementById("sync-gabarito-cover-title");
    const coverSubtitleInput = document.getElementById("sync-gabarito-cover-subtitle");
    const coverInstructionsInput = document.getElementById("sync-gabarito-cover-instructions");
    const qCountBadge = document.getElementById("sync-gabarito-qcount-badge");
    const pagesBadge = document.getElementById("sync-gabarito-pages-badge");
    const pageCountInput = document.getElementById("sync-gabarito-input-page-count");
    const missingAlert = document.getElementById("sync-gabarito-missing-alert");
    const missingDesc = document.getElementById("sync-gabarito-missing-desc");
    const warningAlert = document.getElementById("sync-gabarito-warning-alert");
    const warningDesc = document.getElementById("sync-gabarito-warning-desc");
    const statusBadge = document.getElementById("sync-gabarito-status-badge");
    const btnConfirm = document.getElementById("btn-confirm-sync-gabarito");
    const btnLabel = document.getElementById("sync-gabarito-btn-label");

    // Preenche com o estado local do editor
    if (titleInput) titleInput.value = examTitleInput?.value?.trim() || "Avaliação";
    if (subtitleInput) subtitleInput.value = cfgGrade?.value?.trim() || "ENSINO FUNDAMENTAL";
    if (schoolInput) schoolInput.value = cfgSchool?.value?.trim() || "SEMED - LAGOA DA CANOA";
    if (classroomInput) classroomInput.value = "";
    if (shiftSelect) shiftSelect.value = "MANHÃ";
    if (coverTitleInput) coverTitleInput.value = "PROVA CANOA";
    if (coverSubtitleInput) coverSubtitleInput.value = cfgDiscipline?.value?.trim() || "AVALIAÇÃO DIAGNÓSTICA MUNICIPAL";
    if (qCountBadge) {
      qCountBadge.textContent = `${questions.length} ${questions.length === 1 ? 'Questão' : 'Questões'}`;
    }
    if (pageCountInput) {
      pageCountInput.value = "1";
      pageCountInput.oninput = () => {
        const val = parseInt(pageCountInput.value, 10) || 1;
        if (pagesBadge) {
          pagesBadge.textContent = `${val} ${val === 1 ? 'Página' : 'Páginas'}`;
        }
      };
    }
    if (pagesBadge) pagesBadge.textContent = "Calculando...";

    missingAlert?.classList.add("hidden");
    warningAlert?.classList.add("hidden");
    statusBadge?.classList.add("hidden");
    if (btnConfirm) {
      btnConfirm.disabled = false;
      if (btnLabel) btnLabel.textContent = "Criar Gabarito Completo";
    }

    // Validação local de Edge Case 1: Questões sem alternativa correta
    const missingLocally = [];
    questions.forEach((q, idx) => {
      const qNum = q.question_number || (idx + 1);
      const hasCorrect = (q.alternatives || []).some(a => Boolean(a.is_correct));
      if (!hasCorrect) {
        missingLocally.push(qNum);
      }
    });

    if (missingLocally.length > 0) {
      missingAlert?.classList.remove("hidden");
      if (missingDesc) {
        missingDesc.innerHTML = `As seguintes questões estão sem alternativa correta definida no elaborador: <strong>Questão ${missingLocally.join(", ")}</strong>.`;
      }
      if (btnConfirm) {
        btnConfirm.disabled = true;
        if (btnLabel) btnLabel.textContent = "Marque as Respostas no Elaborador";
      }
    }

    // Exibe o modal IMEDIATAMENTE (0ms de atraso percebido)
    modal?.classList.add("active");

    // Sincroniza e consulta status remoto de forma ultrarrápida em background
    (async () => {
      try {
        if (!currentExamId) {
          const savedId = await saveExamToServer({ isAuto: false });
          if (!savedId) return;
        } else {
          await saveExamToServer({ isAuto: false });
        }
      const res = await apiFetch(`/api/exam-builder/exams/${currentExamId}/grading-status`);
      if (res.ok) {
        const st = await res.json();
        if (titleInput && st.title) titleInput.value = st.title;
        if (subtitleInput && (st.subtitle || st.grade_year)) subtitleInput.value = st.subtitle || st.grade_year;
        if (schoolInput && st.school_name) schoolInput.value = st.school_name;
        if (classroomInput && st.classroom) classroomInput.value = st.classroom;
        if (shiftSelect && st.shift) shiftSelect.value = normalizeShift(st.shift);
        if (coverTitleInput && st.cover_title) coverTitleInput.value = st.cover_title;
        if (coverSubtitleInput && (st.cover_subtitle || st.discipline)) coverSubtitleInput.value = st.cover_subtitle || st.discipline;
        if (coverInstructionsInput && st.cover_instructions) coverInstructionsInput.value = st.cover_instructions;

        if (qCountBadge) {
          const numQ = (questions && questions.length) ? questions.length : (st.num_questions || 0);
          qCountBadge.textContent = `${numQ} ${numQ === 1 ? 'Questão' : 'Questões'}`;
        }
        if (st.page_count) {
          if (pageCountInput) pageCountInput.value = st.page_count;
          if (pagesBadge) {
            pagesBadge.textContent = `${st.page_count} ${st.page_count === 1 ? 'Página' : 'Páginas'}`;
          }
        } else if (pageCountInput) {
          const val = parseInt(pageCountInput.value, 10) || 1;
          if (pagesBadge) {
            pagesBadge.textContent = `${val} ${val === 1 ? 'Página' : 'Páginas'}`;
          }
        }

        const modelToSelect = st.cover_model || "opcao_4_azul_nautico_lagoa";
        const radio = document.querySelector(`input[name="sync_cover_model"][value="${modelToSelect}"]`);
        if (radio) {
          radio.checked = true;
          updateCoverRadiosVisual();
        }

        // Validação Edge Case 1 com dados do servidor
        if (st.missing_correct_questions && st.missing_correct_questions.length > 0) {
          missingAlert?.classList.remove("hidden");
          if (missingDesc) {
            missingDesc.innerHTML = `As seguintes questões estão sem alternativa correta definida no elaborador: <strong>Questão ${st.missing_correct_questions.join(", ")}</strong>.`;
          }
          if (btnConfirm) {
            btnConfirm.disabled = true;
            if (btnLabel) btnLabel.textContent = "Marque as Respostas no Elaborador";
          }
        } else if (missingLocally.length === 0) {
          missingAlert?.classList.add("hidden");
          if (btnConfirm) btnConfirm.disabled = false;

          // Se já tem gabarito vinculado
          if (st.has_linked_exam) {
            currentExamHasLinkedGabarito = true;
            if (st.is_gabarito_outdated != null) {
              updateGabaritoOutdatedBanner(st.is_gabarito_outdated);
            }
            statusBadge?.classList.remove("hidden");
            warningAlert?.classList.remove("hidden");
            if (warningDesc) {
              if (st.submissions_count > 0) {
                warningDesc.textContent = `Esta avaliação já possui um gabarito vinculado com ${st.submissions_count} correções registradas. A sincronização atualizará as respostas oficiais no sistema de correção mantendo o histórico de leituras.`;
              } else {
                warningDesc.textContent = `Esta avaliação já possui um gabarito vinculado no sistema de correção. Confirmar atualizará as respostas e regenerará a folha OMR com a capa selecionada.`;
              }
            }
          } else {
            currentExamHasLinkedGabarito = false;
            updateGabaritoOutdatedBanner(false);
            statusBadge?.classList.add("hidden");
            warningAlert?.classList.add("hidden");
            if (btnLabel) btnLabel.textContent = "Criar Gabarito Completo";
          }
        }
      }
    } catch (e) {
      console.warn("Não foi possível carregar status remoto do gabarito:", e);
    }
  })();
}

  function closeSyncGabaritoModal() {
    document.getElementById("modal-sync-gabarito")?.classList.remove("active");
  }

  async function handleConfirmSyncGabarito() {
    const btnConfirm = document.getElementById("btn-confirm-sync-gabarito");
    const btnLabel = document.getElementById("sync-gabarito-btn-label");
    const previousLabel = btnLabel ? btnLabel.textContent : "Criar Gabarito Completo";

    try {
      if (!currentExamId) {
        showToast("ID da avaliação não identificado. Salve a prova primeiro.", "error");
        return;
      }
      if (btnConfirm && btnConfirm.disabled) return;

      const titleInput = document.getElementById("sync-gabarito-input-title");
      const subtitleInput = document.getElementById("sync-gabarito-input-subtitle");
      const schoolInput = document.getElementById("sync-gabarito-input-school");
      const classroomInput = document.getElementById("sync-gabarito-input-classroom");
      const shiftSelect = document.getElementById("sync-gabarito-select-shift");
      const pageCountInput = document.getElementById("sync-gabarito-input-page-count");
      const coverTitleInput = document.getElementById("sync-gabarito-cover-title");
      const coverSubtitleInput = document.getElementById("sync-gabarito-cover-subtitle");
      const coverInstructionsInput = document.getElementById("sync-gabarito-cover-instructions");
      const selectedModel = document.querySelector('input[name="sync_cover_model"]:checked')?.value || "opcao_4_azul_nautico_lagoa";

      const finalPageCount = parseInt(pageCountInput?.value, 10) || 1;

      const payload = {
        title: titleInput?.value?.trim() || examTitleInput?.value?.trim() || "Avaliação",
        subtitle: subtitleInput?.value?.trim() || "",
        school_name: schoolInput?.value?.trim() || cfgSchool?.value?.trim() || "",
        classroom: classroomInput?.value?.trim() || "",
        shift: normalizeShift(shiftSelect?.value),
        page_count: finalPageCount,
        cover_model: selectedModel,
        cover_title: coverTitleInput?.value?.trim() || "PROVA CANOA",
        cover_subtitle: coverSubtitleInput?.value?.trim() || "",
        cover_instructions: coverInstructionsInput?.value?.trim() || ""
      };

      if (btnConfirm) {
        btnConfirm.disabled = true;
        if (btnLabel) btnLabel.textContent = "Gerando Gabarito OMR & Capa...";
      }

      const res = await apiFetch(`/api/exam-builder/exams/${currentExamId}/create-grading-exam`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Falha ao gerar gabarito no sistema de correção.");
      }

      const result = await res.json();
      closeSyncGabaritoModal();
      showToast(result.message || "Gabarito criado com sucesso!", "success");

      // O gabarito agora está perfeitamente sincronizado com as respostas e páginas
      currentExamHasLinkedGabarito = true;
      isGabaritoOutdated = false;
      updateGabaritoOutdatedBanner(false);

      // Abre Modal de Sucesso (Edge Case 2 - Opção A)
      const modalSuccess = document.getElementById("modal-sync-gabarito-success");
      if (modalSuccess) {
        const successTitle = document.getElementById("sync-success-exam-title");
        const successCount = document.getElementById("sync-success-questions-count");
        const successCover = document.getElementById("sync-success-cover-name");
        const successBtnPdf = document.getElementById("sync-success-btn-pdf");
        const successMsg = document.getElementById("sync-success-message");

        if (successTitle) successTitle.textContent = result.title || payload.title;
        if (successCount) successCount.textContent = `${result.num_questions || questions.length} questões oficiais`;
        if (successCover) successCover.textContent = COVER_NAMES[result.cover_model] || result.cover_model;
        if (successBtnPdf) {
          successBtnPdf.href = result.pdf_url || `/storage/sheets/exam_${result.exam_id}.pdf`;
        }
        if (successMsg) {
          successMsg.textContent = result.is_update
            ? "O gabarito oficial e a folha OMR foram atualizados e sincronizados com a capa escolhida."
            : "O gabarito foi criado e vinculado com sucesso no sistema de correção. A folha de respostas OMR está pronta para impressão!";
        }
        modalSuccess.classList.add("active");
      }
    } catch (err) {
      console.error("Erro ao sincronizar gabarito:", err);
      showToast(err.message || "Erro ao conectar ao servidor.", "error");
      if (btnConfirm) {
        btnConfirm.disabled = false;
        if (btnLabel) btnLabel.textContent = previousLabel || "Atualizar Gabarito Oficial";
      }
    }
  }

  // ==========================================================================
  // Minhas Provas Modal
  // ==========================================================================
  async function openMyExamsModal() {
    modalMyExams.classList.add("active");
    const list = document.getElementById("my-exams-list");
    list.innerHTML = `<div class="p-6 text-center text-xs text-outline">Carregando avaliações...</div>`;

    try {
      const res = await apiFetch("/api/exam-builder/exams");
      if (res.ok) {
        const exams = await res.json();
        if (exams.length === 0) {
          list.innerHTML = `<div class="p-6 text-center text-xs text-outline">Nenhuma avaliação salva ainda.</div>`;
          return;
        }

        list.innerHTML = exams.map(e => `
          <div class="flex items-center justify-between p-3 rounded-xl bg-surface-container-low hover:bg-surface-container transition-colors border border-surface-container">
            <div class="flex flex-col min-w-0 pr-3">
              <span class="font-bold text-sm text-on-surface truncate">${escapeHtml(e.title)}</span>
              <span class="text-xs text-on-surface-variant">${escapeHtml(e.discipline || 'Geral')} • ${escapeHtml(e.grade || '')} • Margens: ${e.margin_top || 3.0}cm</span>
            </div>
            <div class="flex items-center gap-1.5 shrink-0">
              <button type="button" class="btn-load-exam px-3 py-1.5 rounded-lg bg-primary-container text-on-primary text-xs font-semibold hover:bg-primary" data-exam-id="${e.id}">Carregar</button>
            </div>
          </div>
        `).join("");

        list.querySelectorAll(".btn-load-exam").forEach(btn => {
          btn.addEventListener("click", () => {
            const id = btn.getAttribute("data-exam-id");
            loadExamById(id);
          });
        });
      }
    } catch (e) {
      list.innerHTML = `<div class="p-6 text-center text-xs text-error">Erro ao carregar avaliações.</div>`;
    }
  }

  async function loadExamById(id) {
    try {
      showToast("Carregando avaliação...", "info");
      const res = await apiFetch(`/api/exam-builder/exams/${id}`);
      if (!res.ok) {
        console.error("Erro ao carregar exame da API:", res.status, res.statusText);
        showToast("Avaliação não encontrada ou erro no servidor.", "error");
        return;
      }

      const exam = await res.json();
      currentExamId = exam.id;

      // 1. Mapeamento Imediato de Questões e Alternativas
      if (Array.isArray(exam.questions) && exam.questions.length > 0) {
        questions = exam.questions.map((q, idx) => ({
          id: q.id || `q_${Date.now()}_${idx}`,
          question_number: idx + 1,
          statement: q.statement || "",
          points: q.points || 1.0,
          difficulty: q.difficulty || "medio",
          bncc_code: q.bncc_code || q.skill || "",
          skill: q.bncc_code || q.skill || "",
          type: q.type || ((q.alternatives && q.alternatives.length > 4) ? "5" : "4"),
          image_url: q.image_url || "",
          alternatives: (q.alternatives || []).map((a, aIdx) => {
            const imgObj = a.image || (a.image_url ? { url: a.image_url, width: a.image_width || '180px', align: a.image_align || 'center' } : null);
            return {
              letter: a.letter || String.fromCharCode(65 + aIdx),
              text: a.text || "",
              is_correct: Boolean(a.is_correct),
              image: imgObj,
              image_url: (imgObj && imgObj.url) ? imgObj.url : (a.image_url || ""),
              image_width: (imgObj && imgObj.width) ? imgObj.width : (a.image_width || "180px"),
              image_align: (imgObj && imgObj.align) ? imgObj.align : (a.image_align || "center")
            };
          })
        }));
      } else {
        questions = [createBlankQuestion(1, globalExamAlternativesMode || 4)];
      }

      const has5 = (questions || []).some(q => q.alternatives && q.alternatives.length >= 5);
      globalExamAlternativesMode = has5 ? 5 : 4;
      if (btnModalAlt4 && btnModalAlt5) {
        if (globalExamAlternativesMode === 4) {
          btnModalAlt4.className = "flex-1 py-1 rounded text-xs font-bold bg-primary-container text-on-primary shadow-sm transition-colors active";
          btnModalAlt5.className = "flex-1 py-1 rounded text-xs font-bold text-on-surface-variant transition-colors";
        } else {
          btnModalAlt5.className = "flex-1 py-1 rounded text-xs font-bold bg-primary-container text-on-primary shadow-sm transition-colors active";
          btnModalAlt4.className = "flex-1 py-1 rounded text-xs font-bold text-on-surface-variant transition-colors";
        }
      }

      // 2. Metadados do Cabeçalho e Configurações
      if (examTitleInput) examTitleInput.value = exam.title || "Avaliação";
      if (cfgInstitution) cfgInstitution.value = exam.institution || "";
      const sName = exam.school_name || "";
      if (cfgSchool) cfgSchool.value = sName;
      try { updateClassroomsDatalist(sName); } catch (e) { console.warn("updateClassroomsDatalist:", e); }
      if (cfgDiscipline) setSelectValueCaseInsensitive(cfgDiscipline, exam.discipline || "MATEMÁTICA");
      if (cfgTeacher) cfgTeacher.value = exam.teacher_name || "";
      if (cfgGrade) cfgGrade.value = exam.grade || exam.grade_year || "";
      if (cfgClassroom) cfgClassroom.value = exam.classroom || "";
      if (cfgShift) cfgShift.value = exam.shift || "MATUTINO";
      if (cfgDate) cfgDate.value = exam.exam_date || "";
      if (cfgMaxScore) cfgMaxScore.value = exam.max_score || 10.0;
      selectedColumns = exam.columns_layout || exam.columns || 2;
      if (chkAnswerSheet) chkAnswerSheet.checked = Boolean(exam.include_answer_sheet);

      if (chkIncludeHeader) {
        const hasHdr = Boolean(exam.include_header) && (exam.header_style === "standard" || !exam.header_style);
        chkIncludeHeader.checked = hasHdr;
        if (boxInstitutionalFields) {
          boxInstitutionalFields.classList.toggle("opacity-40", !hasHdr);
          boxInstitutionalFields.classList.toggle("pointer-events-none", !hasHdr);
        }
      }

      // 3. Margens
      let mt = exam.margin_top != null ? parseFloat(exam.margin_top) : 3.0;
      let mb = exam.margin_bottom != null ? parseFloat(exam.margin_bottom) : 2.0;
      let ml = exam.margin_left != null ? parseFloat(exam.margin_left) : 3.0;
      let mr = exam.margin_right != null ? parseFloat(exam.margin_right) : 2.0;
      if (mt > 4.0) mt = +(mt / 10).toFixed(1);
      if (mb > 4.0) mb = +(mb / 10).toFixed(1);
      if (ml > 4.0) ml = +(ml / 10).toFixed(1);
      if (mr > 4.0) mr = +(mr / 10).toFixed(1);

      if (cfgMarginTop) cfgMarginTop.value = mt;
      if (cfgMarginBottom) cfgMarginBottom.value = mb;
      if (cfgMarginLeft) cfgMarginLeft.value = ml;
      if (cfgMarginRight) cfgMarginRight.value = mr;

      // 4. Renderização Segura do Editor
      activeQuestionIndex = 0;
      try { syncMarginsPresetButtons(); } catch (e) { console.warn("syncMarginsPresetButtons:", e); }
      try { renderSidebarList(); } catch (e) { console.warn("renderSidebarList:", e); }
      try { loadActiveQuestionToEditor(); } catch (e) { console.warn("loadActiveQuestionToEditor:", e); }
      try { updateSummaryBars(); } catch (e) { console.warn("updateSummaryBars:", e); }

      // 5. Verifica se há gabarito OMR vinculado e se requer atualização
      currentExamHasLinkedGabarito = Boolean(exam.has_linked_exam && exam.linked_exam_id && String(exam.linked_exam_id).trim() !== "");
      isGabaritoOutdated = Boolean(currentExamHasLinkedGabarito && exam.is_gabarito_outdated);
      updateGabaritoOutdatedBanner(isGabaritoOutdated);

      if (modalMyExams) modalMyExams.classList.remove("active");
      showToast("Avaliação carregada com sucesso!", "success");
    } catch (err) {
      console.error("Erro ao abrir avaliação no elaborador:", err);
      showToast(`Erro ao abrir avaliação: ${err.message || err}`, "error");
    }
  }

  // ==========================================================================
  // Integração Oficial BNCC (Ensino Fundamental 1º ao 9º Ano)
  // ==========================================================================
  let bnccDebounceTimer = null;
  let bnccAutocompleteDebounceTimer = null;

  function setupBnccSystem() {
    // 1. Carregar filtros de disciplinas da API
    loadBnccFilters();

    // 2. Eventos de Abertura / Fechamento do Modal
    if (btnOpenBnccModal) {
      btnOpenBnccModal.addEventListener("click", openBnccPickerModal);
    }
    if (btnCloseBnccModal) {
      btnCloseBnccModal.addEventListener("click", closeBnccPickerModal);
    }
    if (btnCancelBnccModal) {
      btnCancelBnccModal.addEventListener("click", closeBnccPickerModal);
    }

    // Fechar ao pressionar ESC
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && modalBnccPicker && modalBnccPicker.classList.contains("active")) {
        closeBnccPickerModal();
      }
    });

    // 3. Eventos dos Filtros do Modal com Debounce
    if (bnccFilterDiscipline) {
      bnccFilterDiscipline.addEventListener("change", triggerBnccSearch);
    }
    if (bnccFilterGrade) {
      bnccFilterGrade.addEventListener("change", triggerBnccSearch);
    }
    if (bnccSearchInput) {
      bnccSearchInput.addEventListener("input", () => {
        clearTimeout(bnccDebounceTimer);
        bnccDebounceTimer = setTimeout(triggerBnccSearch, 250);
      });
    }

    // 4. Autocomplete Instantâneo no campo editorQSkill
    if (editorQSkill) {
      editorQSkill.addEventListener("input", (e) => {
        const val = e.target.value.trim();
        if (questions[activeQuestionIndex]) {
          questions[activeQuestionIndex].skill = val;
          questions[activeQuestionIndex].bncc_code = val;
          markUnsaved();
        }
        clearTimeout(bnccAutocompleteDebounceTimer);
        if (val.length < 2) {
          closeBnccAutocomplete();
          return;
        }
        bnccAutocompleteDebounceTimer = setTimeout(() => {
          fetchBnccAutocomplete(val);
        }, 180);
      });

      editorQSkill.addEventListener("change", (e) => {
        const val = e.target.value.trim();
        if (questions[activeQuestionIndex]) {
          questions[activeQuestionIndex].skill = val;
          questions[activeQuestionIndex].bncc_code = val;
          markUnsaved();
        }
      });

      // Fechar autocomplete se clicar fora
      document.addEventListener("click", (e) => {
        if (!e.target.closest("#editor-q-skill") && !e.target.closest("#bncc-autocomplete-list")) {
          closeBnccAutocomplete();
        }
      });
    }
  }

  async function loadBnccFilters() {
    try {
      const res = await apiFetch("/api/bncc/filtros");
      if (!res.ok) return;
      const data = await res.json();
      if (bnccFilterDiscipline && data.disciplinas) {
        bnccFilterDiscipline.innerHTML = '<option value="">Todas as Disciplinas</option>';
        data.disciplinas.forEach(disc => {
          const opt = document.createElement("option");
          opt.value = disc;
          opt.textContent = disc;
          bnccFilterDiscipline.appendChild(opt);
        });
      }
    } catch (err) {
      console.warn("Aviso ao carregar filtros BNCC:", err);
    }
  }

  function openBnccPickerModal() {
    if (!modalBnccPicker) return;

    // Pré-selecionar disciplina e ano com base na prova atual
    if (bnccFilterDiscipline && cfgDiscipline) {
      const discVal = cfgDiscipline.value.trim().toLowerCase();
      Array.from(bnccFilterDiscipline.options).forEach(opt => {
        if (opt.value && discVal.includes(opt.value.toLowerCase())) {
          opt.selected = true;
        }
      });
    }

    if (bnccFilterGrade && cfgGrade) {
      const gradeVal = cfgGrade.value;
      const match = gradeVal.match(/(\d)/);
      if (match && match[1]) {
        bnccFilterGrade.value = match[1];
      }
    }

    // Limpar termo de busca e disparar busca
    if (bnccSearchInput) {
      bnccSearchInput.value = "";
    }

    modalBnccPicker.classList.add("active");
    triggerBnccSearch();
    setTimeout(() => {
      if (bnccSearchInput) bnccSearchInput.focus();
    }, 150);
  }

  function closeBnccPickerModal() {
    if (modalBnccPicker) modalBnccPicker.classList.remove("active");
  }

  async function triggerBnccSearch() {
    if (!bnccCardsList) return;
    const discipline = bnccFilterDiscipline ? bnccFilterDiscipline.value : "";
    const ano = bnccFilterGrade ? bnccFilterGrade.value : "";
    const q = bnccSearchInput ? bnccSearchInput.value.trim() : "";

    bnccCardsList.innerHTML = `
      <div class="py-12 flex flex-col items-center justify-center text-slate-400 gap-2">
        <span class="material-symbols-outlined text-[32px] animate-spin text-blue-600">sync</span>
        <span class="text-xs font-medium">Buscando habilidades na BNCC...</span>
      </div>
    `;

    try {
      const params = new URLSearchParams();
      if (discipline) params.append("disciplina", discipline);
      if (ano) params.append("ano", ano);
      if (q) params.append("q", q);
      params.append("limit", "80");

      const res = await apiFetch(`/api/bncc/habilidades?${params.toString()}`);
      if (!res.ok) throw new Error("Falha na consulta");
      const data = await res.json();

      renderBnccSkillsCards(data.habilidades || []);
      if (bnccResultsCount) {
        bnccResultsCount.textContent = `${data.total} habilidade(s) encontrada(s)${data.total > 80 ? ' (exibindo as 80 primeiras)' : ''}`;
      }
    } catch (err) {
      bnccCardsList.innerHTML = `
        <div class="p-8 text-center text-slate-400 text-xs">
          Erro ao carregar dados da BNCC. Verifique a conexão com o servidor.
        </div>
      `;
    }
  }

  function renderBnccSkillsCards(skills) {
    if (!bnccCardsList) return;
    bnccCardsList.innerHTML = "";

    if (skills.length === 0) {
      bnccCardsList.innerHTML = `
        <div class="py-12 flex flex-col items-center justify-center text-slate-400 gap-2">
          <span class="material-symbols-outlined text-[36px]">search_off</span>
          <span class="text-xs font-semibold">Nenhuma habilidade encontrada com os filtros selecionados.</span>
          <span class="text-[11px]">Tente buscar por outro termo ou limpar os filtros de disciplina e ano.</span>
        </div>
      `;
      return;
    }

    skills.forEach(skill => {
      const card = document.createElement("div");
      card.className = "bg-white p-3.5 rounded-xl border border-slate-200/90 shadow-2xs hover:border-blue-400 hover:shadow-xs transition-all flex flex-col gap-2";

      card.innerHTML = `
        <div class="flex items-center justify-between flex-wrap gap-2">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="px-2 py-0.5 rounded-md bg-blue-600 text-white font-mono font-bold text-xs tracking-wider shadow-2xs">${escapeHtml(skill.codigo)}</span>
            <span class="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 font-semibold text-[11px] border border-slate-200">${escapeHtml(skill.componente)}</span>
            <span class="px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 font-medium text-[11px] border border-slate-200">${escapeHtml(skill.ano_label)}</span>
            ${skill.unidade_tematica ? `<span class="text-[11px] text-slate-500 italic">• ${escapeHtml(skill.unidade_tematica)}</span>` : ''}
          </div>
          <button type="button" class="btn-press btn-select-skill px-3 py-1 rounded-lg bg-blue-50 hover:bg-blue-600 text-blue-700 hover:text-white border border-blue-200 hover:border-transparent text-xs font-bold transition-all flex items-center gap-1">
            <span class="material-symbols-outlined text-[15px]">check_circle</span>
            <span>Selecionar</span>
          </button>
        </div>
        <p class="text-xs text-slate-700 leading-relaxed text-justify">${escapeHtml(skill.texto)}</p>
      `;

      card.querySelector(".btn-select-skill").addEventListener("click", () => {
        selectBnccSkill(skill.codigo);
      });

      bnccCardsList.appendChild(card);
    });
  }

  function selectBnccSkill(code) {
    const cleanCode = (code || "").trim();
    if (editorQSkill) {
      editorQSkill.value = cleanCode;
    }
    if (questions[activeQuestionIndex]) {
      questions[activeQuestionIndex].skill = cleanCode;
      questions[activeQuestionIndex].bncc_code = cleanCode;
    }
    closeBnccPickerModal();
    closeBnccAutocomplete();
    markUnsaved();
    saveExamToServer({ isAuto: true });
    showToast(`Habilidade ${cleanCode} vinculada com sucesso!`, "success");
  }

  async function fetchBnccAutocomplete(term) {
    if (!bnccAutocompleteList) return;
    try {
      const res = await apiFetch(`/api/bncc/habilidades?q=${encodeURIComponent(term)}&limit=6`);
      if (!res.ok) return;
      const data = await res.json();
      const skills = data.habilidades || [];

      if (skills.length === 0) {
        closeBnccAutocomplete();
        return;
      }

      bnccAutocompleteList.innerHTML = "";
      skills.forEach(skill => {
        const item = document.createElement("div");
        item.className = "p-2 rounded-lg hover:bg-blue-50 cursor-pointer transition-colors flex flex-col gap-0.5 border-b border-slate-100 last:border-b-0";
        item.innerHTML = `
          <div class="flex items-center justify-between text-xs">
            <strong class="font-mono text-blue-700">${escapeHtml(skill.codigo)}</strong>
            <span class="text-[10px] text-slate-500">${escapeHtml(skill.componente)} • ${escapeHtml(skill.ano_label)}</span>
          </div>
          <span class="text-[11px] text-slate-600 line-clamp-2 leading-tight">${escapeHtml(skill.texto)}</span>
        `;
        item.addEventListener("click", () => {
          selectBnccSkill(skill.codigo);
        });
        bnccAutocompleteList.appendChild(item);
      });

      bnccAutocompleteList.classList.remove("hidden");
    } catch (err) {
      closeBnccAutocomplete();
    }
  }

  function closeBnccAutocomplete() {
    if (bnccAutocompleteList) {
      bnccAutocompleteList.classList.add("hidden");
      bnccAutocompleteList.innerHTML = "";
    }
  }

  // ==========================================================================
  // Integração com o Banco de Questões da SEMED
  // ==========================================================================
  let modalBankImport = null;
  let bankImportQuestions = [];
  let selectedBankQuestionIds = new Set();
  let bankDebounceTimer = null;
  let bankFiltersLoaded = false;

  function setupBankImportSystem() {
    modalBankImport = document.getElementById("modal-bank-import");
    const btnHeaderBankImport = document.getElementById("btn-header-bank-import");
    const btnOpenBankImportSide = document.getElementById("btn-open-bank-import-side");
    const btnCloseBankImport = document.getElementById("btn-close-bank-import-modal");
    const btnCancelBankImport = document.getElementById("btn-cancel-bank-import-modal");
    const bankSearchInput = document.getElementById("bank-import-search-input");
    const bankFilterDiscipline = document.getElementById("bank-import-filter-discipline");
    const bankFilterGrade = document.getElementById("bank-import-filter-grade");
    const btnConfirmImport = document.getElementById("btn-confirm-bank-import");
    const btnSelectAll = document.getElementById("btn-bank-select-all");
    const btnClearSel = document.getElementById("btn-bank-clear-selection");

    if (btnHeaderBankImport) {
      btnHeaderBankImport.addEventListener("click", openBankImportModal);
    }
    if (btnOpenBankImportSide) {
      btnOpenBankImportSide.addEventListener("click", openBankImportModal);
    }
    if (btnCloseBankImport) {
      btnCloseBankImport.addEventListener("click", closeBankImportModal);
    }
    if (btnCancelBankImport) {
      btnCancelBankImport.addEventListener("click", closeBankImportModal);
    }

    if (bankSearchInput) {
      bankSearchInput.addEventListener("input", () => {
        clearTimeout(bankDebounceTimer);
        bankDebounceTimer = setTimeout(fetchBankQuestionsForImport, 350);
      });
    }

    if (bankFilterDiscipline) {
      bankFilterDiscipline.addEventListener("change", fetchBankQuestionsForImport);
    }

    if (bankFilterGrade) {
      bankFilterGrade.addEventListener("change", fetchBankQuestionsForImport);
    }

    if (btnSelectAll) {
      btnSelectAll.addEventListener("click", () => {
        bankImportQuestions.forEach(q => selectedBankQuestionIds.add(q.id));
        updateBankCheckboxes();
        updateBankSelectionState();
      });
    }

    if (btnClearSel) {
      btnClearSel.addEventListener("click", () => {
        selectedBankQuestionIds.clear();
        updateBankCheckboxes();
        updateBankSelectionState();
      });
    }

    if (btnConfirmImport) {
      btnConfirmImport.addEventListener("click", confirmImportSelectedBankQuestions);
    }
  }

  async function openBankImportModal() {
    if (!modalBankImport) modalBankImport = document.getElementById("modal-bank-import");
    if (!modalBankImport) return;

    modalBankImport.classList.add("active");
    selectedBankQuestionIds.clear();
    updateBankSelectionState();

    if (!bankFiltersLoaded) {
      await loadBankImportFilters();
    }

    // Pré-selecionar disciplina e ano com base na prova atual se estiverem vazios
    const bankFilterDiscipline = document.getElementById("bank-import-filter-discipline");
    const bankFilterGrade = document.getElementById("bank-import-filter-grade");

    if (bankFilterDiscipline && cfgDiscipline && cfgDiscipline.value && !bankFilterDiscipline.value) {
      const discVal = cfgDiscipline.value.trim().toLowerCase();
      Array.from(bankFilterDiscipline.options).forEach(opt => {
        if (opt.value && discVal.includes(opt.value.toLowerCase())) {
          opt.selected = true;
        }
      });
    }

    if (bankFilterGrade && cfgGrade && cfgGrade.value && !bankFilterGrade.value) {
      const match = cfgGrade.value.match(/(\d)/);
      if (match && match[1]) {
        Array.from(bankFilterGrade.options).forEach(opt => {
          if (opt.value && opt.value.includes(match[1])) {
            opt.selected = true;
          }
        });
      }
    }

    await fetchBankQuestionsForImport();

    const searchInput = document.getElementById("bank-import-search-input");
    if (searchInput) {
      setTimeout(() => searchInput.focus(), 100);
    }
  }

  function closeBankImportModal() {
    if (!modalBankImport) modalBankImport = document.getElementById("modal-bank-import");
    if (modalBankImport) modalBankImport.classList.remove("active");
  }

  async function loadBankImportFilters() {
    try {
      const res = await apiFetch("/api/exam-builder/bank/filters");
      if (res.ok) {
        const data = await res.json();
        const discSelect = document.getElementById("bank-import-filter-discipline");
        const gradeSelect = document.getElementById("bank-import-filter-grade");

        if (discSelect && Array.isArray(data.disciplines)) {
          discSelect.innerHTML = '<option value="">Todas as Disciplinas</option>';
          data.disciplines.forEach(d => {
            if (d) {
              const opt = document.createElement("option");
              opt.value = d;
              opt.textContent = d;
              discSelect.appendChild(opt);
            }
          });
        }

        if (gradeSelect && Array.isArray(data.grades)) {
          gradeSelect.innerHTML = '<option value="">Todos os Anos</option>';
          data.grades.forEach(g => {
            if (g) {
              const opt = document.createElement("option");
              opt.value = g;
              opt.textContent = g;
              gradeSelect.appendChild(opt);
            }
          });
        }

        bankFiltersLoaded = true;
      }
    } catch (err) {
      console.warn("Aviso ao carregar filtros do banco de questões:", err);
    }
  }

  async function fetchBankQuestionsForImport() {
    const list = document.getElementById("bank-import-cards-list");
    const statusText = document.getElementById("bank-import-status-text");
    const searchInput = document.getElementById("bank-import-search-input");
    const discSelect = document.getElementById("bank-import-filter-discipline");
    const gradeSelect = document.getElementById("bank-import-filter-grade");

    if (!list) return;

    list.innerHTML = `
      <div class="py-12 flex flex-col items-center justify-center text-slate-400 gap-2">
        <span class="material-symbols-outlined text-[32px] animate-spin text-indigo-600">sync</span>
        <span class="text-xs font-medium">Buscando questões no banco...</span>
      </div>
    `;

    try {
      const params = new URLSearchParams();
      if (searchInput && searchInput.value.trim()) params.append("query", searchInput.value.trim());
      if (discSelect && discSelect.value) params.append("discipline", discSelect.value);
      if (gradeSelect && gradeSelect.value) params.append("grade_year", gradeSelect.value);
      params.append("limit", "100");

      const res = await apiFetch(`/api/exam-builder/bank/questions?${params.toString()}`);
      if (!res.ok) throw new Error("Erro na resposta da API");

      const resData = await res.json();
      const questionsData = Array.isArray(resData) ? resData : (resData.items || []);
      bankImportQuestions = questionsData;

      if (statusText) {
        statusText.textContent = `${questionsData.length} questão(ões) encontrada(s) no acervo`;
      }

      renderBankImportCards(questionsData);
    } catch (err) {
      list.innerHTML = `
        <div class="py-10 text-center text-rose-500 text-xs">
          Erro ao carregar questões do banco. Verifique a conexão com o servidor.
        </div>
      `;
    }
  }

  function renderBankImportCards(items) {
    const list = document.getElementById("bank-import-cards-list");
    if (!list) return;

    if (!items || items.length === 0) {
      list.innerHTML = `
        <div class="py-12 flex flex-col items-center justify-center text-slate-400 gap-2">
          <span class="material-symbols-outlined text-[36px] text-slate-300">search_off</span>
          <span class="text-xs font-medium">Nenhuma questão encontrada com os filtros selecionados.</span>
        </div>
      `;
      return;
    }

    list.innerHTML = items.map((q, idx) => {
      const isChecked = selectedBankQuestionIds.has(q.id);
      const disc = q.discipline || "Geral";
      const grade = q.grade_year || "";
      const bncc = q.bncc_code || q.skill || "";
      const points = parseFloat(q.points || 1.0).toFixed(1).replace(".", ",");

      let cleanStatement = (q.statement || "").replace(/<[^>]+>/g, " ").trim();
      if (cleanStatement.length > 220) cleanStatement = cleanStatement.substring(0, 220) + "...";

      let altsHtml = "";
      if (Array.isArray(q.alternatives) && q.alternatives.length > 0) {
        altsHtml = `
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-1.5 mt-2.5 pt-2.5 border-t border-slate-100">
            ${q.alternatives.map(a => {
              const altImg = a.image_url || (a.image && a.image.url) || "";
              return `
              <div class="flex flex-col items-start gap-1 text-[11px] p-2 rounded-lg ${a.is_correct ? 'bg-emerald-50/80 border border-emerald-200 font-semibold text-emerald-900' : 'bg-slate-50 border border-slate-100 text-slate-700'}">
                <div class="flex items-center gap-1.5 w-full">
                  <span class="font-bold font-mono px-1 rounded ${a.is_correct ? 'bg-emerald-600 text-white' : 'bg-slate-200 text-slate-700'}">
                    ${escapeHtml(a.letter || 'A')}
                  </span>
                  <span class="truncate flex-1">${escapeHtml(a.text || '')}</span>
                  ${a.is_correct ? '<span class="material-symbols-outlined text-[14px] text-emerald-600 shrink-0">check_circle</span>' : ''}
                </div>
                ${altImg ? `<img src="${escapeHtml(altImg)}" alt="Alternativa ${escapeHtml(a.letter || '')}" class="max-h-20 w-auto object-contain rounded border border-slate-200 bg-white p-0.5 mt-1" loading="lazy">` : ''}
              </div>
            `}).join("")}
          </div>
        `;
      }

      return `
        <div class="bank-item-card p-3.5 rounded-xl border transition-all cursor-pointer select-none ${isChecked ? 'bg-indigo-50/70 border-indigo-300 shadow-xs' : 'bg-white border-slate-200 hover:border-indigo-200 hover:bg-slate-50/80'}" data-bank-id="${escapeHtml(q.id)}">
          <div class="flex items-start gap-3">
            <input type="checkbox" class="bank-item-checkbox mt-1 accent-indigo-600 w-4 h-4 cursor-pointer rounded pointer-events-none" ${isChecked ? 'checked' : ''}>
            <div class="flex-1 min-w-0">
              <div class="flex flex-wrap items-center gap-2 pb-1.5">
                <span class="px-2 py-0.5 rounded-md bg-indigo-100 text-indigo-800 text-[10px] font-bold uppercase tracking-wider">${escapeHtml(disc)}</span>
                ${grade ? `<span class="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 text-[10px] font-semibold">${escapeHtml(grade)}</span>` : ''}
                ${bncc ? `<span class="px-2 py-0.5 rounded-md bg-blue-100 text-blue-800 text-[10px] font-mono font-bold">${escapeHtml(bncc)}</span>` : ''}
                <span class="text-[11px] text-slate-400 font-medium ml-auto">${points} pt</span>
              </div>
              <div class="text-xs text-slate-800 font-medium leading-relaxed math-rendered-preview">
                ${escapeHtml(cleanStatement)}
              </div>
              ${altsHtml}
            </div>
          </div>
        </div>
      `;
    }).join("");

    // Render KaTeX formulas in cards
    if (window.renderMathInElement) {
      try {
        renderMathInElement(list, {
          delimiters: [
            { left: "$$", right: "$$", display: true },
            { left: "$", right: "$", display: false },
            { left: "\\[", right: "\\]", display: true },
            { left: "\\(", right: "\\)", display: false }
          ],
          throwOnError: false
        });
      } catch (e) { }
    }

    // Toggle click listeners
    list.querySelectorAll(".bank-item-card").forEach(card => {
      card.addEventListener("click", () => {
        const id = card.getAttribute("data-bank-id");
        if (selectedBankQuestionIds.has(id)) {
          selectedBankQuestionIds.delete(id);
        } else {
          selectedBankQuestionIds.add(id);
        }
        updateBankCheckboxes();
        updateBankSelectionState();
      });
    });
  }

  function updateBankCheckboxes() {
    const list = document.getElementById("bank-import-cards-list");
    if (!list) return;
    list.querySelectorAll(".bank-item-card").forEach(card => {
      const id = card.getAttribute("data-bank-id");
      const isChecked = selectedBankQuestionIds.has(id);
      const chk = card.querySelector(".bank-item-checkbox");
      if (chk) chk.checked = isChecked;

      if (isChecked) {
        card.classList.add("bg-indigo-50/70", "border-indigo-300", "shadow-xs");
        card.classList.remove("bg-white", "border-slate-200");
      } else {
        card.classList.remove("bg-indigo-50/70", "border-indigo-300", "shadow-xs");
        card.classList.add("bg-white", "border-slate-200");
      }
    });
  }

  function updateBankSelectionState() {
    const count = selectedBankQuestionIds.size;
    const countLabel = document.getElementById("bank-import-selected-count");
    const confirmBtn = document.getElementById("btn-confirm-bank-import");
    const confirmText = document.getElementById("btn-confirm-bank-import-text");

    if (countLabel) {
      countLabel.textContent = `${count} questão(ões) selecionada(s)`;
    }
    if (confirmBtn) {
      confirmBtn.disabled = (count === 0);
    }
    if (confirmText) {
      confirmText.textContent = count > 0 ? `Importar ${count} Questão(ões)` : "Importar para a Prova";
    }
  }

  function confirmImportSelectedBankQuestions() {
    if (selectedBankQuestionIds.size === 0) return;

    const selectedItems = bankImportQuestions.filter(q => selectedBankQuestionIds.has(q.id));
    if (selectedItems.length === 0) return;

    saveCurrentEditorState();

    selectedItems.forEach((q, idx) => {
      const newId = `q_imported_${Date.now()}_${idx}_${Math.random().toString(36).substr(2, 4)}`;
      const importedQ = {
        id: newId,
        question_number: questions.length + 1,
        statement: q.statement || "",
        points: typeof q.points === "number" ? q.points : (parseFloat(q.points) || 1.0),
        difficulty: q.difficulty || "medio",
        bncc_code: q.bncc_code || q.skill || "",
        skill: q.bncc_code || q.skill || "",
        type: String(globalExamAlternativesMode || 4),
        image_url: q.image_url || "",
        alternatives: (q.alternatives || []).map((a, aIdx) => {
          const imgObj = a.image || (a.image_url ? { url: a.image_url, width: a.image_width || '180px', align: a.image_align || 'center' } : null);
          return {
            letter: a.letter || String.fromCharCode(65 + aIdx),
            text: a.text || "",
            is_correct: Boolean(a.is_correct),
            image: imgObj,
            image_url: (imgObj && imgObj.url) ? imgObj.url : (a.image_url || ""),
            image_width: (imgObj && imgObj.width) ? imgObj.width : (a.image_width || "180px"),
            image_align: (imgObj && imgObj.align) ? imgObj.align : (a.image_align || "center")
          };
        })
      };

      // Garantir compatibilidade com o modo de alternativas da prova
      while (importedQ.alternatives.length < globalExamAlternativesMode) {
        const nextIdx = importedQ.alternatives.length;
        importedQ.alternatives.push({
          letter: String.fromCharCode(65 + nextIdx),
          text: "",
          is_correct: false
        });
      }
      if (importedQ.alternatives.length > globalExamAlternativesMode) {
        importedQ.alternatives = importedQ.alternatives.slice(0, globalExamAlternativesMode);
      }

      questions.push(importedQ);
    });

    // Renumerar questões
    questions.forEach((q, i) => { q.question_number = i + 1; });

    // Selecionar a primeira questão importada no editor
    activeQuestionIndex = questions.length - selectedItems.length;

    renderSidebarList();
    loadActiveQuestionToEditor();
    updateSummaryBars();
    updateRealtimeQuestionPreview();
    updateLiveSheetPreview();
    markUnsaved();

    closeBankImportModal();
    showToast(`${selectedItems.length} questão(ões) importada(s) do banco de questões!`, "success");
  }

  // ==========================================================================
  // Funções Utilitárias
  // ==========================================================================
  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function showToast(msg, type = "info", options = {}) {
    let container = document.getElementById("toast-container");
    if (!container) {
      container = document.createElement("div");
      container.id = "toast-container";
      container.className = "toast-container";
      container.setAttribute("aria-live", "polite");
      document.body.appendChild(container);
    }

    // Limita número de notificações simultâneas para não poluir a tela
    while (container.children.length >= 5) {
      container.removeChild(container.firstChild);
    }

    const validTypes = ["success", "error", "warning", "info"];
    const toastType = validTypes.includes(type) ? type : "info";

    const duration = options.duration || (toastType === "error" ? 4500 : 3500);

    const defaultTitles = {
      success: "Sucesso",
      error: "Erro",
      warning: "Atenção",
      info: "Informação"
    };
    const titleText = options.title || defaultTitles[toastType];

    const icons = {
      success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
      error: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
      warning: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
      info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>'
    };

    const toast = document.createElement("div");
    toast.className = `toast-card toast-${toastType}`;
    toast.setAttribute("role", "alert");

    toast.innerHTML = `
      <div class="toast-icon-wrap">
        ${icons[toastType]}
      </div>
      <div class="toast-body">
        <div class="toast-title">${escapeHtml(titleText)}</div>
        <div class="toast-message">${escapeHtml(msg)}</div>
      </div>
      <button type="button" class="toast-close-btn" title="Fechar notificação" aria-label="Fechar notificação">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
      <div class="toast-progress-track">
        <div class="toast-progress-bar" style="animation-duration: ${duration}ms;"></div>
      </div>
    `;

    container.appendChild(toast);

    let dismissTimer = null;
    let remainingTime = duration;
    let startTime = Date.now();

    function startTimer(time) {
      startTime = Date.now();
      remainingTime = time;
      dismissTimer = setTimeout(dismissToast, remainingTime);
    }

    function pauseTimer() {
      if (dismissTimer) {
        clearTimeout(dismissTimer);
        dismissTimer = null;
        remainingTime -= (Date.now() - startTime);
        if (remainingTime < 500) remainingTime = 500;
      }
    }

    function dismissToast() {
      if (dismissTimer) clearTimeout(dismissTimer);
      toast.classList.add("toast-hiding");
      setTimeout(() => {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
      }, 280);
    }

    // Botão de fechar
    const closeBtn = toast.querySelector(".toast-close-btn");
    if (closeBtn) {
      closeBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        dismissToast();
      });
    }

    // Pausar tempo no hover
    toast.addEventListener("mouseenter", pauseTimer);
    toast.addEventListener("mouseleave", () => {
      startTimer(remainingTime);
    });

    startTimer(duration);
  }

  // --- Modal de Confirmação Moderno (Substitui confirm nativo) ---
  function showConfirmModal({
    title = "Confirmar ação",
    message = "Tem certeza que deseja continuar?",
    confirmText = "Confirmar",
    cancelText = "Cancelar",
    type = "danger"
  } = {}) {
    return new Promise((resolve) => {
      let overlay = document.getElementById("confirm-modal-overlay");
      if (!overlay) {
        overlay = document.createElement("div");
        overlay.id = "confirm-modal-overlay";
        overlay.className = "confirm-modal-overlay";
        document.body.appendChild(overlay);
      }

      const icons = {
        danger: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>',
        warning: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
        info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>'
      };

      const iconSvg = icons[type] || icons.danger;

      overlay.innerHTML = `
        <div class="confirm-modal-card" role="dialog" aria-modal="true">
          <button type="button" class="confirm-modal-close" aria-label="Fechar modal">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
          <div class="confirm-modal-icon-wrap type-${type}">
            ${iconSvg}
          </div>
          <div class="confirm-modal-title">${escapeHtml(title)}</div>
          <div class="confirm-modal-message">${escapeHtml(message)}</div>
          <div class="confirm-modal-actions">
            <button type="button" class="confirm-btn-cancel">${escapeHtml(cancelText)}</button>
            <button type="button" class="confirm-btn-confirm type-${type}">${escapeHtml(confirmText)}</button>
          </div>
        </div>
      `;

      requestAnimationFrame(() => {
        overlay.classList.add("active");
      });

      function closeDialog(result) {
        overlay.classList.remove("active");
        cleanup();
        setTimeout(() => {
          overlay.innerHTML = "";
          resolve(result);
        }, 220);
      }

      function onKeyDown(e) {
        if (e.key === "Escape") {
          e.preventDefault();
          closeDialog(false);
        } else if (e.key === "Enter") {
          e.preventDefault();
          closeDialog(true);
        }
      }

      function onOverlayClick(e) {
        if (e.target === overlay) {
          closeDialog(false);
        }
      }

      function cleanup() {
        document.removeEventListener("keydown", onKeyDown);
        overlay.removeEventListener("click", onOverlayClick);
      }

      overlay.querySelector(".confirm-btn-cancel").addEventListener("click", () => closeDialog(false));
      overlay.querySelector(".confirm-modal-close").addEventListener("click", () => closeDialog(false));
      overlay.querySelector(".confirm-btn-confirm").addEventListener("click", () => closeDialog(true));
      overlay.addEventListener("click", onOverlayClick);
      document.addEventListener("keydown", onKeyDown);

      setTimeout(() => {
        const btn = overlay.querySelector(".confirm-btn-confirm");
        if (btn) btn.focus();
      }, 50);
    });
  }

})();

