/**
 * MANUAL DA PLATAFORMA - PROVA CANOA (SEMED • LAGOA DA CANOA)
 * Interatividade, Busca em Tempo Real, Simuladores OMR e Navegação
 */

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initSearch();
  initScrollspy();
  initFaqAccordion();
  initMobileDrawer();
  initLightbox();
});

// --- Theme Management ---
function initTheme() {
  const savedTheme = localStorage.getItem("omr_docs_theme") || "light";
  document.documentElement.setAttribute("data-theme", savedTheme);
  updateThemeIcon(savedTheme);

  const toggleBtn = document.getElementById("btn-theme-toggle");
  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-theme") || "light";
      const next = current === "light" ? "dark" : "light";
      document.documentElement.setAttribute("data-theme", next);
      localStorage.setItem("omr_docs_theme", next);
      updateThemeIcon(next);
    });
  }
}

function updateThemeIcon(theme) {
  const sun = document.getElementById("icon-sun");
  const moon = document.getElementById("icon-moon");
  if (!sun || !moon) return;
  if (theme === "dark") {
    sun.style.display = "block";
    moon.style.display = "none";
  } else {
    sun.style.display = "none";
    moon.style.display = "block";
  }
}

// --- Live Instant Search ---
function initSearch() {
  const searchInput = document.getElementById("docs-search-input");
  if (!searchInput) return;

  // Shortcut Ctrl + K or '/'
  window.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      searchInput.focus();
    } else if (e.key === "/" && document.activeElement !== searchInput) {
      e.preventDefault();
      searchInput.focus();
    }
  });

  searchInput.addEventListener("input", (e) => {
    const query = e.target.value.toLowerCase().trim();
    const sections = document.querySelectorAll(".docs-section");
    const navItems = document.querySelectorAll(".sidebar-nav-item");

    if (!query) {
      sections.forEach(s => s.style.display = "");
      navItems.forEach(n => n.style.display = "");
      return;
    }

    sections.forEach(section => {
      const text = section.textContent.toLowerCase();
      const match = text.includes(query);
      section.style.display = match ? "" : "none";
    });

    navItems.forEach(navItem => {
      const targetId = navItem.querySelector("a")?.getAttribute("href")?.replace("#", "");
      if (!targetId) return;
      const targetSection = document.getElementById(targetId);
      if (targetSection) {
        navItem.style.display = targetSection.style.display;
      }
    });
  });
}

// --- Scrollspy Navigation ---
function initScrollspy() {
  const sections = document.querySelectorAll(".docs-section");
  const navItems = document.querySelectorAll(".sidebar-nav-item");
  if (!sections.length || !navItems.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.id;
        navItems.forEach(item => {
          const href = item.querySelector("a")?.getAttribute("href");
          if (href === `#${id}`) {
            navItems.forEach(i => i.classList.remove("active"));
            item.classList.add("active");
          }
        });
      }
    });
  }, {
    rootMargin: "-20% 0px -70% 0px"
  });

  sections.forEach(section => observer.observe(section));
}

// --- FAQ Accordion ---
function initFaqAccordion() {
  const items = document.querySelectorAll(".faq-item");
  items.forEach(item => {
    const questionBtn = item.querySelector(".faq-question");
    if (questionBtn) {
      questionBtn.addEventListener("click", () => {
        const isOpen = item.classList.contains("open");
        items.forEach(i => i.classList.remove("open"));
        if (!isOpen) item.classList.add("open");
      });
    }
  });
}

// --- Mobile Navigation Drawer ---
function initMobileDrawer() {
  const btn = document.getElementById("btn-mobile-menu");
  const sidebar = document.getElementById("docs-sidebar");
  if (!btn || !sidebar) return;

  btn.addEventListener("click", (e) => {
    e.stopPropagation();
    sidebar.classList.toggle("open");
  });

  document.addEventListener("click", (e) => {
    if (sidebar.classList.contains("open") && !sidebar.contains(e.target) && e.target !== btn) {
      sidebar.classList.remove("open");
    }
  });

  sidebar.querySelectorAll("a").forEach(link => {
    link.addEventListener("click", () => {
      sidebar.classList.remove("open");
    });
  });
}

// --- GIF Lightbox Modal ---
function initLightbox() {
  let modal = document.querySelector(".gif-lightbox-modal");
  if (!modal) {
    modal = document.createElement("div");
    modal.className = "gif-lightbox-modal";
    modal.innerHTML = `
      <div class="gif-lightbox-content">
        <button type="button" class="gif-lightbox-close" aria-label="Fechar">&times;</button>
        <img src="" alt="Demonstração Ampliada">
      </div>
    `;
    document.body.appendChild(modal);

    const closeBtn = modal.querySelector(".gif-lightbox-close");
    closeBtn.addEventListener("click", () => modal.classList.remove("active"));
    modal.addEventListener("click", (e) => {
      if (e.target === modal) modal.classList.remove("active");
    });
    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && modal.classList.contains("active")) {
        modal.classList.remove("active");
      }
    });
  }

  const modalImg = modal.querySelector("img");
  document.querySelectorAll(".gif-media-frame").forEach(frame => {
    frame.addEventListener("click", () => {
      const img = frame.querySelector("img");
      if (img && img.src) {
        modalImg.src = img.src;
        modal.classList.add("active");
      }
    });
  });
}
