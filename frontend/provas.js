/**
 * provas.js - Gerenciador do Hub de Avaliações e Banco de Questões
 * SEMED Lagoa da Canoa • Edição Stitch Design System
 */

document.addEventListener("DOMContentLoaded", () => {
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
    const defaultHeaders = {
      ...getAuthHeaders()
    };
    if (options.body && typeof options.body === "string" && !(options.headers && options.headers["Content-Type"])) {
      defaultHeaders["Content-Type"] = "application/json";
    }
    const headers = {
      ...defaultHeaders,
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
    else if (role === "coordenador") roleText = "Coordenação Pedagógica";
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
          await fetch("/api/auth/logout", {
            method: "POST",
            headers: getAuthHeaders()
          });
        } catch (e) { }
        clearAuthToken();
        window.location.replace("/");
      };
    }
  }

  // Estado Global
  let allExams = [];
  let selectedExamIds = new Set();
  let bankQuestions = [];
  let bankTotalQuestions = 0;
  const bankPageSize = 30;
  let bankCurrentOffset = 0;
  let bankIsLoading = false;
  let bankHasMore = true;
  let selectedBankQuestions = new Set();
  let currentEmitirExam = null;
  let selectedEmitirFormat = "pdf";
  let activeTab = "exams"; // 'exams' ou 'bank'
  let currentViewMode = "table"; // 'table' ou 'cards'
  let searchDebounceTimer = null;


  // Elementos do DOM - Estatísticas & Abas
  const statTotalExams = document.getElementById("stat-total-exams");
  const statInProgress = document.getElementById("stat-in-progress");
  const statPendingGrading = document.getElementById("stat-pending-grading");
  const statCompleted = document.getElementById("stat-completed");
  const statTotalQuestions = document.getElementById("stat-total-questions");

  const tabBtnExams = document.getElementById("tab-btn-exams");
  const tabBtnBank = document.getElementById("tab-btn-bank");
  const btnGotoBank = document.getElementById("btn-goto-bank");
  const badgeCountExams = document.getElementById("badge-count-exams");
  const badgeCountQuestions = document.getElementById("badge-count-questions");
  const panelExams = document.getElementById("panel-exams");
  const panelBank = document.getElementById("panel-bank");

  // Elementos - Painel Provas & Alternador de Visualização
  const btnViewTable = document.getElementById("btn-view-table");
  const btnViewCards = document.getElementById("btn-view-cards");
  const tableExamsContainer = document.getElementById("table-exams-container");
  const tbodyExams = document.getElementById("tbody-exams");
  const gridExams = document.getElementById("grid-exams");
  const labelTableCount = document.getElementById("label-table-count");
  const emptyExamsState = document.getElementById("empty-exams-state");

  // Elementos - Seleção em Massa de Avaliações
  const chkSelectAllExams = document.getElementById("chk-select-all-exams");
  const barBatchActions = document.getElementById("bar-batch-actions");
  const labelBatchSelectedCount = document.getElementById("label-batch-selected-count");
  const btnBatchDeleteExams = document.getElementById("btn-batch-delete-exams");
  const btnBatchClearSelection = document.getElementById("btn-batch-clear-selection");

  // Filtros de Provas
  const inputSearchExams = document.getElementById("input-search-exams");
  const selectFilterDiscipline = document.getElementById("select-filter-discipline");
  const selectFilterGrade = document.getElementById("select-filter-grade");
  const selectFilterStatus = document.getElementById("select-filter-status");
  const btnClearExamFilters = document.getElementById("btn-clear-exam-filters");
  const btnRefreshExams = document.getElementById("btn-refresh-exams");
  const btnEmptyCreate = document.getElementById("btn-empty-create");

  // Elementos - Painel Banco de Questões
  const listBankQuestions = document.getElementById("list-bank-questions");
  const emptyBankState = document.getElementById("empty-bank-state");
  const bankInputQuery = document.getElementById("bank-input-query");
  const bankSelectDiscipline = document.getElementById("bank-select-discipline");
  const bankSelectGrade = document.getElementById("bank-select-grade");
  const bankInputBncc = document.getElementById("bank-input-bncc");
  const btnClearBankFilters = document.getElementById("btn-clear-bank-filters");
  const bankFilteredCount = document.getElementById("bank-filtered-count");
  const bankScrollSentinel = document.getElementById("bank-scroll-sentinel");
  const bankScrollLoader = document.getElementById("bank-scroll-loader");
  const bankScrollEnd = document.getElementById("bank-scroll-end");
  const btnOpenBnccModal = document.getElementById("btn-open-bncc-modal");
  const modalBnccPicker = document.getElementById("modal-bncc-picker");
  const btnCloseBnccModal = document.getElementById("btn-close-bncc-modal");
  const btnCancelBnccModal = document.getElementById("btn-cancel-bncc-modal");
  const bnccModalFilterDiscipline = document.getElementById("bncc-modal-filter-discipline");
  const bnccModalFilterGrade = document.getElementById("bncc-modal-filter-grade");
  const bnccModalSearchInput = document.getElementById("bncc-modal-search-input");
  const bnccModalResultsCount = document.getElementById("bncc-modal-results-count");
  const bnccModalCardsList = document.getElementById("bncc-modal-cards-list");
  let bnccModalDebounceTimer = null;
  let bnccPickerTarget = null;

  // Elementos - Modal Criar Nova Prova
  const modalCreateExam = document.getElementById("modal-create-exam");
  const btnOpenCreateModal = document.getElementById("btn-open-create-modal");
  const btnCloseCreateModal = document.getElementById("btn-close-create-modal");
  const btnCancelCreate = document.getElementById("btn-cancel-create");
  const btnConfirmCreateExam = document.getElementById("btn-confirm-create-exam");
  const modalInputTitle = document.getElementById("modal-input-title");
  const modalInputDiscipline = document.getElementById("modal-input-discipline");
  const modalSelectGrade = document.getElementById("modal-select-grade");
  const modalInputClassroom = document.getElementById("modal-input-classroom");
  const modalInputSchool = document.getElementById("modal-input-school");
  const optionCreateTypes = document.querySelectorAll(".option-create-type");
  const modalBankSelectorArea = document.getElementById("modal-bank-selector-area");
  const modalBankSelectedCount = document.getElementById("modal-bank-selected-count");
  const modalBankQuickSearch = document.getElementById("modal-bank-quick-search");
  const modalBankQuestionsChecklist = document.getElementById("modal-bank-questions-checklist");

  // Elementos - Modal Emitir Prova
  const modalEmitirProva = document.getElementById("modal-emitir-prova");
  const btnCloseEmitirModal = document.getElementById("btn-close-emitir-modal");
  const btnCancelEmitir = document.getElementById("btn-cancel-emitir");
  const btnConfirmEmitirDownload = document.getElementById("btn-confirm-emitir-download");
  const optionEmitirFormats = document.querySelectorAll(".option-emitir-format");

  // Elementos - Modal de Confirmação Moderno
  const modalConfirmDialog = document.getElementById("modal-confirm-dialog");
  const confirmDialogIconBox = document.getElementById("confirm-dialog-icon-box");
  const confirmDialogIcon = document.getElementById("confirm-dialog-icon");
  const confirmDialogTitle = document.getElementById("confirm-dialog-title");
  const confirmDialogMessage = document.getElementById("confirm-dialog-message");
  const confirmDialogBtnClose = document.getElementById("confirm-dialog-btn-close");
  const confirmDialogCallout = document.getElementById("confirm-dialog-callout");
  const confirmDialogCalloutIcon = document.getElementById("confirm-dialog-callout-icon");
  const confirmDialogCalloutTitle = document.getElementById("confirm-dialog-callout-title");
  const confirmDialogCalloutDesc = document.getElementById("confirm-dialog-callout-desc");
  const confirmDialogBtnCancel = document.getElementById("confirm-dialog-btn-cancel");
  const confirmDialogBtnConfirm = document.getElementById("confirm-dialog-btn-confirm");
  const confirmDialogBtnIcon = document.getElementById("confirm-dialog-btn-icon");
  const confirmDialogBtnLabel = document.getElementById("confirm-dialog-btn-label");

  // Container de Toasts
  const toastContainer = document.getElementById("toast-container");

  // Elementos - Gaveta Flutuante de Nova Prova (Montador Lateral)
  const drawerNewExam = document.getElementById("drawer-new-exam");
  const drawerQuestionsList = document.getElementById("drawer-questions-list");
  const drawerCountBadge = document.getElementById("drawer-count-badge");
  const drawerTotalCount = document.getElementById("drawer-total-count");
  const drawerTotalPoints = document.getElementById("drawer-total-points");
  const btnDrawerClose = document.getElementById("btn-drawer-close");
  const btnDrawerClear = document.getElementById("btn-drawer-clear");
  const btnDrawerCreateExam = document.getElementById("btn-drawer-create-exam");
  const btnDrawerToggleFloating = document.getElementById("btn-drawer-toggle-floating");
  const floatingBadgeCount = document.getElementById("floating-badge-count");
  const mainContentWrapper = document.getElementById("main-content-wrapper");

  // Estado da Gaveta de Questões
  let drawerQuestions = [];
  let drawerUserOpened = false;

  // =========================================================================
  // Inicialização
  // =========================================================================
  init();

  async function init() {
    checkDeviceCompatibility();
    window.addEventListener("resize", checkDeviceCompatibility);

    const isAuthed = await checkAuth();
    if (!isAuthed) return;

    setupTabNavigation();
    setupViewModeSwitcher();
    setupDrawerEvents();
    setupCreateModalEvents();
    setupEmitirModalEvents();
    setupFilters();
    setupBankBnccPicker();
    setupAIQuestionGenerator();
    setupExamBatchSelectionEvents();
    await Promise.all([loadExamsList(), loadBankFilters(), loadBankQuestions(), loadSystemSchools()]);
  }

  // =========================================================================
  // Toasts de Notificação com Material Symbols
  // =========================================================================
  function showToast(message, type = "info") {
    if (!toastContainer) return;
    const toast = document.createElement("div");
    const colors = {
      success: "bg-secondary text-on-secondary shadow-md",
      error: "bg-error text-on-error shadow-md",
      warning: "bg-amber-600 text-white shadow-md",
      info: "bg-inverse-surface text-inverse-on-surface shadow-md"
    };
    const icons = {
      success: "check_circle",
      error: "error",
      warning: "warning",
      info: "info"
    };

    toast.className = `inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold pointer-events-auto transform transition-all duration-300 translate-y-2 opacity-0 ${colors[type] || colors.info}`;
    toast.innerHTML = `
      <span class="material-symbols-outlined text-[18px]">${icons[type] || icons.info}</span>
      <span>${escapeHtml(message)}</span>
    `;
    toastContainer.appendChild(toast);

    requestAnimationFrame(() => {
      toast.classList.remove("translate-y-2", "opacity-0");
    });

    setTimeout(() => {
      toast.classList.add("translate-y-2", "opacity-0");
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  // =========================================================================
  // Modal Moderno de Confirmação (Substituto Visual Elegante para confirm())
  // =========================================================================
  function showModernConfirmDialog({
    title = "Confirmar Ação",
    message = "Deseja continuar com esta operação?",
    calloutTitle = "Banco de Questões Seguro",
    calloutDesc = "Todas as questões e alternativas dessas avaliações permanecerão salvas e seguras no Banco de Questões.",
    calloutIcon = "verified_user",
    calloutType = "preserve", // "preserve" (verde), "danger" (vermelho), "warning" (âmbar), "hidden"
    icon = "delete_sweep",
    iconType = "danger", // "danger" (vermelho), "warning" (âmbar), "primary" (azul)
    confirmText = "Sim, Excluir",
    confirmIcon = "delete",
    cancelText = "Cancelar",
    isDanger = true
  } = {}) {
    return new Promise((resolve) => {
      if (!modalConfirmDialog) {
        resolve(window.confirm(`${title}\n\n${message}`));
        return;
      }

      // Configura os textos dinâmicos
      if (confirmDialogTitle) confirmDialogTitle.textContent = title;
      if (confirmDialogMessage) confirmDialogMessage.textContent = message;
      if (confirmDialogBtnLabel) confirmDialogBtnLabel.textContent = confirmText;
      if (confirmDialogBtnCancel) confirmDialogBtnCancel.textContent = cancelText;
      if (confirmDialogIcon) confirmDialogIcon.textContent = icon;
      if (confirmDialogBtnIcon) confirmDialogBtnIcon.textContent = confirmIcon;

      // Configura estilo visual do ícone principal
      if (confirmDialogIconBox) {
        if (iconType === "danger") {
          confirmDialogIconBox.className = "w-12 h-12 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center border border-rose-100 shadow-xs shrink-0";
        } else if (iconType === "warning") {
          confirmDialogIconBox.className = "w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center border border-amber-100 shadow-xs shrink-0";
        } else {
          confirmDialogIconBox.className = "w-12 h-12 rounded-xl bg-primary-fixed/30 text-primary flex items-center justify-center border border-primary-fixed shadow-xs shrink-0";
        }
      }

      // Configura o callout de alerta / preservação
      if (confirmDialogCallout) {
        if (calloutType === "hidden") {
          confirmDialogCallout.classList.add("hidden");
        } else {
          confirmDialogCallout.classList.remove("hidden");
          if (confirmDialogCalloutIcon) confirmDialogCalloutIcon.textContent = calloutIcon;
          if (confirmDialogCalloutTitle) confirmDialogCalloutTitle.textContent = calloutTitle;
          if (confirmDialogCalloutDesc) confirmDialogCalloutDesc.textContent = calloutDesc;

          if (calloutType === "preserve") {
            confirmDialogCallout.className = "bg-emerald-50 border border-emerald-200/80 rounded-xl p-3.5 flex items-start gap-3 my-2 transition-all";
            if (confirmDialogCalloutIcon) confirmDialogCalloutIcon.className = "material-symbols-outlined text-emerald-600 text-[22px] shrink-0 mt-0.5";
            if (confirmDialogCalloutTitle) confirmDialogCalloutTitle.className = "font-bold text-emerald-950 block mb-0.5";
            if (confirmDialogCalloutDesc) confirmDialogCalloutDesc.className = "text-emerald-800 leading-relaxed block";
          } else if (calloutType === "danger") {
            confirmDialogCallout.className = "bg-rose-50 border border-rose-200/80 rounded-xl p-3.5 flex items-start gap-3 my-2 transition-all";
            if (confirmDialogCalloutIcon) confirmDialogCalloutIcon.className = "material-symbols-outlined text-rose-600 text-[22px] shrink-0 mt-0.5";
            if (confirmDialogCalloutTitle) confirmDialogCalloutTitle.className = "font-bold text-rose-950 block mb-0.5";
            if (confirmDialogCalloutDesc) confirmDialogCalloutDesc.className = "text-rose-800 leading-relaxed block";
          } else if (calloutType === "warning") {
            confirmDialogCallout.className = "bg-amber-50 border border-amber-200/80 rounded-xl p-3.5 flex items-start gap-3 my-2 transition-all";
            if (confirmDialogCalloutIcon) confirmDialogCalloutIcon.className = "material-symbols-outlined text-amber-600 text-[22px] shrink-0 mt-0.5";
            if (confirmDialogCalloutTitle) confirmDialogCalloutTitle.className = "font-bold text-amber-950 block mb-0.5";
            if (confirmDialogCalloutDesc) confirmDialogCalloutDesc.className = "text-amber-800 leading-relaxed block";
          }
        }
      }

      // Configura botão de ação
      if (confirmDialogBtnConfirm) {
        confirmDialogBtnConfirm.disabled = false;
        if (isDanger) {
          confirmDialogBtnConfirm.className = "flex-1 px-5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 active:bg-rose-800 text-white font-bold text-sm shadow-xs hover:shadow transition-all cursor-pointer flex items-center justify-center gap-2";
        } else {
          confirmDialogBtnConfirm.className = "flex-1 px-5 py-2.5 rounded-xl bg-primary-container hover:bg-primary text-white font-bold text-sm shadow-xs hover:shadow transition-all cursor-pointer flex items-center justify-center gap-2";
        }
      }

      let isResolved = false;

      function cleanup() {
        modalConfirmDialog.classList.remove("active");
        confirmDialogBtnClose?.removeEventListener("click", handleCancel);
        confirmDialogBtnCancel?.removeEventListener("click", handleCancel);
        confirmDialogBtnConfirm?.removeEventListener("click", handleConfirm);
        document.removeEventListener("keydown", handleKeydown);
        modalConfirmDialog.removeEventListener("click", handleBackdropClick);
      }

      function handleCancel() {
        if (isResolved) return;
        isResolved = true;
        cleanup();
        resolve(false);
      }

      function handleConfirm() {
        if (isResolved) return;
        isResolved = true;
        cleanup();
        resolve(true);
      }

      function handleKeydown(e) {
        if (e.key === "Escape") {
          e.preventDefault();
          handleCancel();
        }
      }

      function handleBackdropClick(e) {
        if (e.target === modalConfirmDialog) {
          handleCancel();
        }
      }

      confirmDialogBtnClose?.addEventListener("click", handleCancel);
      confirmDialogBtnCancel?.addEventListener("click", handleCancel);
      confirmDialogBtnConfirm?.addEventListener("click", handleConfirm);
      document.addEventListener("keydown", handleKeydown);
      modalConfirmDialog.addEventListener("click", handleBackdropClick);

      modalConfirmDialog.classList.add("active");
      confirmDialogBtnCancel?.focus();
    });
  }

  // =========================================================================
  // Abas de Navegação (Minhas Provas vs Banco de Questões)
  // =========================================================================
  function setupTabNavigation() {
    if (tabBtnExams) {
      tabBtnExams.addEventListener("click", () => switchTab("exams"));
    }
    if (tabBtnBank) {
      tabBtnBank.addEventListener("click", () => switchTab("bank"));
    }
    if (btnGotoBank) {
      btnGotoBank.addEventListener("click", () => switchTab("bank"));
    }
  }

  function switchTab(tab) {
    activeTab = tab;
    if (tab === "exams") {
      tabBtnExams.className = "h-full flex items-center transition-colors px-space-xs text-primary border-b-2 border-primary font-label-lg font-semibold cursor-pointer";
      tabBtnBank.className = "font-label-lg text-on-surface-variant hover:text-on-surface h-full flex items-center transition-colors px-space-xs border-b-2 border-transparent font-medium cursor-pointer";
      panelExams?.classList.remove("hidden");
      panelExams?.classList.add("flex");
      panelBank?.classList.add("hidden");
      panelBank?.classList.remove("flex");

      // O painel lateral e botão flutuante SÓ devem ser exibidos na seção Banco de Questões
      drawerNewExam?.classList.add("hidden");
      drawerNewExam?.classList.remove("flex");
      btnDrawerToggleFloating?.classList.add("hidden");
      btnDrawerToggleFloating?.classList.remove("flex");
      if (mainContentWrapper) {
        mainContentWrapper.style.marginRight = "auto";
        mainContentWrapper.style.maxWidth = "1440px";
      }
    } else {
      tabBtnExams.className = "font-label-lg text-on-surface-variant hover:text-on-surface h-full flex items-center transition-colors px-space-xs border-b-2 border-transparent font-medium cursor-pointer";
      tabBtnBank.className = "h-full flex items-center transition-colors px-space-xs text-primary border-b-2 border-primary font-label-lg font-semibold cursor-pointer";
      panelExams?.classList.add("hidden");
      panelExams?.classList.remove("flex");
      panelBank?.classList.remove("hidden");
      panelBank?.classList.add("flex");

      if (window.renderMathInElement && panelBank) {
        try {
          renderMathInElement(panelBank, {
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

      // Restaura o painel ou botão flutuante na seção Banco de Questões
      if (drawerUserOpened) {
        openDrawer();
      } else if (drawerQuestions.length > 0) {
        btnDrawerToggleFloating?.classList.remove("hidden");
        btnDrawerToggleFloating?.classList.add("flex");
      }
    }
  }

  // =========================================================================
  // Alternador de Visualização: Tabela vs Cards
  // =========================================================================
  function setupViewModeSwitcher() {
    btnViewTable?.addEventListener("click", () => setViewMode("table"));
    btnViewCards?.addEventListener("click", () => setViewMode("cards"));
  }

  function setViewMode(mode) {
    currentViewMode = mode;
    if (mode === "table") {
      btnViewTable.className = "px-space-sm py-1 rounded bg-surface-container-lowest text-primary shadow-xs font-label-sm text-label-sm flex items-center gap-1 font-semibold cursor-pointer transition-all";
      btnViewCards.className = "px-space-sm py-1 rounded text-on-surface-variant hover:text-on-surface font-label-sm text-label-sm flex items-center gap-1 transition-colors cursor-pointer";
      tableExamsContainer?.classList.remove("hidden");
      gridExams?.classList.add("hidden");
      gridExams?.classList.remove("grid");
    } else {
      btnViewTable.className = "px-space-sm py-1 rounded text-on-surface-variant hover:text-on-surface font-label-sm text-label-sm flex items-center gap-1 transition-colors cursor-pointer";
      btnViewCards.className = "px-space-sm py-1 rounded bg-surface-container-lowest text-primary shadow-xs font-label-sm text-label-sm flex items-center gap-1 font-semibold cursor-pointer transition-all";
      tableExamsContainer?.classList.add("hidden");
      gridExams?.classList.remove("hidden");
      gridExams?.classList.add("grid");
    }
  }

  // =========================================================================
  // Carregamento e Renderização de Provas
  // =========================================================================
  async function loadExamsList() {
    try {
      const res = await apiFetch("/api/exam-builder/exams");
      if (res.ok) {
        allExams = await res.json();
        renderExams();
        updateKPIs();
        populateDisciplineFilter();
      }
    } catch (err) {
      console.error("Erro ao carregar avaliações:", err);
      showToast("Não foi possível carregar as avaliações salvas.", "error");
    }
  }

  function updateKPIs() {
    const total = allExams.length;
    if (statTotalExams) statTotalExams.textContent = total;
    if (badgeCountExams) badgeCountExams.textContent = total;
  }

  function populateDisciplineFilter() {
    if (!selectFilterDiscipline) return;
    const disciplines = Array.from(new Set(allExams.map(e => e.discipline).filter(Boolean))).sort();
    const currentVal = selectFilterDiscipline.value;
    selectFilterDiscipline.innerHTML = '<option value="">Disciplina: Todas</option>';
    disciplines.forEach(d => {
      const opt = document.createElement("option");
      opt.value = d;
      opt.textContent = d;
      selectFilterDiscipline.appendChild(opt);
    });
    selectFilterDiscipline.value = currentVal;
  }

  function getExamDisciplineTheme(discipline = "") {
    const disc = discipline.toUpperCase();
    if (disc.includes("MATEM")) {
      return {
        icon: "functions",
        bgIcon: "bg-primary-fixed text-on-primary-fixed",
        badge: "bg-primary-fixed/40 text-primary border border-primary/20",
        accentBar: "bg-primary-container"
      };
    }
    if (disc.includes("PORTUG") || disc.includes("LÍNGUA")) {
      return {
        icon: "menu_book",
        bgIcon: "bg-tertiary-fixed text-tertiary",
        badge: "bg-tertiary-fixed/40 text-tertiary border border-tertiary/20",
        accentBar: "bg-tertiary"
      };
    }
    if (disc.includes("CIÊN") || disc.includes("BIOL") || disc.includes("FÍS")) {
      return {
        icon: "psychology",
        bgIcon: "bg-secondary-container text-secondary",
        badge: "bg-secondary-container/40 text-secondary border border-secondary/20",
        accentBar: "bg-secondary"
      };
    }
    if (disc.includes("HIST") || disc.includes("GEOG")) {
      return {
        icon: "public",
        bgIcon: "bg-amber-100 text-amber-900",
        badge: "bg-amber-50 text-amber-900 border border-amber-200",
        accentBar: "bg-amber-500"
      };
    }
    return {
      icon: "assignment",
      bgIcon: "bg-surface-container-high text-primary",
      badge: "bg-surface-container text-on-surface border border-surface-container-high",
      accentBar: "bg-primary"
    };
  }

  function getExamStatusBadge(exam) {
    const qCount = exam.question_count ?? (exam.questions ? exam.questions.length : 0);
    const status = (exam.status || "").toLowerCase();

    if (status === "completed" || exam.is_graded) {
      return `
        <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-secondary-container text-secondary font-label-sm text-label-sm font-semibold">
          <span class="w-1.5 h-1.5 rounded-full bg-secondary"></span> Concluída
        </span>
      `;
    }
    if (status === "ready" || status === "omr_ready" || qCount >= 5) {
      return `
        <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-surface-container-high text-primary font-label-sm text-label-sm font-semibold">
          <span class="w-1.5 h-1.5 rounded-full bg-primary"></span> OMR Pronto
        </span>
      `;
    }
    return `
      <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-surface-container text-outline font-label-sm text-label-sm font-semibold">
        <span class="w-1.5 h-1.5 rounded-full bg-outline"></span> Em Edição
      </span>
    `;
  }

  function filterExams() {
    const search = (inputSearchExams?.value || "").toLowerCase().trim();
    const disciplineFilter = (selectFilterDiscipline?.value || "").toLowerCase().trim();
    const gradeFilter = (selectFilterGrade?.value || "").toLowerCase().trim();

    return allExams.filter(exam => {
      const titleMatch = (exam.title || "").toLowerCase().includes(search);
      const discMatch = (exam.discipline || "").toLowerCase().includes(search);
      const schoolMatch = (exam.school_name || "").toLowerCase().includes(search);
      const classMatch = (exam.classroom || exam.grade_year || "").toLowerCase().includes(search);
      const textMatches = !search || (titleMatch || discMatch || schoolMatch || classMatch);

      const filterDiscMatches = !disciplineFilter || (exam.discipline || "").toLowerCase() === disciplineFilter;
      const filterGradeMatches = !gradeFilter || (exam.grade_year || "").toLowerCase() === gradeFilter;

      return textMatches && filterDiscMatches && filterGradeMatches;
    });
  }

  function renderExams() {
    const filtered = filterExams();

    if (labelTableCount) {
      labelTableCount.textContent = `${filtered.length} prova${filtered.length !== 1 ? "s" : ""} exibida${filtered.length !== 1 ? "s" : ""}`;
    }

    if (filtered.length === 0) {
      tableExamsContainer?.classList.add("hidden");
      gridExams?.classList.add("hidden");
      emptyExamsState?.classList.remove("hidden");
      emptyExamsState?.classList.add("flex");
      return;
    }

    emptyExamsState?.classList.add("hidden");
    emptyExamsState?.classList.remove("flex");

    // Mantém o modo de visualização atual
    if (currentViewMode === "table") {
      tableExamsContainer?.classList.remove("hidden");
      gridExams?.classList.add("hidden");
      gridExams?.classList.remove("grid");
    } else {
      tableExamsContainer?.classList.add("hidden");
      gridExams?.classList.remove("hidden");
      gridExams?.classList.add("grid");
    }

    renderTableRows(filtered);
    renderCards(filtered);
    updateExamSelectionUI();
  }

  // =========================================================================
  // Seleção em Massa de Avaliações (Batch Selection)
  // =========================================================================
  function setupExamBatchSelectionEvents() {
    if (chkSelectAllExams) {
      chkSelectAllExams.addEventListener("change", () => {
        const filtered = filterExams();
        if (chkSelectAllExams.checked) {
          filtered.forEach(e => selectedExamIds.add(e.id));
        } else {
          filtered.forEach(e => selectedExamIds.delete(e.id));
        }
        updateExamSelectionUI();
      });
    }

    if (btnBatchClearSelection) {
      btnBatchClearSelection.addEventListener("click", () => {
        selectedExamIds.clear();
        updateExamSelectionUI();
      });
    }

    if (btnBatchDeleteExams) {
      btnBatchDeleteExams.addEventListener("click", confirmBatchDeleteExams);
    }
  }

  function updateExamSelectionUI() {
    const filtered = filterExams();
    const visibleCount = filtered.length;
    const selectedCount = selectedExamIds.size;

    if (labelBatchSelectedCount) {
      labelBatchSelectedCount.textContent = `${selectedCount} avaliação${selectedCount !== 1 ? "ões" : ""} selecionada${selectedCount !== 1 ? "s" : ""}`;
    }

    if (barBatchActions) {
      if (selectedCount > 0) {
        barBatchActions.classList.remove("hidden");
        barBatchActions.classList.add("flex");
      } else {
        barBatchActions.classList.add("hidden");
        barBatchActions.classList.remove("flex");
      }
    }

    if (chkSelectAllExams) {
      if (visibleCount > 0 && selectedCount >= visibleCount && filtered.every(e => selectedExamIds.has(e.id))) {
        chkSelectAllExams.checked = true;
        chkSelectAllExams.indeterminate = false;
      } else if (selectedCount > 0) {
        chkSelectAllExams.checked = false;
        chkSelectAllExams.indeterminate = true;
      } else {
        chkSelectAllExams.checked = false;
        chkSelectAllExams.indeterminate = false;
      }
    }

    // Sincroniza checkboxes e classes visuais nas linhas da tabela
    document.querySelectorAll(".chk-exam-row").forEach(chk => {
      const eId = chk.getAttribute("data-exam-id");
      const isChecked = selectedExamIds.has(eId);
      chk.checked = isChecked;
      const tr = chk.closest("tr");
      if (tr) {
        if (isChecked) {
          tr.classList.add("bg-primary-fixed/20");
        } else {
          tr.classList.remove("bg-primary-fixed/20");
        }
      }
    });

    // Sincroniza checkboxes e destaques visuais nos cards
    document.querySelectorAll(".chk-exam-card").forEach(chk => {
      const eId = chk.getAttribute("data-exam-id");
      const isChecked = selectedExamIds.has(eId);
      chk.checked = isChecked;
      const card = chk.closest(".exam-card-item");
      if (card) {
        if (isChecked) {
          card.classList.add("border-primary", "ring-2", "ring-primary/40", "bg-primary-fixed/5");
        } else {
          card.classList.remove("border-primary", "ring-2", "ring-primary/40", "bg-primary-fixed/5");
        }
      }
    });
  }

  async function confirmBatchDeleteExams() {
    if (selectedExamIds.size === 0) return;
    const count = selectedExamIds.size;
    const confirmed = await showModernConfirmDialog({
      title: `Excluir ${count} Avaliações Selecionadas`,
      message: `Tem certeza que deseja excluir as ${count} avaliações selecionadas da sua listagem?`,
      calloutTitle: "Banco de Questões Preservado",
      calloutDesc: "Todas as questões e alternativas dessas avaliações permanecerão salvas e seguras no Banco de Questões. Elas só poderão ser excluídas se você as apagar diretamente no banco.",
      calloutIcon: "verified_user",
      calloutType: "preserve",
      icon: "delete_sweep",
      iconType: "danger",
      confirmText: `Excluir ${count} Avaliaç${count > 1 ? 'ões' : 'ão'}`,
      confirmIcon: "delete_sweep",
      cancelText: "Cancelar",
      isDanger: true
    });
    if (!confirmed) return;

    showToast(`Excluindo ${count} avaliações...`, "info");
    try {
      const res = await apiFetch("/api/exam-builder/exams/batch-delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ exam_ids: Array.from(selectedExamIds) })
      });
      if (res.ok) {
        const data = await res.json();
        showToast(`${data.deleted_count || count} avaliações excluídas! As questões continuam salvas no Banco.`, "success");
        selectedExamIds.clear();
        await loadExamsList();
        await loadBankQuestions();
      } else {
        showToast("Falha ao excluir avaliações em lote.", "error");
      }
    } catch (err) {
      showToast("Erro de conexão ao excluir avaliações.", "error");
    }
  }

  // Renderiza Linhas da Tabela (Design Stitch)
  function renderTableRows(exams) {
    if (!tbodyExams) return;
    tbodyExams.innerHTML = "";

    exams.forEach(exam => {
      const isChecked = selectedExamIds.has(exam.id);
      const tr = document.createElement("tr");
      tr.className = `hover:bg-surface-container-low/40 transition-colors border-b border-surface-container-low/60 ${isChecked ? 'bg-primary-fixed/20' : ''}`;

      const theme = getExamDisciplineTheme(exam.discipline);
      const disc = exam.discipline || "GERAL";
      const qCount = exam.question_count ?? (exam.questions ? exam.questions.length : 0);
      const maxScore = (parseFloat(exam.max_score) || 10.0).toFixed(1).replace(".", ",");
      const updatedDate = exam.updated_at ? new Date(exam.updated_at).toLocaleDateString("pt-BR") : (exam.exam_date || "Recente");
      const statusBadge = getExamStatusBadge(exam);

      tr.innerHTML = `
        <td class="py-3.5 px-4 text-center w-12">
          <input type="checkbox" class="chk-exam-row w-4 h-4 rounded text-primary focus:ring-primary/30 border-outline-variant cursor-pointer align-middle" data-exam-id="${exam.id}" ${isChecked ? 'checked' : ''} title="Selecionar avaliação">
        </td>
        <td class="py-3.5 px-4">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl ${theme.bgIcon} flex items-center justify-center flex-shrink-0 shadow-xs">
              <span class="material-symbols-outlined text-[19px]">${theme.icon}</span>
            </div>
            <div class="flex items-center gap-2 min-w-0 flex-wrap">
              <span class="text-sm font-semibold text-on-surface truncate">${escapeHtml(exam.title || "Avaliação Sem Título")}</span>
              <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold ${theme.badge}">
                ${escapeHtml(disc)}
              </span>
              ${exam.grade_year ? `<span class="inline-flex items-center px-1.5 py-0.5 rounded-md text-[11px] font-medium bg-surface-container text-on-surface-variant">${escapeHtml(exam.grade_year)}</span>` : ""}
            </div>
          </div>
        </td>
        <td class="py-3.5 px-4 w-44 sm:w-52">
          <div class="flex items-center gap-1.5">
            <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-surface-container-low text-on-surface text-xs font-semibold">
              <span class="material-symbols-outlined text-[14px] text-outline">quiz</span>
              ${qCount} questõ${qCount === 1 ? "ão" : "es"}
            </span>
            <span class="inline-flex items-center px-2 py-1 rounded-lg bg-secondary-container/60 text-secondary text-xs font-bold">
              ${maxScore} pts
            </span>
          </div>
        </td>
        <td class="py-3.5 px-5 text-right w-44">
          <div class="flex items-center justify-end gap-1">
            <a href="/elaborador?exam_id=${exam.id}" class="w-8 h-8 rounded-lg flex items-center justify-center text-primary hover:bg-surface-container-high transition-colors" title="Editar Avaliação">
              <span class="material-symbols-outlined text-[18px]">edit</span>
            </a>
            <button class="btn-table-gabarito w-8 h-8 rounded-lg flex items-center justify-center text-emerald-600 hover:bg-emerald-50 hover:text-emerald-700 transition-colors cursor-pointer relative" title="${exam.is_gabarito_outdated ? 'Atenção: Prova alterada após gerar gabarito OMR. Clique para atualizar!' : 'Gerar / Sincronizar Gabarito OMR no Sistema de Correção'}">
              <span class="material-symbols-outlined text-[18px]">fact_check</span>
              ${exam.is_gabarito_outdated ? `<span class="absolute -top-1 -right-1 w-2.5 h-2.5 bg-amber-500 rounded-full animate-pulse border border-white" title="Gabarito OMR desatualizado"></span>` : ''}
            </button>
            <button class="btn-table-emitir w-8 h-8 rounded-lg flex items-center justify-center text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-colors cursor-pointer" title="Imprimir / Baixar (PDF/DOCX)">
              <span class="material-symbols-outlined text-[18px]">print</span>
            </button>
            <button class="btn-table-duplicate w-8 h-8 rounded-lg flex items-center justify-center text-on-surface-variant hover:bg-surface-container hover:text-primary transition-colors cursor-pointer" title="Duplicar Prova">
              <span class="material-symbols-outlined text-[18px]">content_copy</span>
            </button>
            <button class="btn-table-delete w-8 h-8 rounded-lg flex items-center justify-center text-outline hover:bg-error-container hover:text-error transition-colors cursor-pointer" title="Excluir Avaliação">
              <span class="material-symbols-outlined text-[18px]">delete</span>
            </button>
          </div>
        </td>
      `;

      tr.querySelector(".chk-exam-row")?.addEventListener("change", (e) => {
        e.stopPropagation();
        if (e.target.checked) {
          selectedExamIds.add(exam.id);
        } else {
          selectedExamIds.delete(exam.id);
        }
        updateExamSelectionUI();
      });

      tr.querySelector(".btn-table-gabarito")?.addEventListener("click", () => openSyncGabaritoModal(exam));
      tr.querySelector(".btn-table-emitir")?.addEventListener("click", () => openEmitirModal(exam));
      tr.querySelector(".btn-table-duplicate")?.addEventListener("click", () => duplicateExam(exam.id));
      tr.querySelector(".btn-table-delete")?.addEventListener("click", () => confirmDeleteExam(exam));

      tbodyExams.appendChild(tr);
    });
  }

  // Renderiza Grid de Cards (Design Stitch Moderno)
  function renderCards(exams) {
    if (!gridExams) return;
    gridExams.innerHTML = "";

    exams.forEach(exam => {
      const isChecked = selectedExamIds.has(exam.id);
      const card = document.createElement("div");
      card.className = `exam-card-item bg-white rounded-2xl border ${isChecked ? 'border-primary ring-2 ring-primary/40 bg-primary-fixed/5' : 'border-surface-container'} p-5 flex flex-col justify-between hover:shadow-lg hover:border-primary/40 hover:-translate-y-1 transition-all duration-200 relative group overflow-hidden shadow-xs`;

      const theme = getExamDisciplineTheme(exam.discipline);
      const disc = exam.discipline || "GERAL";
      const grade = exam.grade_year || "9º ANO";
      const qCount = exam.question_count ?? (exam.questions ? exam.questions.length : 0);
      const maxScore = (parseFloat(exam.max_score) || 10.0).toFixed(1).replace(".", ",");
      const updatedDate = exam.updated_at ? new Date(exam.updated_at).toLocaleDateString("pt-BR") : (exam.exam_date || "Recente");

      card.innerHTML = `
        <!-- Barra colorida no topo do card -->
        <div class="absolute top-0 left-0 right-0 h-1.5 ${theme.accentBar}"></div>

        <div class="pt-1">
          <!-- Topo do Card: Checkbox + Ícone da Disciplina + Badges + Data -->
          <div class="flex items-center justify-between gap-2 mb-3">
            <div class="flex items-center gap-2 flex-wrap">
              <input type="checkbox" class="chk-exam-card w-4 h-4 rounded text-primary focus:ring-primary/30 border-outline-variant cursor-pointer align-middle shrink-0" data-exam-id="${exam.id}" ${isChecked ? 'checked' : ''} title="Selecionar avaliação">
              <div class="w-8 h-8 rounded-lg ${theme.bgIcon} flex items-center justify-center shadow-xs shrink-0">
                <span class="material-symbols-outlined text-[18px]">${theme.icon}</span>
              </div>
              <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-bold ${theme.badge}">
                ${escapeHtml(disc)}
              </span>
              <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-surface-container text-on-surface-variant">
                ${escapeHtml(grade)}
              </span>
            </div>
            <span class="text-[11px] font-medium text-outline flex items-center gap-1 shrink-0">
              <span class="material-symbols-outlined text-[13px]">calendar_today</span>
              ${updatedDate}
            </span>
          </div>

          <!-- Título da Avaliação -->
          <h3 class="font-headline-md text-[15px] font-bold text-on-surface line-clamp-2 leading-snug group-hover:text-primary transition-colors mb-2" title="${escapeHtml(exam.title || '')}">
            ${escapeHtml(exam.title || "Avaliação Sem Título")}
          </h3>

          <!-- Escola e Turma -->
          <div class="flex items-center gap-1.5 text-xs text-on-surface-variant mb-4 line-clamp-1">
            <span class="material-symbols-outlined text-[16px] text-outline shrink-0">domain</span>
            <span class="truncate">${escapeHtml(exam.school_name || "SEMED Canoa")}</span>
            ${exam.classroom ? `<span class="text-outline">•</span><span class="font-semibold text-primary shrink-0">${escapeHtml(exam.classroom)}</span>` : ""}
          </div>
        </div>

        <div>
          <!-- Cápsula de Métricas da Prova -->
          <div class="bg-surface-container-low/70 border border-surface-container rounded-xl p-2.5 flex items-center justify-between text-xs mb-4">
            <div class="flex items-center gap-1.5 font-semibold text-on-surface">
              <span class="material-symbols-outlined text-primary text-[18px]">format_list_numbered</span>
              <span>${qCount} ${qCount === 1 ? "Questão" : "Questões"}</span>
            </div>
            <div class="flex items-center gap-1.5 font-bold text-on-surface">
              <span class="text-on-surface-variant font-normal text-[11px]">Valor:</span>
              <span class="px-2 py-0.5 rounded-md bg-secondary-container/80 text-secondary text-xs font-bold">${maxScore} pts</span>
            </div>
          </div>

          <!-- Barra de Ações com Botões Equilibrados -->
          <div class="flex items-center gap-1.5 pt-3 border-t border-surface-container">
            <a href="/elaborador?exam_id=${exam.id}" class="flex-1 inline-flex items-center justify-center gap-1.5 h-9 px-3 rounded-xl font-label-md text-xs font-bold bg-primary-container text-on-primary hover:bg-primary transition-all shadow-xs cursor-pointer" title="Abrir Editor">
              <span class="material-symbols-outlined text-[16px]">edit</span>
              <span>Editar</span>
            </a>

            <button class="btn-card-gabarito w-9 h-9 flex items-center justify-center text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50 rounded-xl border border-emerald-200/80 transition-colors cursor-pointer shrink-0 relative" title="${exam.is_gabarito_outdated ? 'Atenção: Prova alterada após gerar gabarito OMR. Clique para atualizar!' : 'Gerar / Sincronizar Gabarito OMR no Sistema'}">
              <span class="material-symbols-outlined text-[17px]">fact_check</span>
              ${exam.is_gabarito_outdated ? `<span class="absolute -top-1 -right-1 w-2.5 h-2.5 bg-amber-500 rounded-full animate-pulse border border-white" title="Gabarito OMR desatualizado"></span>` : ''}
            </button>

            <button class="btn-card-emitir w-9 h-9 flex items-center justify-center text-on-surface-variant hover:text-on-surface hover:bg-surface-container rounded-xl border border-surface-container transition-colors cursor-pointer shrink-0" title="Emitir Prova (PDF/Word)">
              <span class="material-symbols-outlined text-[17px]">print</span>
            </button>

            <button class="btn-card-duplicate w-9 h-9 flex items-center justify-center text-on-surface-variant hover:text-primary hover:bg-surface-container rounded-xl border border-surface-container transition-colors cursor-pointer shrink-0" title="Duplicar Avaliação">
              <span class="material-symbols-outlined text-[17px]">content_copy</span>
            </button>

            <button class="btn-card-delete w-9 h-9 flex items-center justify-center text-outline hover:text-error hover:bg-error-container rounded-xl border border-surface-container transition-colors cursor-pointer shrink-0" title="Excluir Avaliação">
              <span class="material-symbols-outlined text-[17px]">delete</span>
            </button>
          </div>
        </div>
      `;

      card.querySelector(".chk-exam-card")?.addEventListener("change", (e) => {
        e.stopPropagation();
        if (e.target.checked) {
          selectedExamIds.add(exam.id);
        } else {
          selectedExamIds.delete(exam.id);
        }
        updateExamSelectionUI();
      });

      card.querySelector(".btn-card-gabarito")?.addEventListener("click", () => openSyncGabaritoModal(exam));
      card.querySelector(".btn-card-duplicate")?.addEventListener("click", () => duplicateExam(exam.id));
      card.querySelector(".btn-card-emitir")?.addEventListener("click", () => openEmitirModal(exam));
      card.querySelector(".btn-card-delete")?.addEventListener("click", () => confirmDeleteExam(exam));

      gridExams.appendChild(card);
    });
  }

  // =========================================================================
  // Ações de Prova: Duplicar e Excluir
  // =========================================================================
  async function duplicateExam(examId) {
    showToast("Duplicando avaliação e questões...", "info");
    try {
      const res = await apiFetch(`/api/exam-builder/exams/${examId}/duplicate`, { method: "POST" });
      if (res.ok) {
        showToast("Avaliação duplicada com sucesso!", "success");
        await loadExamsList();
      } else {
        showToast("Falha ao duplicar avaliação.", "error");
      }
    } catch (err) {
      showToast("Erro de rede ao duplicar.", "error");
    }
  }

  async function confirmDeleteExam(exam) {
    const confirmed = await showModernConfirmDialog({
      title: "Excluir Avaliação",
      message: `Tem certeza que deseja excluir a avaliação "${exam.title}" da sua listagem?`,
      calloutTitle: "Banco de Questões Preservado",
      calloutDesc: "As questões desta avaliação permanecerão salvas e seguras no Banco de Questões para serem reutilizadas quando desejar.",
      calloutIcon: "verified_user",
      calloutType: "preserve",
      icon: "delete",
      iconType: "danger",
      confirmText: "Sim, Excluir Prova",
      confirmIcon: "delete",
      cancelText: "Cancelar",
      isDanger: true
    });
    if (!confirmed) return;

    showToast("Excluindo avaliação...", "info");
    try {
      const res = await apiFetch(`/api/exam-builder/exams/${exam.id}`, { method: "DELETE" });
      if (res.ok) {
        showToast("Avaliação excluída com sucesso! As questões continuam salvas no Banco.", "success");
        selectedExamIds.delete(exam.id);
        await loadExamsList();
        await loadBankQuestions();
      } else {
        showToast("Falha ao excluir avaliação.", "error");
      }
    } catch (err) {
      showToast("Erro ao conectar ao servidor.", "error");
    }
  }

  // =========================================================================
  // Modal: Configurar e Gerar Gabarito OMR no Sistema de Correção (Simplificado)
  // =========================================================================
  let currentSyncExam = null;
  const modalSyncGabarito = document.getElementById("modal-sync-gabarito");
  const btnCloseSyncGabarito = document.getElementById("btn-close-sync-gabarito");
  const btnCancelSyncGabarito = document.getElementById("btn-cancel-sync-gabarito");
  const btnConfirmSyncGabarito = document.getElementById("btn-confirm-sync-gabarito");
  const syncGabaritoBtnLabel = document.getElementById("sync-gabarito-btn-label");
  const syncGabaritoTitleInput = document.getElementById("sync-gabarito-input-title");
  const syncGabaritoSubtitleInput = document.getElementById("sync-gabarito-input-subtitle");
  const syncGabaritoSchoolInput = document.getElementById("sync-gabarito-input-school");
  const syncGabaritoClassroomInput = document.getElementById("sync-gabarito-input-classroom");
  const syncGabaritoShiftSelect = document.getElementById("sync-gabarito-select-shift");
  const syncGabaritoCoverTitleInput = document.getElementById("sync-gabarito-cover-title");
  const syncGabaritoCoverSubtitleInput = document.getElementById("sync-gabarito-cover-subtitle");
  const syncGabaritoCoverInstructionsInput = document.getElementById("sync-gabarito-cover-instructions");
  const syncGabaritoStatusBadge = document.getElementById("sync-gabarito-status-badge");
  const syncGabaritoMissingAlert = document.getElementById("sync-gabarito-missing-alert");
  const syncGabaritoMissingDesc = document.getElementById("sync-gabarito-missing-desc");
  const syncGabaritoWarningAlert = document.getElementById("sync-gabarito-warning-alert");
  const syncGabaritoWarningDesc = document.getElementById("sync-gabarito-warning-desc");
  const syncGabaritoQCountBadge = document.getElementById("sync-gabarito-qcount-badge");
  const syncGabaritoPagesBadge = document.getElementById("sync-gabarito-pages-badge");
  const syncGabaritoPageCountInput = document.getElementById("sync-gabarito-input-page-count");

  // Modal Sucesso
  const modalSyncGabaritoSuccess = document.getElementById("modal-sync-gabarito-success");
  const syncSuccessMessage = document.getElementById("sync-success-message");
  const syncSuccessExamTitle = document.getElementById("sync-success-exam-title");
  const syncSuccessQuestionsCount = document.getElementById("sync-success-questions-count");
  const syncSuccessCoverName = document.getElementById("sync-success-cover-name");
  const syncSuccessBtnPdf = document.getElementById("sync-success-btn-pdf");
  const syncSuccessBtnClose = document.getElementById("sync-success-btn-close");

  const COVER_NAMES = {
    "opcao_4_azul_nautico_lagoa": "Opção 4: Lagoa Serena & Náutico Real (Oficial 2026)",
    "opcao_1_montanhas_canoa": "Opção 1: Montanhas de Canoa (Navy & Ouro)",
    "opcao_2_rio_verde_petroleo": "Opção 2: Rio São Francisco (Verde Petróleo)",
    "opcao_3_por_do_sol_solar": "Opção 3: Pôr do Sol Solar (Laranja & Âmbar)"
  };

  function updateCoverRadiosVisual() {
    const radios = document.querySelectorAll('input[name="sync_cover_model"]');
    radios.forEach(r => {
      const label = r.closest(".cover-card-label");
      if (!label) return;
      if (r.checked) {
        label.classList.add("border-emerald-500", "bg-emerald-50/40");
        label.classList.remove("border-slate-200", "bg-white");
      } else {
        label.classList.remove("border-emerald-500", "bg-emerald-50/40");
        label.classList.add("border-slate-200", "bg-white");
      }
    });
  }

  document.querySelectorAll('input[name="sync_cover_model"]').forEach(r => {
    r.addEventListener("change", updateCoverRadiosVisual);
  });

  function normalizeShift(val) {
    if (!val) return "MANHÃ";
    const s = String(val).trim().toUpperCase();
    if (s.includes("MAT") || s.includes("MANH")) return "MANHÃ";
    if (s.includes("VESP") || s.includes("TARD")) return "TARDE";
    if (s.includes("NOT") || s.includes("NOIT")) return "NOITE";
    if (s.includes("INTEG")) return "INTEGRAL";
    return "MANHÃ";
  }

  async function openSyncGabaritoModal(exam) {
    if (!exam || !exam.id) return;
    currentSyncExam = exam;

    // Reset visual
    if (syncGabaritoTitleInput) syncGabaritoTitleInput.value = exam.title || "Avaliação";
    if (syncGabaritoSubtitleInput) syncGabaritoSubtitleInput.value = exam.subtitle || exam.grade_year || "ENSINO FUNDAMENTAL";
    if (syncGabaritoSchoolInput) syncGabaritoSchoolInput.value = exam.school_name || "SEMED - LAGOA DA CANOA";
    if (syncGabaritoClassroomInput) syncGabaritoClassroomInput.value = exam.classroom || "";
    if (syncGabaritoShiftSelect) syncGabaritoShiftSelect.value = normalizeShift(exam.shift);
    if (syncGabaritoCoverTitleInput) syncGabaritoCoverTitleInput.value = "PROVA CANOA";
    if (syncGabaritoCoverSubtitleInput) syncGabaritoCoverSubtitleInput.value = exam.discipline || "AVALIAÇÃO DIAGNÓSTICA MUNICIPAL";
    if (syncGabaritoQCountBadge) {
      const qc = exam.question_count ?? (exam.questions ? exam.questions.length : 0);
      syncGabaritoQCountBadge.textContent = `${qc} ${qc === 1 ? 'Questão' : 'Questões'}`;
    }

    if (syncGabaritoMissingAlert) syncGabaritoMissingAlert.classList.add("hidden");
    if (syncGabaritoWarningAlert) syncGabaritoWarningAlert.classList.add("hidden");
    if (syncGabaritoStatusBadge) syncGabaritoStatusBadge.classList.add("hidden");
    if (btnConfirmSyncGabarito) {
      btnConfirmSyncGabarito.disabled = false;
      if (syncGabaritoBtnLabel) syncGabaritoBtnLabel.textContent = "Criar Gabarito Completo";
    }

    // Exibe modal com loading suave dos dados atualizados
    if (modalSyncGabarito) modalSyncGabarito.classList.add("active");

    try {
      const res = await apiFetch(`/api/exam-builder/exams/${exam.id}/grading-status`);
      if (res.ok) {
        const st = await res.json();
        
        if (syncGabaritoTitleInput) syncGabaritoTitleInput.value = st.title || exam.title;
        if (syncGabaritoSubtitleInput) syncGabaritoSubtitleInput.value = st.subtitle || st.grade_year || exam.grade_year || "ENSINO FUNDAMENTAL";
        if (syncGabaritoSchoolInput) syncGabaritoSchoolInput.value = st.school_name || exam.school_name || "SEMED - LAGOA DA CANOA";
        if (syncGabaritoClassroomInput) syncGabaritoClassroomInput.value = st.classroom || exam.classroom || "";
        if (syncGabaritoShiftSelect) syncGabaritoShiftSelect.value = normalizeShift(st.shift || exam.shift);
        if (syncGabaritoCoverTitleInput) syncGabaritoCoverTitleInput.value = st.cover_title || "PROVA CANOA";
        if (syncGabaritoCoverSubtitleInput) syncGabaritoCoverSubtitleInput.value = st.cover_subtitle || st.discipline || "AVALIAÇÃO DIAGNÓSTICA MUNICIPAL";
        if (syncGabaritoCoverInstructionsInput) syncGabaritoCoverInstructionsInput.value = st.cover_instructions || "1. Preencha completamente o círculo da resposta correta.\n2. Utilize caneta esferográfica azul ou preta.\n3. Não dobre, rasure ou molhe esta folha de respostas.";
        
        if (syncGabaritoQCountBadge) {
          syncGabaritoQCountBadge.textContent = `${st.num_questions} ${st.num_questions === 1 ? 'Questão' : 'Questões'}`;
        }
        if (st.page_count) {
          if (syncGabaritoPageCountInput) syncGabaritoPageCountInput.value = st.page_count;
          if (syncGabaritoPagesBadge) {
            syncGabaritoPagesBadge.textContent = `${st.page_count} ${st.page_count === 1 ? 'Página' : 'Páginas'}`;
          }
        }

        // Marca o modelo de capa
        const modelToSelect = st.cover_model || "opcao_4_azul_nautico_lagoa";
        const radio = document.querySelector(`input[name="sync_cover_model"][value="${modelToSelect}"]`);
        if (radio) {
          radio.checked = true;
          updateCoverRadiosVisual();
        }

        // Validação Edge Case 1: Questões sem resposta correta
        if (st.missing_correct_questions && st.missing_correct_questions.length > 0) {
          const listStr = st.missing_correct_questions.join(", ");
          if (syncGabaritoMissingAlert) syncGabaritoMissingAlert.classList.remove("hidden");
          if (syncGabaritoMissingDesc) {
            syncGabaritoMissingDesc.innerHTML = `As seguintes questões estão sem alternativa correta definida no elaborador: <strong>Questão ${escapeHtml(listStr)}</strong>.`;
          }
          if (btnConfirmSyncGabarito) {
            btnConfirmSyncGabarito.disabled = true;
            if (syncGabaritoBtnLabel) syncGabaritoBtnLabel.textContent = "Marque as Respostas no Elaborador";
          }
        } else {
          if (syncGabaritoMissingAlert) syncGabaritoMissingAlert.classList.add("hidden");
          if (btnConfirmSyncGabarito) btnConfirmSyncGabarito.disabled = false;

          // Se já tem gabarito vinculado
          if (st.has_linked_exam) {
            if (syncGabaritoStatusBadge) syncGabaritoStatusBadge.classList.remove("hidden");
            if (syncGabaritoWarningAlert) syncGabaritoWarningAlert.classList.remove("hidden");
            if (syncGabaritoWarningDesc) {
              if (st.submissions_count > 0) {
                syncGabaritoWarningDesc.textContent = `Esta avaliação já possui um gabarito vinculado com ${st.submissions_count} correções registradas. A sincronização atualizará as respostas oficiais no sistema de correção mantendo o histórico.`;
              } else {
                syncGabaritoWarningDesc.textContent = `Esta avaliação já possui um gabarito vinculado no sistema de correção. Confirmar atualizará as respostas e regenerará a folha OMR com a capa selecionada.`;
              }
            }
            if (syncGabaritoBtnLabel) syncGabaritoBtnLabel.textContent = "Atualizar Gabarito Oficial";
          } else {
            if (syncGabaritoStatusBadge) syncGabaritoStatusBadge.classList.add("hidden");
            if (syncGabaritoWarningAlert) syncGabaritoWarningAlert.classList.add("hidden");
            if (syncGabaritoBtnLabel) syncGabaritoBtnLabel.textContent = "Criar Gabarito Completo";
          }
        }
      }
    } catch (err) {
      console.warn("Erro ao carregar status do gabarito:", err);
    }
  }

  function closeSyncGabaritoModal() {
    if (modalSyncGabarito) modalSyncGabarito.classList.remove("active");
    currentSyncExam = null;
  }

  async function handleConfirmSyncGabarito() {
    const previousLabel = syncGabaritoBtnLabel ? syncGabaritoBtnLabel.textContent : "Criar Gabarito Completo";

    try {
      if (!currentSyncExam || !currentSyncExam.id) {
        showToast("Nenhuma avaliação selecionada para sincronizar gabarito.", "warning");
        return;
      }
      if (btnConfirmSyncGabarito && btnConfirmSyncGabarito.disabled) return;

      const selectedModel = document.querySelector('input[name="sync_cover_model"]:checked')?.value || "opcao_4_azul_nautico_lagoa";
      const rawPageCount = syncGabaritoPageCountInput ? parseInt(syncGabaritoPageCountInput.value, 10) : 1;
      const finalPageCount = (!isNaN(rawPageCount) && rawPageCount > 0) ? rawPageCount : 1;

      const payload = {
        title: syncGabaritoTitleInput?.value?.trim() || currentSyncExam.title || "Avaliação",
        subtitle: syncGabaritoSubtitleInput?.value?.trim() || "",
        school_name: currentSyncExam.school_name || "",
        classroom: syncGabaritoClassroomInput?.value?.trim() || "",
        shift: normalizeShift(syncGabaritoShiftSelect?.value),
        page_count: finalPageCount,
        cover_model: selectedModel,
        cover_title: syncGabaritoCoverTitleInput?.value?.trim() || "PROVA CANOA",
        cover_subtitle: syncGabaritoCoverSubtitleInput?.value?.trim() || "",
        cover_instructions: syncGabaritoCoverInstructionsInput?.value?.trim() || ""
      };

      if (btnConfirmSyncGabarito) {
        btnConfirmSyncGabarito.disabled = true;
        if (syncGabaritoBtnLabel) syncGabaritoBtnLabel.textContent = "Gerando Gabarito OMR & Capa...";
      }

      const res = await apiFetch(`/api/exam-builder/exams/${currentSyncExam.id}/create-grading-exam`, {
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

      // Abre Modal de Sucesso (Edge Case 2 - Opção A)
      if (modalSyncGabaritoSuccess) {
        if (syncSuccessExamTitle) syncSuccessExamTitle.textContent = result.title || payload.title;
        if (syncSuccessQuestionsCount) syncSuccessQuestionsCount.textContent = `${result.num_questions || 'Várias'} questões oficiais`;
        if (syncSuccessCoverName) syncSuccessCoverName.textContent = COVER_NAMES[result.cover_model] || result.cover_model;
        if (syncSuccessBtnPdf) {
          syncSuccessBtnPdf.href = result.pdf_url || `/storage/sheets/exam_${result.exam_id}.pdf`;
        }
        if (syncSuccessMessage) {
          syncSuccessMessage.textContent = result.is_update 
            ? "O gabarito oficial e a folha OMR foram atualizados e sincronizados com a capa escolhida."
            : "O gabarito foi criado e vinculado com sucesso no sistema de correção. A folha de respostas OMR está pronta para impressão!";
        }
        modalSyncGabaritoSuccess.classList.add("active");
      }

      await loadExamsList();
    } catch (err) {
      console.error("Erro ao sincronizar gabarito:", err);
      showToast(err.message || "Erro ao conectar ao servidor.", "error");
      if (btnConfirmSyncGabarito) {
        btnConfirmSyncGabarito.disabled = false;
        if (syncGabaritoBtnLabel) syncGabaritoBtnLabel.textContent = previousLabel || "Atualizar Gabarito Oficial";
      }
    }
  }

  btnCloseSyncGabarito?.addEventListener("click", closeSyncGabaritoModal);
  btnCancelSyncGabarito?.addEventListener("click", closeSyncGabaritoModal);
  btnConfirmSyncGabarito?.addEventListener("click", handleConfirmSyncGabarito);
  syncSuccessBtnClose?.addEventListener("click", () => {
    modalSyncGabaritoSuccess?.classList.remove("active");
  });

  modalSyncGabarito?.addEventListener("click", (e) => {
    if (e.target === modalSyncGabarito) closeSyncGabaritoModal();
  });
  modalSyncGabaritoSuccess?.addEventListener("click", (e) => {
    if (e.target === modalSyncGabaritoSuccess) modalSyncGabaritoSuccess.classList.remove("active");
  });

  // =========================================================================
  // Banco de Questões: Filtros e Listagem
  // =========================================================================
  async function loadBankFilters() {
    try {
      const res = await apiFetch("/api/exam-builder/bank/filters");
      if (res.ok) {
        const data = await res.json();
        const total = data.total_questions || 0;
        if (statTotalQuestions) statTotalQuestions.textContent = total;
        if (badgeCountQuestions) badgeCountQuestions.textContent = total;

        if (bankSelectDiscipline) {
          bankSelectDiscipline.innerHTML = '<option value="">Todas as Disciplinas</option>';
          (data.disciplines || []).forEach(d => {
            const opt = document.createElement("option");
            opt.value = d;
            opt.textContent = d;
            bankSelectDiscipline.appendChild(opt);
          });
        }

        if (bankSelectGrade) {
          bankSelectGrade.innerHTML = '<option value="">Todos os Anos</option>';
          (data.grades || []).forEach(g => {
            const opt = document.createElement("option");
            opt.value = g;
            opt.textContent = g;
            bankSelectGrade.appendChild(opt);
          });
        }
      }
    } catch (err) {
      console.error("Erro ao carregar filtros do banco:", err);
    }
  }

  async function loadBankQuestions(reset = true) {
    if (reset) {
      bankCurrentOffset = 0;
      bankQuestions = [];
      bankHasMore = true;
      if (listBankQuestions) listBankQuestions.innerHTML = "";
      if (bankScrollEnd) bankScrollEnd.classList.add("hidden");
    }

    if (bankIsLoading || (!reset && !bankHasMore)) return;
    bankIsLoading = true;

    if (bankScrollLoader) {
      bankScrollLoader.classList.remove("hidden");
    }

    const query = bankInputQuery?.value || "";
    const disc = bankSelectDiscipline?.value || "";
    const grade = bankSelectGrade?.value || "";
    const bncc = bankInputBncc?.value || "";

    const params = new URLSearchParams();
    if (query) params.append("query", query);
    if (disc) params.append("discipline", disc);
    if (grade) params.append("grade_year", grade);
    if (bncc) params.append("bncc_code", bncc);
    params.append("limit", String(bankPageSize));
    params.append("offset", String(bankCurrentOffset));

    try {
      const res = await apiFetch(`/api/exam-builder/bank/questions?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        const items = Array.isArray(data) ? data : (data.items || data.questions || []);
        bankTotalQuestions = (typeof data.total === "number") ? data.total : (data.total_questions || items.length);

        if (reset) {
          bankQuestions = items;
          renderBankQuestionsList();
        } else if (items.length > 0) {
          appendBankQuestionsList(items);
          bankQuestions.push(...items);
        }

        bankCurrentOffset = bankQuestions.length;
        bankHasMore = bankQuestions.length < bankTotalQuestions && items.length > 0;

        updateBankQuestionsCounter();

        // Atualiza o badge do topo com o total real se não houver filtros aplicados
        if (badgeCountQuestions && (!query && !disc && !grade && !bncc)) {
          badgeCountQuestions.textContent = bankTotalQuestions;
        }

        if (bankScrollEnd) {
          if (!bankHasMore && bankQuestions.length > 0) {
            bankScrollEnd.classList.remove("hidden");
          } else {
            bankScrollEnd.classList.add("hidden");
          }
        }
      }
    } catch (err) {
      console.error("Erro ao buscar banco de questões:", err);
    } finally {
      bankIsLoading = false;
      if (bankScrollLoader) {
        bankScrollLoader.classList.add("hidden");
      }
    }
  }

  function updateBankQuestionsCounter() {
    if (!bankFilteredCount) return;
    if (bankTotalQuestions === 0) {
      bankFilteredCount.textContent = "0 questões encontradas";
    } else if (bankQuestions.length < bankTotalQuestions) {
      bankFilteredCount.textContent = `${bankTotalQuestions} questões encontradas (exibindo ${bankQuestions.length})`;
    } else {
      bankFilteredCount.textContent = `${bankTotalQuestions} questão${bankTotalQuestions > 1 ? "ões encontradas" : " encontrada"}`;
    }
  }

  function renderBankQuestionsList() {
    if (!listBankQuestions) return;
    listBankQuestions.innerHTML = "";

    if (bankQuestions.length === 0) {
      listBankQuestions.classList.add("hidden");
      emptyBankState?.classList.remove("hidden");
      return;
    }

    listBankQuestions.classList.remove("hidden");
    emptyBankState?.classList.add("hidden");

    const frag = document.createDocumentFragment();
    bankQuestions.forEach((q, idx) => {
      const card = createBankQuestionCardElement(q, idx);
      frag.appendChild(card);
    });
    listBankQuestions.appendChild(frag);

    applyKaTeXMath(listBankQuestions);
  }

  function appendBankQuestionsList(newItems) {
    if (!listBankQuestions || !newItems || newItems.length === 0) return;
    const startIndex = bankQuestions.length;
    const frag = document.createDocumentFragment();
    newItems.forEach((q, idx) => {
      const card = createBankQuestionCardElement(q, startIndex + idx);
      frag.appendChild(card);
    });
    listBankQuestions.appendChild(frag);

    applyKaTeXMath(listBankQuestions);
  }

  function applyKaTeXMath(element) {
    if (window.renderMathInElement && element) {
      try {
        renderMathInElement(element, {
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
  }


  function createBankQuestionCardElement(q, idx) {
    const card = document.createElement("div");
    card.className = "bg-surface-container-lowest rounded-2xl border border-surface-container p-5 sm:p-6 shadow-xs hover:border-outline-variant hover:shadow-sm transition-all flex flex-col gap-3.5";

    const disc = q.discipline || "GERAL";
    const grade = q.grade_year || "";
    const bncc = q.bncc_code || q.skill || "";
    const pts = parseFloat(q.points) || 1.0;
    const ptsStr = `${pts.toFixed(1).replace(".", ",")} pt${pts !== 1 ? "s" : ""}`;

    const altsHtml = (q.alternatives || []).map(a => {
      const isCorr = Boolean(a.is_correct);
      const altImgUrl = a.image_url || (a.image && a.image.url) || "";
      const corrClass = isCorr 
        ? "bg-secondary-container text-on-secondary-container font-semibold border-secondary" 
        : "bg-surface-container-low text-on-surface border-surface-container";
      
      const imgMarkup = altImgUrl ? `
        <div class="mt-2 max-w-[220px] w-full rounded-lg overflow-hidden bg-white border border-surface-container p-1.5 shadow-2xs">
          <img src="${escapeHtml(altImgUrl)}" alt="Alternativa ${escapeHtml(a.letter || '')}" class="max-h-32 w-auto object-contain mx-auto" loading="lazy">
        </div>
      ` : "";

      return `
        <div class="flex flex-col justify-start p-2.5 rounded-xl border font-body-sm text-body-sm ${corrClass} transition-all">
          <div class="flex items-center gap-2 w-full">
            <span class="font-bold text-on-surface shrink-0">${escapeHtml(a.letter || '')})</span>
            <span class="flex-1 min-w-0 break-words leading-snug">${escapeHtml(a.text || "")}</span>
            ${isCorr ? `<span class="material-symbols-outlined text-secondary text-[16px] shrink-0 ml-auto" title="Gabarito correto">check_circle</span>` : ""}
          </div>
          ${imgMarkup}
        </div>
      `;
    }).join("");

    const imgHtml = q.image_url ? `
      <div class="my-2 max-w-xs rounded-lg overflow-hidden border border-surface-container bg-surface-container-low">
        <img src="${escapeHtml(q.image_url)}" alt="Imagem da Questão" class="w-full h-auto object-contain max-h-48" loading="lazy">
      </div>
    ` : "";

    card.innerHTML = `
      <div class="flex items-center justify-between gap-2 flex-wrap">
        <div class="flex items-center gap-2 flex-wrap">
          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full font-label-sm text-label-sm font-bold bg-primary-fixed text-on-primary-fixed">
            ${escapeHtml(disc)}
          </span>
          ${grade ? `<span class="inline-flex items-center px-2 py-0.5 rounded-full font-label-sm text-label-sm font-semibold bg-surface-container text-on-surface-variant">${escapeHtml(grade)}</span>` : ""}
          ${bncc ? `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full font-label-sm text-label-sm font-bold bg-amber-100 text-amber-900 border border-amber-200"><span class="material-symbols-outlined text-[13px]">sell</span>${escapeHtml(bncc)}</span>` : ""}
        </div>

        <div class="flex items-center gap-2">
          <span class="font-label-md text-label-md font-bold text-on-surface-variant">${ptsStr}</span>
          <button class="btn-use-question inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold ${isQuestionInDrawer(q) ? 'bg-secondary-container text-secondary' : 'bg-primary-fixed text-on-primary-fixed hover:bg-primary-container hover:text-on-primary'} transition-all cursor-pointer" data-qid="${escapeHtml(q.id || String(idx))}">
            <span class="material-symbols-outlined text-[16px]">${isQuestionInDrawer(q) ? 'check' : 'add'}</span>
            <span>${isQuestionInDrawer(q) ? 'Adicionada' : 'Usar em Nova Prova'}</span>
          </button>
          <button class="btn-delete-bank-question w-8 h-8 rounded-lg flex items-center justify-center text-outline hover:text-error hover:bg-error-container transition-colors cursor-pointer" title="Excluir questão permanentemente do Banco" data-qid="${escapeHtml(q.id || '')}">
            <span class="material-symbols-outlined text-[17px]">delete</span>
          </button>
        </div>
      </div>

      <div class="font-body-md text-body-md text-on-surface leading-relaxed font-normal whitespace-pre-line">
        ${q.statement || "Sem enunciado"}
      </div>

      ${imgHtml}

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-1">
        ${altsHtml}
      </div>

      <div class="font-label-sm text-label-sm text-outline pt-2 border-t border-surface-container flex items-center justify-between">
        <span>Origem: ${escapeHtml(q.source_exam_title || "Banco SEMED")}</span>
        <span>ID: ${(q.id || "").substring(0, 8)}...</span>
      </div>
    `;

    const btnUse = card.querySelector(".btn-use-question");
    btnUse?.addEventListener("click", () => {
      toggleQuestionInDrawer(q, btnUse);
    });

    const btnDelete = card.querySelector(".btn-delete-bank-question");
    btnDelete?.addEventListener("click", async () => {
      const confirmed = await showModernConfirmDialog({
        title: "Excluir Questão do Banco",
        message: "Tem certeza que deseja excluir permanentemente esta questão do seu acervo?",
        calloutTitle: "Atenção: Ação Irreversível",
        calloutDesc: "Esta questão e todas as suas alternativas serão removidas permanentemente do Banco de Questões. Esta ação não poderá ser desfeita.",
        calloutIcon: "warning",
        calloutType: "danger",
        icon: "delete_forever",
        iconType: "danger",
        confirmText: "Sim, Excluir Questão",
        confirmIcon: "delete_forever",
        cancelText: "Cancelar",
        isDanger: true
      });
      if (!confirmed) return;

      showToast("Excluindo questão do banco...", "info");
      try {
        const res = await apiFetch(`/api/exam-builder/bank/questions/${q.id}`, { method: "DELETE" });
        if (res.ok) {
          showToast("Questão excluída do Banco com sucesso!", "success");
          await loadBankQuestions();
          await loadBankFilters();
        } else {
          showToast("Falha ao excluir questão do banco.", "error");
        }
      } catch (err) {
        showToast("Erro de conexão ao excluir questão.", "error");
      }
    });

    return card;
  }

  // =========================================================================
  // Filtros com Debounce
  // =========================================================================
  function setupFilters() {
    inputSearchExams?.addEventListener("input", () => {
      clearTimeout(searchDebounceTimer);
      searchDebounceTimer = setTimeout(renderExams, 200);
    });

    selectFilterDiscipline?.addEventListener("change", renderExams);
    selectFilterGrade?.addEventListener("change", renderExams);

    btnClearExamFilters?.addEventListener("click", () => {
      if (inputSearchExams) inputSearchExams.value = "";
      if (selectFilterDiscipline) selectFilterDiscipline.value = "";
      if (selectFilterGrade) selectFilterGrade.value = "";
      renderExams();
    });

    btnRefreshExams?.addEventListener("click", async () => {
      showToast("Atualizando dados...", "info");
      await Promise.all([loadExamsList(), loadBankFilters(), loadBankQuestions()]);
      showToast("Dados atualizados!", "success");
    });

    bankInputQuery?.addEventListener("input", () => {
      clearTimeout(searchDebounceTimer);
      searchDebounceTimer = setTimeout(() => loadBankQuestions(true), 350);
    });

    bankSelectDiscipline?.addEventListener("change", () => loadBankQuestions(true));
    bankSelectGrade?.addEventListener("change", () => loadBankQuestions(true));
    bankInputBncc?.addEventListener("input", () => {
      clearTimeout(searchDebounceTimer);
      searchDebounceTimer = setTimeout(() => loadBankQuestions(true), 350);
    });

    btnClearBankFilters?.addEventListener("click", () => {
      if (bankInputQuery) bankInputQuery.value = "";
      if (bankSelectDiscipline) bankSelectDiscipline.value = "";
      if (bankSelectGrade) bankSelectGrade.value = "";
      if (bankInputBncc) bankInputBncc.value = "";
      loadBankQuestions(true);
    });

    setupBankInfiniteScroll();
  }

  let bankObserver = null;
  function setupBankInfiniteScroll() {
    const sentinel = document.getElementById("bank-scroll-sentinel");

    if ("IntersectionObserver" in window && sentinel) {
      bankObserver = new IntersectionObserver((entries) => {
        const entry = entries[0];
        if (entry.isIntersecting && activeTab === "bank" && !bankIsLoading && bankHasMore) {
          loadBankQuestions(false);
        }
      }, {
        rootMargin: "350px"
      });
      bankObserver.observe(sentinel);
    }

    // Fallback de rolagem na janela do navegador
    window.addEventListener("scroll", () => {
      if (activeTab !== "bank" || bankIsLoading || !bankHasMore) return;
      const scrollPos = window.innerHeight + window.scrollY;
      const threshold = document.documentElement.scrollHeight - 600;
      if (scrollPos >= threshold) {
        loadBankQuestions(false);
      }
    }, { passive: true });
  }


  // =========================================================================
  // Modal: Catálogo Oficial de Habilidades da BNCC
  // =========================================================================
  function setupBankBnccPicker() {
    loadBnccModalFilters();

    btnOpenBnccModal?.addEventListener("click", () => {
      bnccPickerTarget = bankInputBncc;
      openBnccModal();
    });
    btnCloseBnccModal?.addEventListener("click", closeBnccModal);
    btnCancelBnccModal?.addEventListener("click", closeBnccModal);

    modalBnccPicker?.addEventListener("click", (e) => {
      if (e.target === modalBnccPicker) closeBnccModal();
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && modalBnccPicker && modalBnccPicker.classList.contains("active")) {
        closeBnccModal();
      }
    });

    bnccModalFilterDiscipline?.addEventListener("change", triggerBnccModalSearch);
    bnccModalFilterGrade?.addEventListener("change", triggerBnccModalSearch);
    bnccModalSearchInput?.addEventListener("input", () => {
      clearTimeout(bnccModalDebounceTimer);
      bnccModalDebounceTimer = setTimeout(triggerBnccModalSearch, 250);
    });
  }

  async function loadBnccModalFilters() {
    try {
      const res = await apiFetch("/api/bncc/filtros");
      if (!res.ok) return;
      const data = await res.json();
      if (bnccModalFilterDiscipline && data.disciplinas) {
        bnccModalFilterDiscipline.innerHTML = '<option value="">Todas as Disciplinas</option>';
        data.disciplinas.forEach(disc => {
          const opt = document.createElement("option");
          opt.value = disc;
          opt.textContent = disc;
          bnccModalFilterDiscipline.appendChild(opt);
        });
      }
    } catch (err) {
      console.warn("Aviso ao carregar filtros BNCC:", err);
    }
  }

  function openBnccModal() {
    if (!modalBnccPicker) return;

    // Sincronizar pré-seleção com filtros atuais do banco
    if (bnccModalFilterDiscipline && bankSelectDiscipline) {
      const discVal = (bankSelectDiscipline.value || "").trim().toLowerCase();
      Array.from(bnccModalFilterDiscipline.options).forEach(opt => {
        if (opt.value && (discVal.includes(opt.value.toLowerCase()) || opt.value.toLowerCase().includes(discVal))) {
          opt.selected = true;
        }
      });
    }

    if (bnccModalFilterGrade && bankSelectGrade) {
      const gradeVal = bankSelectGrade.value || "";
      const match = gradeVal.match(/(\d)/);
      if (match && match[1]) {
        bnccModalFilterGrade.value = match[1];
      }
    }

    if (bnccModalSearchInput) {
      bnccModalSearchInput.value = "";
    }

    modalBnccPicker.classList.add("active");
    triggerBnccModalSearch();
    setTimeout(() => {
      bnccModalSearchInput?.focus();
    }, 150);
  }

  function closeBnccModal() {
    if (modalBnccPicker) modalBnccPicker.classList.remove("active");
  }

  async function triggerBnccModalSearch() {
    if (!bnccModalCardsList) return;
    const discipline = bnccModalFilterDiscipline ? bnccModalFilterDiscipline.value : "";
    const ano = bnccModalFilterGrade ? bnccModalFilterGrade.value : "";
    const q = bnccModalSearchInput ? bnccModalSearchInput.value.trim() : "";

    bnccModalCardsList.innerHTML = `
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

      renderBnccModalCards(data.habilidades || []);
      if (bnccModalResultsCount) {
        bnccModalResultsCount.textContent = `${data.total} habilidade(s) encontrada(s)${data.total > 80 ? ' (exibindo as 80 primeiras)' : ''}`;
      }
    } catch (err) {
      bnccModalCardsList.innerHTML = `
        <div class="p-8 text-center text-slate-400 text-xs">
          Erro ao carregar dados da BNCC. Verifique a conexão com o servidor.
        </div>
      `;
    }
  }

  function renderBnccModalCards(skills) {
    if (!bnccModalCardsList) return;
    bnccModalCardsList.innerHTML = "";

    if (skills.length === 0) {
      bnccModalCardsList.innerHTML = `
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
          <button type="button" class="btn-select-bncc-skill px-3 py-1 rounded-lg bg-blue-50 hover:bg-blue-600 text-blue-700 hover:text-white border border-blue-200 hover:border-transparent text-xs font-bold transition-all flex items-center gap-1 cursor-pointer">
            <span class="material-symbols-outlined text-[15px]">check_circle</span>
            <span>Selecionar</span>
          </button>
        </div>
        <p class="text-xs text-slate-700 leading-relaxed text-justify">${escapeHtml(skill.texto)}</p>
      `;

      card.querySelector(".btn-select-bncc-skill")?.addEventListener("click", () => {
        if (bnccPickerTarget) {
          bnccPickerTarget.value = skill.codigo;
          if (bnccPickerTarget === bankInputBncc) {
            loadBankQuestions(true);
            showToast(`Filtro aplicado: ${skill.codigo} (${skill.componente})`, "success");
          } else {
            showToast(`Habilidade selecionada: ${skill.codigo}`, "success");
          }
        } else if (bankInputBncc) {
          bankInputBncc.value = skill.codigo;
          loadBankQuestions(true);
          showToast(`Filtro aplicado: ${skill.codigo} (${skill.componente})`, "success");
        }
        closeBnccModal();
      });

      bnccModalCardsList.appendChild(card);
    });
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
    const dlSchools = document.getElementById("datalist-schools");
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
    const dlClassrooms = document.getElementById("datalist-classrooms");
    const hint = document.getElementById("modal-classroom-hint");
    if (!dlClassrooms) return;
    dlClassrooms.innerHTML = "";

    if (!schoolName || !schoolName.trim()) {
      if (hint) hint.textContent = "escolha ou digite";
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
    if (!classroomName || !modalSelectGrade) return;
    const upper = classroomName.toUpperCase();
    const gradeOptions = Array.from(modalSelectGrade.options).map(o => o.value);
    for (const g of gradeOptions) {
      if (upper.includes(g)) {
        modalSelectGrade.value = g;
        return;
      }
    }
    const m = upper.match(/(\d)[º°ªa-zA-Z\s]*([A-Z])/);
    if (m && m[1]) {
      const gNum = `${m[1]}º ANO`;
      if (gradeOptions.includes(gNum)) {
        modalSelectGrade.value = gNum;
      }
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

  // =========================================================================
  // Modal: Criar Nova Prova
  // =========================================================================
  function setupCreateModalEvents() {
    btnOpenCreateModal?.addEventListener("click", () => openCreateModal());
    btnEmptyCreate?.addEventListener("click", () => openCreateModal());
    btnCloseCreateModal?.addEventListener("click", closeCreateModal);
    btnCancelCreate?.addEventListener("click", closeCreateModal);

    modalCreateExam?.addEventListener("click", (e) => {
      if (e.target === modalCreateExam) closeCreateModal();
    });

    modalInputSchool?.addEventListener("input", (e) => updateClassroomsDatalist(e.target.value));
    modalInputSchool?.addEventListener("change", (e) => updateClassroomsDatalist(e.target.value));
    modalInputClassroom?.addEventListener("change", (e) => autoDetectGradeFromClassroom(e.target.value));

    optionCreateTypes.forEach(opt => {
      opt.addEventListener("click", () => {
        const type = opt.getAttribute("data-type");
        optionCreateTypes.forEach(o => {
          const radio = o.querySelector("input[type=radio]");
          const checkIcon = o.querySelector(".check-icon");
          if (o === opt) {
            o.className = "cursor-pointer border-2 border-primary bg-primary-fixed/20 rounded-2xl p-4 flex flex-col gap-2 transition-all relative option-create-type active";
            if (radio) radio.checked = true;
            if (checkIcon) {
              checkIcon.textContent = "check_circle";
              checkIcon.className = "material-symbols-outlined text-primary text-[22px] check-icon";
            }
          } else {
            o.className = "cursor-pointer border-2 border-surface-container hover:border-outline-variant rounded-2xl p-4 flex flex-col gap-2 transition-all relative option-create-type";
            if (radio) radio.checked = false;
            if (checkIcon) {
              checkIcon.textContent = "radio_button_unchecked";
              checkIcon.className = "material-symbols-outlined text-outline text-[22px] check-icon";
            }
          }
        });

        if (type === "bank") {
          modalBankSelectorArea?.classList.remove("hidden");
          modalBankSelectorArea?.classList.add("flex");
          renderModalBankChecklist();
        } else {
          modalBankSelectorArea?.classList.add("hidden");
          modalBankSelectorArea?.classList.remove("flex");
        }
      });
    });

    modalBankQuickSearch?.addEventListener("input", renderModalBankChecklist);
    btnConfirmCreateExam?.addEventListener("click", confirmCreateExam);

    // Controles de Presets de Margens no Modal de Criação
    document.querySelectorAll(".modal-create-preset-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const preset = btn.getAttribute("data-preset");
        setModalMarginPreset(preset);
      });
    });

    ["modal-cfg-margin-top", "modal-cfg-margin-bottom", "modal-cfg-margin-left", "modal-cfg-margin-right"].forEach(id => {
      document.getElementById(id)?.addEventListener("input", syncModalMarginPresetState);
    });

    // Controles de Alternativas (4 vs 5)
    document.getElementById("modal-btn-alt-4")?.addEventListener("click", () => setModalAltMode(4));
    document.getElementById("modal-btn-alt-5")?.addEventListener("click", () => setModalAltMode(5));

    // Controles de Colunas (1 vs 2)
    document.getElementById("modal-btn-col-1")?.addEventListener("click", () => setModalColMode(1));
    document.getElementById("modal-btn-col-2")?.addEventListener("click", () => setModalColMode(2));
  }

  let modalSelectedAltMode = 4;
  let modalSelectedColumns = 2;

  const MODAL_MARGIN_PRESETS = {
    narrow: { top: 1.5, bottom: 1.5, left: 1.5, right: 1.5 },
    standard: { top: 3.0, bottom: 2.0, left: 3.0, right: 2.0 },
    wide: { top: 3.5, bottom: 3.0, left: 3.5, right: 3.0 }
  };

  function setModalMarginPreset(presetKey) {
    const p = MODAL_MARGIN_PRESETS[presetKey];
    if (!p) return;

    const inpTop = document.getElementById("modal-cfg-margin-top");
    const inpBottom = document.getElementById("modal-cfg-margin-bottom");
    const inpLeft = document.getElementById("modal-cfg-margin-left");
    const inpRight = document.getElementById("modal-cfg-margin-right");

    if (inpTop) inpTop.value = p.top;
    if (inpBottom) inpBottom.value = p.bottom;
    if (inpLeft) inpLeft.value = p.left;
    if (inpRight) inpRight.value = p.right;

    document.querySelectorAll(".modal-create-preset-btn").forEach(btn => {
      const isCurrent = btn.getAttribute("data-preset") === presetKey;
      btn.className = isCurrent
        ? "modal-create-preset-btn px-2.5 py-1 rounded text-xs font-semibold bg-primary-container text-on-primary shadow-xs transition-colors active"
        : "modal-create-preset-btn px-2.5 py-1 rounded text-xs font-semibold text-on-surface-variant hover:bg-surface-container transition-colors";
    });
  }

  function syncModalMarginPresetState() {
    const t = parseFloat(document.getElementById("modal-cfg-margin-top")?.value) || 0;
    const b = parseFloat(document.getElementById("modal-cfg-margin-bottom")?.value) || 0;
    const l = parseFloat(document.getElementById("modal-cfg-margin-left")?.value) || 0;
    const r = parseFloat(document.getElementById("modal-cfg-margin-right")?.value) || 0;

    let matched = null;
    for (const [key, p] of Object.entries(MODAL_MARGIN_PRESETS)) {
      if (Math.abs(p.top - t) < 0.05 && Math.abs(p.bottom - b) < 0.05 && Math.abs(p.left - l) < 0.05 && Math.abs(p.right - r) < 0.05) {
        matched = key;
        break;
      }
    }

    document.querySelectorAll(".modal-create-preset-btn").forEach(btn => {
      const isCurrent = matched && btn.getAttribute("data-preset") === matched;
      btn.className = isCurrent
        ? "modal-create-preset-btn px-2.5 py-1 rounded text-xs font-semibold bg-primary-container text-on-primary shadow-xs transition-colors active"
        : "modal-create-preset-btn px-2.5 py-1 rounded text-xs font-semibold text-on-surface-variant hover:bg-surface-container transition-colors";
    });
  }

  function setModalAltMode(mode) {
    modalSelectedAltMode = mode;
    const btnAlt4 = document.getElementById("modal-btn-alt-4");
    const btnAlt5 = document.getElementById("modal-btn-alt-5");
    if (btnAlt4 && btnAlt5) {
      if (mode === 4) {
        btnAlt4.className = "flex-1 py-1 rounded text-xs font-bold bg-primary-container text-on-primary shadow-xs transition-colors active";
        btnAlt5.className = "flex-1 py-1 rounded text-xs font-bold text-on-surface-variant transition-colors";
      } else {
        btnAlt5.className = "flex-1 py-1 rounded text-xs font-bold bg-primary-container text-on-primary shadow-xs transition-colors active";
        btnAlt4.className = "flex-1 py-1 rounded text-xs font-bold text-on-surface-variant transition-colors";
      }
    }
  }

  function setModalColMode(cols) {
    modalSelectedColumns = cols;
    const btnCol1 = document.getElementById("modal-btn-col-1");
    const btnCol2 = document.getElementById("modal-btn-col-2");
    if (btnCol1 && btnCol2) {
      if (cols === 1) {
        btnCol1.className = "flex-1 py-1 rounded text-xs font-semibold bg-primary-container text-on-primary shadow-xs transition-colors active";
        btnCol2.className = "flex-1 py-1 rounded text-xs font-semibold text-on-surface-variant transition-colors";
      } else {
        btnCol2.className = "flex-1 py-1 rounded text-xs font-semibold bg-primary-container text-on-primary shadow-xs transition-colors active";
        btnCol1.className = "flex-1 py-1 rounded text-xs font-semibold text-on-surface-variant transition-colors";
      }
    }
  }

  function openCreateModal(initialData = {}) {
    if (!modalCreateExam) return;
    // Campos preenchidos de forma amigável com suporte a escolas e turmas da rede
    if (modalInputTitle) modalInputTitle.value = initialData.title || "";
    if (modalInputDiscipline) setSelectValueCaseInsensitive(modalInputDiscipline, initialData.discipline || "MATEMÁTICA");
    if (modalSelectGrade) modalSelectGrade.value = initialData.grade_year || "9º ANO";
    
    const schName = initialData.school_name || "";
    if (modalInputSchool) modalInputSchool.value = schName;
    updateClassroomsDatalist(schName);

    if (modalInputClassroom) modalInputClassroom.value = initialData.classroom || "";

    setModalMarginPreset(initialData.preset || "standard");
    setModalAltMode(initialData.alt_mode || 4);
    setModalColMode(initialData.columns || 2);
    const chkSheet = document.getElementById("modal-chk-answer-sheet");
    if (chkSheet) chkSheet.checked = (initialData.include_answer_sheet !== false);

    const boxDrawerBadge = document.getElementById("box-drawer-selected-badge");
    const boxModeSelector = document.getElementById("box-create-mode-selector");
    const drawerCountText = document.getElementById("modal-drawer-count-text");

    if (initialData.from_drawer) {
      if (boxDrawerBadge) {
        boxDrawerBadge.classList.remove("hidden");
        boxDrawerBadge.classList.add("flex");
      }
      if (drawerCountText) {
        const count = drawerQuestions.length;
        drawerCountText.textContent = `${count} questõe${count !== 1 ? 's' : ''} selecionada${count !== 1 ? 's' : ''}`;
      }
      if (boxModeSelector) boxModeSelector.classList.add("hidden");
      modalBankSelectorArea?.classList.add("hidden");
      modalBankSelectorArea?.classList.remove("flex");
    } else {
      if (boxDrawerBadge) {
        boxDrawerBadge.classList.add("hidden");
        boxDrawerBadge.classList.remove("flex");
      }
      if (boxModeSelector) boxModeSelector.classList.remove("hidden");
      const blankOption = document.querySelector('.option-create-type[data-type="blank"]');
      if (blankOption) blankOption.click();
    }

    selectedBankQuestions.clear();
    modalCreateExam.classList.add("active");
    modalInputTitle?.focus();
  }

  function openCreateModalWithQuestion(question) {
    openCreateModal({
      title: `Avaliação de ${question.discipline || "Matemática"}`,
      discipline: question.discipline || "MATEMÁTICA",
      grade_year: question.grade_year || "9º ANO"
    });

    const bankOption = document.querySelector('.option-create-type[data-type="bank"]');
    if (bankOption) bankOption.click();

    selectedBankQuestions.add(question.id);
    updateModalBankCount();
    renderModalBankChecklist();
  }

  function closeCreateModal() {
    if (!modalCreateExam) return;
    modalCreateExam.classList.remove("active");
  }

  function renderModalBankChecklist() {
    if (!modalBankQuestionsChecklist) return;
    modalBankQuestionsChecklist.innerHTML = "";

    const search = (modalBankQuickSearch?.value || "").toLowerCase().trim();
    const filtered = bankQuestions.filter(q => {
      const stmtMatch = (q.statement || "").toLowerCase().includes(search);
      const bnccMatch = (q.bncc_code || q.skill || "").toLowerCase().includes(search);
      const discMatch = (q.discipline || "").toLowerCase().includes(search);
      return !search || (stmtMatch || bnccMatch || discMatch);
    });

    if (filtered.length === 0) {
      modalBankQuestionsChecklist.innerHTML = `
        <div class="py-6 text-center font-body-sm text-body-sm text-outline">Nenhuma questão encontrada para os filtros.</div>
      `;
      return;
    }

    filtered.forEach(q => {
      const isChecked = selectedBankQuestions.has(q.id);
      const item = document.createElement("label");
      item.className = `flex items-start gap-2.5 p-2.5 rounded-xl border text-xs cursor-pointer transition-all ${isChecked ? "bg-primary-fixed/20 border-primary font-semibold" : "bg-surface-container-lowest border-surface-container hover:bg-surface-container-low"}`;

      item.innerHTML = `
        <input type="checkbox" class="w-4 h-4 mt-0.5 accent-primary rounded cursor-pointer" ${isChecked ? "checked" : ""}>
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-1.5 mb-1">
            <span class="font-bold text-on-surface">${escapeHtml(q.discipline || "Geral")}</span>
            ${q.bncc_code ? `<span class="px-1.5 py-0.5 rounded text-[10px] bg-amber-100 text-amber-900 font-bold">${escapeHtml(q.bncc_code)}</span>` : ""}
          </div>
          <div class="text-on-surface-variant line-clamp-2 leading-tight">${escapeHtml(q.statement || "Sem texto")}</div>
        </div>
      `;

      item.querySelector("input")?.addEventListener("change", (e) => {
        if (e.target.checked) {
          selectedBankQuestions.add(q.id);
        } else {
          selectedBankQuestions.delete(q.id);
        }
        updateModalBankCount();
      });

      modalBankQuestionsChecklist.appendChild(item);
    });
  }

  function updateModalBankCount() {
    if (modalBankSelectedCount) {
      modalBankSelectedCount.textContent = `${selectedBankQuestions.size} selecionadas`;
    }
  }

  async function confirmCreateExam() {
    const title = (modalInputTitle?.value || "").trim() || "Nova Avaliação";
    const discipline = (modalInputDiscipline?.value || "").trim() || "MATEMÁTICA";
    const grade = modalSelectGrade?.value || "9º ANO";
    const classroom = (modalInputClassroom?.value || "").trim();
    const school = (modalInputSchool?.value || "").trim() || "Escola Municipal";

    const mt = parseFloat(document.getElementById("modal-cfg-margin-top")?.value) || 3.0;
    const mb = parseFloat(document.getElementById("modal-cfg-margin-bottom")?.value) || 2.0;
    const ml = parseFloat(document.getElementById("modal-cfg-margin-left")?.value) || 3.0;
    const mr = parseFloat(document.getElementById("modal-cfg-margin-right")?.value) || 2.0;
    const cols = modalSelectedColumns || 2;
    const incSheet = Boolean(document.getElementById("modal-chk-answer-sheet")?.checked);

    const createTypeRadio = document.querySelector('input[name="create_type"]:checked');
    const createType = createTypeRadio ? createTypeRadio.value : "blank";

    let initialQuestions = [];
    if (createType === "bank") {
      const questionsSource = [];
      if (drawerQuestions.length > 0) {
        drawerQuestions.forEach(q => {
          if (!q.id || selectedBankQuestions.has(q.id)) {
            questionsSource.push(q);
          }
        });
      }
      bankQuestions.forEach(q => {
        if (selectedBankQuestions.has(q.id) && !questionsSource.some(s => s.id === q.id)) {
          questionsSource.push(q);
        }
      });

      const maxAlts = modalSelectedAltMode === 5 ? 5 : 4;

      initialQuestions = questionsSource.map((q, idx) => ({
        question_number: idx + 1,
        statement: q.statement || "",
        points: parseFloat(q.points) || 1.0,
        image_url: q.image_url || "",
        image_position: q.image_position || "after_statement",
        image_width: q.image_width || "50%",
        image_caption: q.image_caption || "",
        bncc_code: q.bncc_code || "",
        discipline: discipline || q.discipline || "GERAL",
        grade_year: grade || q.grade_year || "9º ANO",
        alternatives: (q.alternatives || []).slice(0, maxAlts).map((a, aIdx) => {
          const altImg = a.image_url || (a.image ? a.image.url : "") || "";
          const altWidth = a.image_width || (a.image ? a.image.width : "180px") || "180px";
          const altAlign = a.image_align || (a.image ? a.image.align : "center") || "center";
          return {
            letter: a.letter || String.fromCharCode(65 + aIdx),
            text: a.text || "",
            is_correct: Boolean(a.is_correct),
            image_url: altImg,
            image_width: altWidth,
            image_align: altAlign,
            image: altImg ? { url: altImg, width: altWidth, align: altAlign } : null
          };
        })
      }));
    } else {
      // PROVA EM BRANCO DO ZERO: Cria exatamente 1 questão vazia e limpa para o professor preencher
      const maxAlts = modalSelectedAltMode === 5 ? 5 : 4;
      const alts = [];
      for (let i = 0; i < maxAlts; i++) {
        alts.push({
          letter: String.fromCharCode(65 + i),
          text: "",
          is_correct: i === 0,
          image_url: ""
        });
      }
      initialQuestions = [{
        question_number: 1,
        statement: "",
        points: 1.0,
        image_url: "",
        image_position: "after_statement",
        image_width: "50%",
        image_caption: "",
        bncc_code: "",
        discipline: discipline || "GERAL",
        grade_year: grade || "9º ANO",
        alternatives: alts
      }];
    }

    const payload = {
      title: title,
      discipline: discipline,
      grade_year: grade,
      classroom: classroom,
      school_name: school,
      institution: "PREFEITURA MUNICIPAL DE LAGOA DA CANOA - SEMED",
      teacher_name: "",
      shift: "MATUTINO",
      exam_date: new Date().toLocaleDateString("pt-BR"),
      max_score: initialQuestions.length > 0 ? initialQuestions.reduce((s, q) => s + q.points, 0) : 10.0,
      columns_layout: cols,
      columns: cols,
      font_size: "medium",
      header_style: "standard",
      include_header: true,
      include_answer_sheet: incSheet ? 1 : 0,
      margin_top: mt,
      margin_bottom: mb,
      margin_left: ml,
      margin_right: mr,
      footer_text: "Boa Prova!",
      questions: initialQuestions
    };

    showToast("Criando avaliação no sistema...", "info");
    try {
      const res = await apiFetch("/api/exam-builder/exams", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const created = await res.json();
        closeCreateModal();
        drawerQuestions = [];
        drawerUserOpened = false;
        updateDrawerUI();
        showToast("Avaliação criada! Redirecionando para o editor...", "success");
        setTimeout(() => {
          window.location.href = `/elaborador?exam_id=${created.id}`;
        }, 400);
      } else {
        showToast("Falha ao criar avaliação no servidor.", "error");
      }
    } catch (err) {
      showToast("Erro ao conectar ao servidor.", "error");
    }
  }

  // =========================================================================
  // Modal: Emitir Prova (PDF vs DOCX)
  // =========================================================================
  function setupEmitirModalEvents() {
    btnCloseEmitirModal?.addEventListener("click", closeEmitirModal);
    btnCancelEmitir?.addEventListener("click", closeEmitirModal);
    modalEmitirProva?.addEventListener("click", (e) => {
      if (e.target === modalEmitirProva) closeEmitirModal();
    });

    optionEmitirFormats.forEach(opt => {
      opt.addEventListener("click", () => {
        const fmt = opt.getAttribute("data-format");
        selectedEmitirFormat = fmt;
        optionEmitirFormats.forEach(o => {
          const radio = o.querySelector("input[type=radio]");
          const radioIcon = o.querySelector(".radio-icon");
          if (o === opt) {
            o.className = "cursor-pointer border-2 border-primary bg-primary-fixed/20 rounded-xl p-3.5 transition-all flex flex-col gap-2 relative option-emitir-format active";
            if (radio) radio.checked = true;
            if (radioIcon) {
              radioIcon.textContent = "check_circle";
              radioIcon.className = "material-symbols-outlined text-primary text-[20px] radio-icon";
            }
          } else {
            o.className = "cursor-pointer border-2 border-surface-container rounded-xl p-3.5 hover:border-outline-variant hover:bg-surface-container-low transition-all flex flex-col gap-2 relative option-emitir-format";
            if (radio) radio.checked = false;
            if (radioIcon) {
              radioIcon.textContent = "radio_button_unchecked";
              radioIcon.className = "material-symbols-outlined text-outline text-[20px] radio-icon";
            }
          }
        });
      });
    });

    btnConfirmEmitirDownload?.addEventListener("click", downloadEmitirProva);
  }

  function openEmitirModal(exam) {
    currentEmitirExam = exam;
    if (modalEmitirProva) {
      modalEmitirProva.classList.add("active");
    }
  }

  function closeEmitirModal() {
    if (modalEmitirProva) {
      modalEmitirProva.classList.remove("active");
    }
  }

  // Helper Seguro de Download de Blobs (PDF / Word)
  function triggerFileDownload(rawBlob, defaultFilename, dispositionHeader = null, mimeType = "application/pdf") {
    let resolvedFilename = defaultFilename || "Avaliacao.pdf";

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

    resolvedFilename = resolvedFilename.replace(/[/\\?%*:|"<>]/g, "_").trim();

    const isDocx = (mimeType.includes("word") || defaultFilename.toLowerCase().endsWith(".docx"));
    const requiredExt = isDocx ? ".docx" : ".pdf";
    if (!resolvedFilename.toLowerCase().endsWith(requiredExt)) {
      resolvedFilename += requiredExt;
    }

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

    setTimeout(() => {
      try {
        if (downloadLink.parentNode) {
          document.body.removeChild(downloadLink);
        }
        window.URL.revokeObjectURL(blobUrl);
      } catch (err) { }
    }, 15000);
  }

  async function downloadEmitirProva() {
    if (!currentEmitirExam) return;
    closeEmitirModal();

    const isDocx = (selectedEmitirFormat === "docx");
    showToast(isDocx ? "Compilando documento Word (.docx)..." : "Compilando PDF oficial...", "info");

    try {
      const endpoint = isDocx
        ? "/api/exam-builder/generate-docx"
        : `/api/exam-builder/exams/${currentEmitirExam.id}/pdf`;

      const options = isDocx
        ? {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(currentEmitirExam)
          }
        : { method: "GET" };

      const res = await apiFetch(endpoint, options);
      if (res.ok) {
        const disposition = res.headers.get("Content-Disposition");
        const blob = await res.blob();
        const ext = isDocx ? "docx" : "pdf";
        const fallbackName = (currentEmitirExam.title || "Avaliacao").replace(/[/\\?%*:|"<>]/g, "_") + `.${ext}`;
        const mimeType = isDocx ? "application/vnd.openxmlformats-officedocument.wordprocessingml.document" : "application/pdf";
        triggerFileDownload(blob, fallbackName, disposition, mimeType);
        showToast(isDocx ? "Word (.docx) baixado com sucesso!" : "PDF baixado com sucesso!", "success");
      } else {
        showToast("Erro ao compilar arquivo para download.", "error");
      }
    } catch (err) {
      showToast("Falha na conexão ao emitir prova.", "error");
    }
  }

  // =========================================================================
  // GAVETA FLUTUANTE LATERAL: MONTADOR DE PROVA (CARRINHO DE QUESTÕES)
  // =========================================================================
  function setupDrawerEvents() {
    btnDrawerClose?.addEventListener("click", closeDrawer);
    btnDrawerClear?.addEventListener("click", clearDrawer);
    btnDrawerToggleFloating?.addEventListener("click", openDrawer);
    btnDrawerCreateExam?.addEventListener("click", openCreateModalFromDrawer);

    // Fechar ao teclar Esc se a gaveta estiver aberta
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !drawerNewExam?.classList.contains("hidden")) {
        closeDrawer();
      }
    });

    updateDrawerUI();
  }

  function openDrawer() {
    drawerUserOpened = true;
    if (activeTab !== "bank") {
      switchTab("bank");
      return;
    }
    drawerNewExam?.classList.remove("hidden");
    drawerNewExam?.classList.add("flex");
    btnDrawerToggleFloating?.classList.add("hidden");
    btnDrawerToggleFloating?.classList.remove("flex");

    // Ajusta o container principal para ficar ao lado do painel fixo, sem sobreposição
    if (window.innerWidth >= 1200 && mainContentWrapper) {
      mainContentWrapper.style.marginRight = "440px";
      mainContentWrapper.style.maxWidth = "calc(100vw - 460px)";
    }
  }

  function closeDrawer() {
    drawerUserOpened = false;
    drawerNewExam?.classList.add("hidden");
    drawerNewExam?.classList.remove("flex");
    if (mainContentWrapper) {
      mainContentWrapper.style.marginRight = "auto";
      mainContentWrapper.style.maxWidth = "1440px";
    }
    if (drawerQuestions.length > 0 && activeTab === "bank") {
      btnDrawerToggleFloating?.classList.remove("hidden");
      btnDrawerToggleFloating?.classList.add("flex");
    } else {
      btnDrawerToggleFloating?.classList.add("hidden");
      btnDrawerToggleFloating?.classList.remove("flex");
    }
  }

  function isQuestionInDrawer(q) {
    return drawerQuestions.some(item => {
      if (item.id && q.id) return item.id === q.id;
      return (item.statement === q.statement) && (item.discipline === q.discipline);
    });
  }

  function toggleQuestionInDrawer(q, btnElement) {
    const existingIndex = drawerQuestions.findIndex(item => {
      if (item.id && q.id) return item.id === q.id;
      return (item.statement === q.statement) && (item.discipline === q.discipline);
    });

    if (existingIndex >= 0) {
      // Remove da gaveta
      drawerQuestions.splice(existingIndex, 1);
      showToast("Questão removida da nova prova.", "info");
    } else {
      // Adiciona à gaveta
      drawerQuestions.push(q);
      showToast(`Questão adicionada à prova! (${drawerQuestions.length} no total)`, "success");
      openDrawer();
    }

    updateDrawerUI();
    renderBankQuestionsButtonsState();
  }

  function removeQuestionFromDrawer(index) {
    if (index >= 0 && index < drawerQuestions.length) {
      drawerQuestions.splice(index, 1);
      updateDrawerUI();
      renderBankQuestionsButtonsState();
      showToast("Questão removida da prova.", "info");
    }
  }

  function clearDrawer() {
    if (drawerQuestions.length === 0) return;
    drawerQuestions = [];
    updateDrawerUI();
    renderBankQuestionsButtonsState();
    showToast("Todas as questões foram removidas da nova prova.", "info");
  }

  function renderBankQuestionsButtonsState() {
    // Atualiza todos os botões visíveis no acervo
    document.querySelectorAll(".btn-use-question").forEach(btn => {
      const qid = btn.getAttribute("data-qid");
      const inDrawer = drawerQuestions.some((q, idx) => (q.id ? String(q.id) === qid : String(idx) === qid));
      if (inDrawer) {
        btn.className = "btn-use-question inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-secondary-container text-secondary transition-all cursor-pointer";
        btn.innerHTML = `<span class="material-symbols-outlined text-[16px]">check</span><span>Adicionada</span>`;
      } else {
        btn.className = "btn-use-question inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-primary-fixed text-on-primary-fixed hover:bg-primary-container hover:text-on-primary transition-all cursor-pointer";
        btn.innerHTML = `<span class="material-symbols-outlined text-[16px]">add</span><span>Usar em Nova Prova</span>`;
      }
    });
  }

  function updateDrawerUI() {
    const count = drawerQuestions.length;
    if (drawerCountBadge) drawerCountBadge.textContent = count;
    if (drawerTotalCount) drawerTotalCount.textContent = count;
    if (floatingBadgeCount) floatingBadgeCount.textContent = count;

    // Calcular soma de pontos
    const totalPoints = drawerQuestions.reduce((acc, q) => acc + (parseFloat(q.points) || 1.0), 0);
    if (drawerTotalPoints) {
      drawerTotalPoints.textContent = totalPoints.toFixed(1).replace(".", ",");
    }

    if (btnDrawerCreateExam) {
      btnDrawerCreateExam.disabled = (count === 0);
    }

    // Atualiza visibilidade do botão flutuante se a gaveta estiver fechada e na aba Banco de Questões
    const isDrawerOpen = !drawerNewExam?.classList.contains("hidden");
    if (activeTab === "bank") {
      if (!isDrawerOpen && count > 0) {
        btnDrawerToggleFloating?.classList.remove("hidden");
        btnDrawerToggleFloating?.classList.add("flex");
      } else if (count === 0) {
        btnDrawerToggleFloating?.classList.add("hidden");
        btnDrawerToggleFloating?.classList.remove("flex");
      }
    } else {
      btnDrawerToggleFloating?.classList.add("hidden");
      btnDrawerToggleFloating?.classList.remove("flex");
      drawerNewExam?.classList.add("hidden");
      drawerNewExam?.classList.remove("flex");
      if (mainContentWrapper) {
        mainContentWrapper.style.marginRight = "auto";
        mainContentWrapper.style.maxWidth = "1440px";
      }
    }

    renderDrawerList();
  }

  function renderDrawerList() {
    if (!drawerQuestionsList) return;
    drawerQuestionsList.innerHTML = "";

    if (drawerQuestions.length === 0) {
      drawerQuestionsList.innerHTML = `
        <div class="h-full min-h-[260px] flex flex-col items-center justify-center text-center p-6 text-on-surface-variant select-none">
          <div class="w-14 h-14 rounded-2xl bg-surface-container-low flex items-center justify-center text-outline mb-3">
            <span class="material-symbols-outlined text-[30px]">playlist_add</span>
          </div>
          <h4 class="font-headline-md text-sm font-bold text-on-surface mb-1">Nenhuma questão na prova</h4>
          <p class="text-xs text-on-surface-variant leading-relaxed max-w-[220px]">
            Clique em <strong>+ Usar em Nova Prova</strong> nas questões do acervo para adicioná-las aqui.
          </p>
        </div>
      `;
      return;
    }

    drawerQuestions.forEach((q, idx) => {
      const card = document.createElement("div");
      card.className = "bg-white hover:bg-slate-50/80 rounded-xl p-3.5 border border-slate-200/90 hover:border-slate-300 flex flex-col gap-2 transition-all relative group shadow-none";

      const disc = q.discipline || "GERAL";
      const pts = parseFloat(q.points) || 1.0;
      const ptsStr = `${pts.toFixed(1).replace(".", ",")} pt`;

      card.innerHTML = `
        <div class="flex items-center justify-between gap-2">
          <div class="flex items-center gap-1.5 flex-wrap">
            <span class="w-5 h-5 rounded-md bg-primary-fixed text-on-primary-fixed text-[11px] font-bold flex items-center justify-center shadow-xs">
              ${idx + 1}
            </span>
            <span class="text-[11px] font-bold text-primary px-2 py-0.5 rounded-full bg-primary-fixed/40">
              ${escapeHtml(disc)}
            </span>
            <span class="text-[11px] font-semibold text-secondary">
              ${ptsStr}
            </span>
            ${q.grade_year ? `<span class="text-[10px] px-1.5 py-0.5 rounded bg-surface-container text-on-surface-variant font-medium">${escapeHtml(q.grade_year)}</span>` : ""}
          </div>
          <button type="button" class="btn-remove-drawer-q text-outline hover:text-error p-1 rounded-lg hover:bg-error-container/40 transition-colors cursor-pointer" title="Remover questão">
            <span class="material-symbols-outlined text-[18px]">close</span>
          </button>
        </div>

        <p class="text-xs text-on-surface line-clamp-2 leading-relaxed">
          ${escapeHtml(q.statement || "Sem enunciado")}
        </p>

        ${q.bncc_code ? `
          <div class="pt-1 flex items-center gap-1 text-[10px] font-mono font-bold text-amber-900 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200 w-fit">
            <span class="material-symbols-outlined text-[12px]">sell</span>
            <span>${escapeHtml(q.bncc_code)}</span>
          </div>
        ` : ""}
      `;

      card.querySelector(".btn-remove-drawer-q")?.addEventListener("click", () => {
        removeQuestionFromDrawer(idx);
      });

      drawerQuestionsList.appendChild(card);
    });

    if (window.renderMathInElement) {
      try {
        renderMathInElement(drawerQuestionsList, {
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
  }

  function openCreateModalFromDrawer() {
    if (drawerQuestions.length === 0) {
      showToast("Adicione ao menos uma questão para criar a prova.", "warning");
      return;
    }

    // Campos em branco para o professor preencher livremente
    const has5Alts = drawerQuestions.some(q => q.alternatives && q.alternatives.length >= 5);

    openCreateModal({
      title: "",
      discipline: "",
      grade_year: "9º ANO",
      classroom: "",
      school_name: "",
      preset: "standard",
      alt_mode: has5Alts ? 5 : 4,
      columns: 2,
      include_answer_sheet: true,
      from_drawer: true
    });

    // Ativar a opção "Selecionar do Banco" internamente
    const bankRadio = document.querySelector('input[name="create_type"][value="bank"]');
    if (bankRadio) bankRadio.checked = true;

    // Sincronizar selectedBankQuestions com as questões da gaveta
    selectedBankQuestions.clear();
    drawerQuestions.forEach(q => {
      if (q.id) selectedBankQuestions.add(q.id);
    });
  }

  async function createExamFromDrawer() {
    if (drawerQuestions.length === 0) {
      showToast("Adicione ao menos uma questão para criar a prova.", "warning");
      return;
    }

    // Identificar a disciplina e ano mais frequentes
    const discCounts = {};
    const gradeCounts = {};
    drawerQuestions.forEach(q => {
      const d = (q.discipline || "MATEMÁTICA").trim().toUpperCase();
      discCounts[d] = (discCounts[d] || 0) + 1;
      const g = (q.grade_year || "9º ANO").trim().toUpperCase();
      gradeCounts[g] = (gradeCounts[g] || 0) + 1;
    });

    const primaryDisc = Object.keys(discCounts).sort((a, b) => discCounts[b] - discCounts[a])[0] || "MATEMÁTICA";
    const primaryGrade = Object.keys(gradeCounts).sort((a, b) => gradeCounts[b] - gradeCounts[a])[0] || "9º ANO";

    const totalPts = drawerQuestions.reduce((acc, q) => acc + (parseFloat(q.points) || 1.0), 0);

    const questionsPayload = drawerQuestions.map((q, idx) => ({
      question_number: idx + 1,
      statement: q.statement || "",
      points: parseFloat(q.points) || 1.0,
      image_url: q.image_url || "",
      alternatives: (q.alternatives || []).map(a => {
        const altImg = a.image_url || (a.image ? a.image.url : "") || "";
        const altWidth = a.image_width || (a.image ? a.image.width : "180px") || "180px";
        const altAlign = a.image_align || (a.image ? a.image.align : "center") || "center";
        return {
          letter: a.letter,
          text: a.text || "",
          is_correct: Boolean(a.is_correct),
          image_url: altImg,
          image_width: altWidth,
          image_align: altAlign,
          image: altImg ? { url: altImg, width: altWidth, align: altAlign } : null
        };
      })
    }));

    const payload = {
      title: `Avaliação de ${primaryDisc} - ${primaryGrade}`,
      school_name: "SEMED - LAGOA DA CANOA",
      institution: "PREFEITURA MUNICIPAL DE LAGOA DA CANOA - SEMED",
      discipline: primaryDisc,
      grade_year: primaryGrade,
      classroom: "TURMA A",
      shift: "MATUTINO",
      max_score: Math.max(10.0, totalPts),
      columns_layout: 2,
      font_size: "medium",
      header_style: "standard",
      include_header: true,
      footer_text: "Boa Prova!",
      include_answer_sheet: 1,
      questions: questionsPayload
    };

    btnDrawerCreateExam.disabled = true;
    const originalBtnHtml = btnDrawerCreateExam.innerHTML;
    btnDrawerCreateExam.innerHTML = `
      <span class="material-symbols-outlined text-[20px] animate-spin">progress_activity</span>
      <span>Criando Prova...</span>
    `;

    try {
      const res = await apiFetch("/api/exam-builder/exams", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const created = await res.json();
        showToast("Prova criada com sucesso! Redirecionando para o editor...", "success");
        drawerQuestions = [];
        updateDrawerUI();
        setTimeout(() => {
          window.location.href = `/elaborador?exam_id=${created.id}`;
        }, 500);
      } else {
        const err = await res.json();
        showToast(err.detail || "Erro ao criar avaliação.", "error");
        btnDrawerCreateExam.disabled = false;
        btnDrawerCreateExam.innerHTML = originalBtnHtml;
      }
    } catch (e) {
      console.error("Erro na criação:", e);
      showToast("Falha de conexão ao criar a avaliação.", "error");
      btnDrawerCreateExam.disabled = false;
      btnDrawerCreateExam.innerHTML = originalBtnHtml;
    }
  }

  // =========================================================================
  // Gerador de Questões Inéditas com IA (Groq Cloud - Llama 3.1 8B + BNCC)
  // =========================================================================
  let currentGeneratedAIItem = null;

  function setupAIQuestionGenerator() {
    const btnOpenAI = document.getElementById("btn-open-ai-generator");
    const modalAI = document.getElementById("modal-ai-question-generator");
    const btnCloseAI = document.getElementById("btn-close-ai-generator");
    const btnCancelAI = document.getElementById("btn-cancel-ai-generator");
    const btnPickBncc = document.getElementById("btn-ai-pick-bncc");
    const btnSubmitGenerate = document.getElementById("btn-ai-submit-generate");
    const btnRegenerate = document.getElementById("btn-ai-regenerate");
    const btnSaveBank = document.getElementById("btn-ai-save-bank");
    const btnAddDrawer = document.getElementById("btn-ai-add-drawer");

    const inputDiscipline = document.getElementById("ai-input-discipline");
    const inputGrade = document.getElementById("ai-input-grade");
    const inputBncc = document.getElementById("ai-input-bncc");
    const inputDifficulty = document.getElementById("ai-input-difficulty");
    const inputNumAlts = document.getElementById("ai-input-num-alts");
    const inputTheme = document.getElementById("ai-input-theme");
    const inputCustom = document.getElementById("ai-input-custom");

    const loadingState = document.getElementById("ai-loading-state");
    const previewCard = document.getElementById("ai-preview-card");
    const keyWarning = document.getElementById("ai-key-warning");

    if (!modalAI) return;

    async function checkGroqKeyStatus() {
      try {
        const res = await apiFetch("/api/settings");
        if (res.ok) {
          const s = await res.json();
          if (keyWarning) {
            if (!s.has_groq_api_key) {
              keyWarning.classList.remove("hidden");
            } else {
              keyWarning.classList.add("hidden");
            }
          }
        }
      } catch (e) {
        console.warn("Erro ao checar status da chave Groq:", e);
      }
    }

    function openAIModal() {
      if (inputDiscipline && bankSelectDiscipline && bankSelectDiscipline.value) {
        inputDiscipline.value = bankSelectDiscipline.value;
      }
      if (inputGrade && bankSelectGrade && bankSelectGrade.value) {
        inputGrade.value = bankSelectGrade.value;
      }
      if (inputBncc && bankInputBncc && bankInputBncc.value) {
        inputBncc.value = bankInputBncc.value;
      }

      modalAI.classList.add("active");
      checkGroqKeyStatus();
    }

    function closeAIModal() {
      modalAI.classList.remove("active");
    }

    btnOpenAI?.addEventListener("click", openAIModal);
    btnCloseAI?.addEventListener("click", closeAIModal);
    btnCancelAI?.addEventListener("click", closeAIModal);

    modalAI.addEventListener("click", (e) => {
      if (e.target === modalAI) closeAIModal();
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && modalAI.classList.contains("active")) {
        closeAIModal();
      }
    });

    btnPickBncc?.addEventListener("click", () => {
      bnccPickerTarget = inputBncc;
      openBnccModal();
    });

    async function handleGenerateQuestion() {
      const discipline = inputDiscipline ? inputDiscipline.value : "Matemática";
      const gradeYear = inputGrade ? inputGrade.value : "5º Ano";
      const bnccCode = inputBncc ? inputBncc.value.trim() : "";
      const difficulty = inputDifficulty ? inputDifficulty.value : "Médio";
      const numAlternatives = inputNumAlts ? parseInt(inputNumAlts.value, 10) : 4;
      const localTheme = inputTheme ? inputTheme.value.trim() : "";
      const customPrompt = inputCustom ? inputCustom.value.trim() : "";

      if (loadingState) loadingState.classList.remove("hidden");
      if (previewCard) previewCard.classList.add("hidden");
      if (btnSubmitGenerate) btnSubmitGenerate.disabled = true;

      try {
        const res = await apiFetch("/api/exam-builder/ai/generate-question", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            discipline: discipline,
            grade_year: gradeYear,
            bncc_code: bnccCode,
            difficulty: difficulty,
            num_alternatives: numAlternatives,
            local_theme: localTheme,
            custom_prompt: customPrompt
          })
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          let errMsg = "Erro ao conectar com a API da Groq.";
          if (typeof errData.detail === "string") {
            errMsg = errData.detail;
          } else if (Array.isArray(errData.detail)) {
            errMsg = errData.detail.map(d => (d && d.msg) ? `${d.loc ? d.loc.join('.') + ': ' : ''}${d.msg}` : JSON.stringify(d)).join("; ");
          } else if (errData.detail && typeof errData.detail === "object") {
            errMsg = JSON.stringify(errData.detail);
          }
          if (typeof errMsg === "string" && errMsg.toLowerCase().includes("chave") && keyWarning) {
            keyWarning.classList.remove("hidden");
          }
          throw new Error(errMsg);
        }

        const data = await res.json();
        currentGeneratedAIItem = data;
        renderAIGeneratedPreview(data);

        showToast("Questão gerada com sucesso pela IA!", "success");
      } catch (err) {
        showToast(err.message || "Erro na geração com IA.", "error");
      } finally {
        if (loadingState) loadingState.classList.add("hidden");
        if (btnSubmitGenerate) btnSubmitGenerate.disabled = false;
      }
    }

    btnSubmitGenerate?.addEventListener("click", handleGenerateQuestion);
    btnRegenerate?.addEventListener("click", handleGenerateQuestion);

    function renderAIGeneratedPreview(item) {
      if (!previewCard) return;

      const badgeBncc = document.getElementById("ai-preview-badge-bncc");
      const badgeDisc = document.getElementById("ai-preview-badge-disc");
      const badgeDiff = document.getElementById("ai-preview-badge-diff");
      const txtStatement = document.getElementById("ai-preview-statement");
      const txtExplanation = document.getElementById("ai-preview-explanation");
      const altsContainer = document.getElementById("ai-preview-alternatives-list");

      if (badgeBncc) {
        badgeBncc.textContent = item.bncc_code || "BNCC Livre";
        badgeBncc.style.display = item.bncc_code ? "inline-block" : "none";
      }
      if (badgeDisc) badgeDisc.textContent = item.discipline || "Geral";
      if (badgeDiff) badgeDiff.textContent = item.difficulty || "Médio";
      if (txtStatement) txtStatement.value = item.statement || "";
      if (txtExplanation) txtExplanation.value = item.explanation || "";

      if (altsContainer) {
        altsContainer.innerHTML = "";
        const alts = item.alternatives || [];
        alts.forEach((alt, idx) => {
          const row = document.createElement("div");
          row.className = "flex items-center gap-2.5 p-2 rounded-xl bg-slate-50 border border-slate-200/90 focus-within:border-blue-400 focus-within:bg-blue-50/20 transition-all";

          const isChecked = !!alt.is_correct;
          row.innerHTML = `
            <label class="flex items-center gap-2 cursor-pointer select-none pl-1">
              <input type="radio" name="ai-correct-radio" value="${escapeHtml(alt.letter)}" ${isChecked ? "checked" : ""} class="w-4 h-4 text-emerald-600 focus:ring-emerald-500 cursor-pointer">
              <span class="w-6 h-6 rounded-lg bg-slate-200 font-bold text-xs text-slate-800 flex items-center justify-center">${escapeHtml(alt.letter)}</span>
            </label>
            <input type="text" class="ai-alt-input flex-1 bg-transparent border-0 text-xs sm:text-sm text-slate-800 focus:outline-none" value="${escapeHtml(alt.text || "")}" data-letter="${escapeHtml(alt.letter)}" placeholder="Texto da alternativa ${escapeHtml(alt.letter)}">
          `;
          altsContainer.appendChild(row);
        });
      }

      previewCard.classList.remove("hidden");
      previewCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
      applyKaTeXMath(previewCard);
    }

    async function saveAIQuestionCore() {
      if (!currentGeneratedAIItem) return null;

      const txtStatement = document.getElementById("ai-preview-statement");
      const txtExplanation = document.getElementById("ai-preview-explanation");
      const statementVal = txtStatement ? txtStatement.value.trim() : "";

      if (!statementVal) {
        showToast("O enunciado da questão não pode ficar vazio.", "warning");
        txtStatement?.focus();
        return null;
      }

      const altInputs = document.querySelectorAll(".ai-alt-input");
      const selectedRadio = document.querySelector('input[name="ai-correct-radio"]:checked');
      const correctLetter = selectedRadio ? selectedRadio.value : "A";

      const finalAlternatives = [];
      altInputs.forEach((inp, idx) => {
        const letVal = inp.dataset.letter || String.fromCharCode(65 + idx);
        const textVal = inp.value.trim();
        finalAlternatives.push({
          letter: letVal,
          text: textVal,
          is_correct: (letVal === correctLetter),
          order_index: idx
        });
      });

      const payload = {
        statement: statementVal,
        discipline: currentGeneratedAIItem.discipline || (inputDiscipline ? inputDiscipline.value : "Matemática"),
        grade_year: currentGeneratedAIItem.grade_year || (inputGrade ? inputGrade.value : "5º Ano"),
        bncc_code: currentGeneratedAIItem.bncc_code || (inputBncc ? inputBncc.value.trim() : ""),
        difficulty: currentGeneratedAIItem.difficulty || (inputDifficulty ? inputDifficulty.value : "Médio"),
        points: 1.0,
        alternatives: finalAlternatives,
        explanation: txtExplanation ? txtExplanation.value.trim() : ""
      };

      const res = await apiFetch("/api/exam-builder/ai/save-to-bank", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        let errMsg = "Erro ao salvar no banco.";
        if (typeof err.detail === "string") {
          errMsg = err.detail;
        } else if (Array.isArray(err.detail)) {
          errMsg = err.detail.map(d => (d && d.msg) ? `${d.loc ? d.loc.join('.') + ': ' : ''}${d.msg}` : JSON.stringify(d)).join("; ");
        } else if (err.detail && typeof err.detail === "object") {
          errMsg = JSON.stringify(err.detail);
        }
        throw new Error(errMsg);
      }

      const savedData = await res.json();
      return {
        ...payload,
        id: savedData.id,
        created_at: new Date().toISOString()
      };
    }

    async function handleSaveAIToBank() {
      if (btnSaveBank) {
        btnSaveBank.disabled = true;
        btnSaveBank.innerHTML = '<span class="material-symbols-outlined text-[18px] animate-spin">progress_activity</span> Salvando...';
      }

      try {
        const savedItem = await saveAIQuestionCore();
        if (!savedItem) return;

        showToast("Questão adicionada ao Banco de Questões com sucesso!", "success");
        closeAIModal();

        if (activeTab !== "bank") {
          switchTab("bank");
        } else {
          loadBankQuestions(true);
        }
      } catch (e) {
        showToast(e.message || "Falha ao salvar questão.", "error");
      } finally {
        if (btnSaveBank) {
          btnSaveBank.disabled = false;
          btnSaveBank.innerHTML = '<span class="material-symbols-outlined text-[18px] text-blue-600">bookmark_add</span> <span>Salvar no Banco</span>';
        }
      }
    }

    async function handleSaveAndAddToDrawer() {
      if (btnAddDrawer) {
        btnAddDrawer.disabled = true;
        btnAddDrawer.innerHTML = '<span class="material-symbols-outlined text-[18px] animate-spin">progress_activity</span> Adicionando...';
      }

      try {
        const savedItem = await saveAIQuestionCore();
        if (!savedItem) return;

        drawerQuestions.push(savedItem);
        drawerUserOpened = true;
        updateDrawerUI();
        renderBankQuestionsButtonsState();
        openDrawer();

        showToast(`Questão adicionada à prova! (${drawerQuestions.length} questões)`, "success");
        closeAIModal();

        loadBankQuestions(true);
      } catch (e) {
        showToast(e.message || "Falha ao adicionar à prova.", "error");
      } finally {
        if (btnAddDrawer) {
          btnAddDrawer.disabled = false;
          btnAddDrawer.innerHTML = '<span class="material-symbols-outlined text-[18px]">add_circle</span> <span>Salvar &amp; Usar na Prova</span>';
        }
      }
    }

    btnSaveBank?.addEventListener("click", handleSaveAIToBank);
    btnAddDrawer?.addEventListener("click", handleSaveAndAddToDrawer);
  }

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  window.addEventListener("resize", () => {
    if (activeTab === "bank" && drawerUserOpened && !drawerNewExam?.classList.contains("hidden")) {
      if (window.innerWidth >= 1200 && mainContentWrapper) {
        mainContentWrapper.style.marginRight = "440px";
        mainContentWrapper.style.maxWidth = "calc(100vw - 460px)";
      } else if (mainContentWrapper) {
        mainContentWrapper.style.marginRight = "auto";
        mainContentWrapper.style.maxWidth = "1440px";
      }
    }
  });

});
