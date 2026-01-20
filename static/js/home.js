document.addEventListener("DOMContentLoaded", () => {
  // ==================== ESTADO GLOBAL ====================
  let LOGGED_USER = {
    username: null,
    email: null,
    password_masked: null,
    is_admin: false,
  };

  let cardLinks = {};
  let currentCardFile = null;
  let userLiked = false;
  const originalCardsOrder = [];

  // ==================== UTILITÁRIOS ====================
  
  function hideAllOverlays() {
    document.querySelectorAll(".popup-overlay.show").forEach(ov => ov.classList.remove("show"));
  }

  function blockScroll() {
    document.body.classList.add("no-scroll");
  }

  function unblockScroll() {
    document.body.classList.remove("no-scroll");
  }

  function updateScrollLock() {
    const anyOverlayShown = document.querySelectorAll(".popup-overlay.show").length > 0;
    anyOverlayShown ? blockScroll() : unblockScroll();
  }

  function showQuickWarning(message, type = "error") {
    const toastContainer = document.getElementById("toast-container");
    const toastId = "toast-" + Date.now();
    
    const toastEl = document.createElement("div");
    toastEl.id = toastId;
    toastEl.className = `toast toast-${type}`;
    toastEl.setAttribute("role", "alert");
    
    const icons = {
      success: "✓",
      error: "✕",
      warning: "⚠",
      info: "ℹ"
    };
    
    toastEl.innerHTML = `
      <span class="toast-icon">${icons[type] || icons.info}</span>
      <span class="toast-message">${escapeHtml(message)}</span>
      <button class="toast-close" aria-label="Fechar notificação">×</button>
    `;
    
    toastContainer.appendChild(toastEl);
    
    // Trigger animação de entrada
    setTimeout(() => {
      toastEl.classList.add("show");
    }, 10);
    
    // Fechar pelo botão
    toastEl.querySelector(".toast-close").addEventListener("click", () => {
      removeToast(toastId);
    });
    
    // Fechar automaticamente após 3.5s
    const autoCloseTimer = setTimeout(() => {
      removeToast(toastId);
    }, 3500);
    
    // Remover timer se o toast for fechado manualmente
    toastEl.addEventListener("transitionend", () => {
      if (!toastEl.classList.contains("show")) {
        clearTimeout(autoCloseTimer);
        toastEl.remove();
      }
    });
  }
  
  function removeToast(toastId) {
    const toastEl = document.getElementById(toastId);
    if (toastEl) {
      toastEl.classList.remove("show");
      setTimeout(() => {
        if (toastEl && toastEl.parentNode) {
          toastEl.remove();
        }
      }, 300);
    }
  }
  
  function escapeHtml(text) {
    const map = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;"
    };
    return text.replace(/[&<>"']/g, (char) => map[char]);
  }

  // ==================== PASSWORD TOGGLE ==================== 
  
  function setupPasswordToggle() {
    const passwordToggles = document.querySelectorAll(".password-toggle");
    
    passwordToggles.forEach(toggle => {
      toggle.addEventListener("click", (e) => {
        e.preventDefault();
        
        const wrapper = toggle.closest(".password-wrapper");
        const passwordField = wrapper.querySelector(".password-field");
        const eyeOpen = toggle.querySelector(".eye-open");
        const eyeClosed = toggle.querySelector(".eye-closed");
        
        const isPassword = passwordField.type === "password";
        
        if (isPassword) {
          passwordField.type = "text";
          eyeOpen.style.display = "none";
          eyeClosed.style.display = "block";
        } else {
          passwordField.type = "password";
          eyeOpen.style.display = "block";
          eyeClosed.style.display = "none";
        }
      });
    });
  }

  // ==================== DADOS DO USUÁRIO ====================

  function updateLoggedUser(username, email = "", password_masked = "") {
    LOGGED_USER.username = username;
    LOGGED_USER.email = email;
    LOGGED_USER.password_masked = password_masked;
  }

  function updateAccountPopupFields(username, email, passwordMasked) {
    const inputUsername = document.getElementById("account-username-popup");
    const inputEmail = document.getElementById("account-email-popup");
    const inputPassword = document.getElementById("account-password");

    if (inputUsername) inputUsername.value = username;
    if (inputEmail && email) inputEmail.value = email;
    if (inputPassword && passwordMasked) inputPassword.value = passwordMasked;
  }

  function updateCommentInterface() {
    const commentInput = document.getElementById("comment-input");
    const commentBtn = document.getElementById("comment-submit");
    if (!commentInput || !commentBtn) return;

    if (LOGGED_USER.username) {
      commentInput.disabled = false;
      commentBtn.disabled = false;
      commentInput.placeholder = "Escreva seu comentário...";
    } else {
      commentInput.disabled = true;
      commentBtn.disabled = true;
      commentInput.placeholder = "Faça login para comentar";
    }
  }

  // Carrega dados do usuário atual
  fetch("/api/current_user")
    .then((res) => res.json())
    .then((data) => {
      if (data.logged_in) {
        updateLoggedUser(data.username, data.email || "", data.password_masked || "");
        LOGGED_USER.is_admin = data.is_admin === true || data.is_admin === "true";
        updateAccountPopupFields(LOGGED_USER.username, LOGGED_USER.email, LOGGED_USER.password_masked);
      }
    })
    .catch((err) => console.error("Erro ao carregar usuário:", err));

  // ==================== DARK MODE ====================

  const toggleBtn = document.getElementById("dark-mode-toggle");
  const body = document.body;
  const footer = document.querySelector("footer");

  if (localStorage.getItem("dark-mode") === "enabled") {
    body.classList.add("dark-mode");
    footer.classList.add("dark-mode");
  }

  toggleBtn.addEventListener("click", () => {
    body.classList.toggle("dark-mode");
    footer.classList.toggle("dark-mode");
    localStorage.setItem("dark-mode", body.classList.contains("dark-mode") ? "enabled" : "disabled");
  });

  // ==================== SETUP PASSWORD TOGGLE ==================== 
  setupPasswordToggle();

  // ==================== SLIDESHOW ====================

  const slideshowContainer = document.getElementById("background-slideshow");
  slideImages.forEach((src) => {
    const div = document.createElement("div");
    div.classList.add("bg-slide");
    div.style.backgroundImage = `url(${src})`;
    div.style.opacity = "0";
    slideshowContainer.appendChild(div);
  });

  const slides = document.querySelectorAll(".bg-slide");
  let currentSlide = 0;

  function showSlide(index) {
    slides.forEach((slide, i) => {
      slide.style.opacity = i === index ? "1" : "0";
    });
  }

  function getNextSlideIndex() {
    let next;
    do {
      next = Math.floor(Math.random() * slides.length);
    } while (next === currentSlide);
    return next;
  }

  showSlide(currentSlide);
  setInterval(() => {
    currentSlide = getNextSlideIndex();
    showSlide(currentSlide);
  }, 5000);

  // ==================== POPUP DE CARDS ====================

  const popupOverlay = document.getElementById("popup-overlay");
  const popupImage = document.getElementById("popup-image");
  const popupTitle = document.getElementById("popup-title");
  const popupDescription = document.getElementById("popup-description");
  const popupClose = document.getElementById("popup-close");
  const cards = document.querySelectorAll(".card");

  originalCardsOrder.push(...cards);

  cards.forEach((card) => {
    if (card.dataset.visible !== "true") card.style.display = "none";
  });

  function imageExists(url) {
    const xhr = new XMLHttpRequest();
    xhr.open("HEAD", url, false);
    try {
      xhr.send();
      return xhr.status === 200;
    } catch {
      return false;
    }
  }

  function getTitleImage(baseName) {
    const exts = ["png", "jpg", "jpeg", "webp"];
    for (const ext of exts) {
      const path = `/static/images/titles/${baseName}.${ext}`;
      if (imageExists(path)) return path;
    }
    return null;
  }

  function loadLikes(fileName) {
    currentCardFile = fileName;
    fetch(`/get_likes/${encodeURIComponent(fileName)}`, { credentials: "same-origin" })
      .then((res) => res.json())
      .then((data) => {
        const likeCount = document.getElementById("like-count");
        if (likeCount) likeCount.textContent = data.likes;
        userLiked = data.user_liked;
        const btnLike = document.getElementById("btn-like");
        if (btnLike) userLiked ? btnLike.classList.add("liked") : btnLike.classList.remove("liked");
      })
      .catch((err) => console.error("Erro ao carregar likes:", err));
  }

  function openPopup(cardImgSrc, titleImgSrc, description, cardFileName) {
    popupImage.src = cardImgSrc;
    popupImage.classList.add("card-image");

    if (titleImgSrc) {
      popupTitle.innerHTML = `<img src="${titleImgSrc}" alt="Título" style="width:100%; height:auto;">`;
    } else {
      popupTitle.innerHTML = "";
    }

    popupDescription.textContent = description || "";
    popupOverlay.classList.add("show");
    updateScrollLock();
    updateCommentInterface();
    loadComments(cardFileName);
  }

  cards.forEach((card) => {
    card.addEventListener("click", () => {
      const img = card.querySelector("img");
      const cardImgSrc = img?.src || "";
      const baseName = cardImgSrc.split("/").pop().split(".")[0];
      const titleImgSrc = getTitleImage(baseName);
      const description = card.dataset.description;
      const cardFileName = cardImgSrc.split("/").pop();

      openPopup(cardImgSrc, titleImgSrc, description, cardFileName);
    });
  });

  popupClose.addEventListener("click", () => {
    popupOverlay.classList.remove("show");
    updateScrollLock();
  });

  popupOverlay.addEventListener("click", (e) => {
    if (e.target === popupOverlay) {
      popupOverlay.classList.remove("show");
      updateScrollLock();
    }
  });

  // ==================== LINKS DOS CARDS ====================

  const btnDownloadMap = document.getElementById("btn-download-map");
  const btnReadStory = document.getElementById("btn-read-story");

  function setPopupLinks(fileName) {
    const links = cardLinks[fileName];
    
    if (links?.mapa) {
      btnDownloadMap.onclick = () => window.open(links.mapa, "_blank");
      btnDownloadMap.classList.remove("disabled");
    } else {
      btnDownloadMap.onclick = null;
      btnDownloadMap.classList.add("disabled");
    }

    if (links?.historia) {
      btnReadStory.onclick = () => window.open(links.historia, "_blank");
      btnReadStory.classList.remove("disabled");
    } else {
      btnReadStory.onclick = null;
      btnReadStory.classList.add("disabled");
    }
  }

  fetch("/api/links.json")
    .then((res) => res.json())
    .then((data) => {
      cardLinks = data;
      cards.forEach((card) => {
        card.addEventListener("click", () => {
          const cardFileName = popupImage.src.split("/").pop();
          setPopupLinks(cardFileName);
          loadLikes(cardFileName);
        });
      });
    })
    .catch((err) => console.error("Erro ao carregar links:", err));

  // ==================== AUTENTICAÇÃO ====================

  const authOverlay = document.getElementById("auth-popup-overlay");
  const authClose = document.getElementById("auth-popup-close");
  const loginPopup = document.getElementById("login-popup");
  const registerPopup = document.getElementById("register-popup");
  const loginBtn = document.querySelector(".btn-login");
  const registerBtn = document.querySelector(".btn-register");

  function showLogin() {
    loginPopup.style.display = "flex";
    registerPopup.style.display = "none";
    authOverlay.classList.add("show");
    updateScrollLock();
  }

  function showRegister() {
    registerPopup.style.display = "flex";
    loginPopup.style.display = "none";
    authOverlay.classList.add("show");
    updateScrollLock();
  }

  if (loginBtn) loginBtn.addEventListener("click", showLogin);
  if (registerBtn) registerBtn.addEventListener("click", showRegister);

  document.getElementById("switch-to-register").addEventListener("click", showRegister);
  document.getElementById("switch-to-login").addEventListener("click", showLogin);

  authClose.addEventListener("click", () => {
    authOverlay.classList.remove("show");
    updateScrollLock();
  });

  authOverlay.addEventListener("click", (e) => {
    if (e.target === authOverlay) {
      authOverlay.classList.remove("show");
      updateScrollLock();
    }
  });

  // ==================== VALIDAÇÕES ====================

  const BADWORDS = [
    "burro", "idiota", "otario", "palhaco", "lixo", "puta", "caralho", "porra", "merda", "bosta", "cu",
    "0tario", "1diota", "1ixo", "arrombada", "arrombado", "b0sta", "babaca", "babacas", "bicha", "bo5ta",
    "bost4", "bostas", "bostinha", "bostinhas", "buceta", "burr0", "burra", "burras", "burrinho",
    "burrinhos", "burros", "c4ralho", "cacete", "canalha", "canalhas", "cara1ho", "caralh0", "caralha",
    "caralhas", "caralhinho", "caralhinhos", "caralho", "caralhos", "caralo", "cretina", "cretino", "cus",
    "foda", "foder", "fodido", "fudido", "grelo", "idi0ta", "idiot4", "idiota", "idiotas", "idiotinha",
    "idiotinhas", "imbecil", "imbecis", "kct", "l1xo", "lix0", "lixa", "lixas", "lixinho", "lixinhos",
    "lixo", "lixos", "m3rda", "merd4", "merda", "merdas", "merdinha", "merdinhas", "ot4rio", "otar1o",
    "otaria", "otarias", "otariinho", "otariinhos", "otario", "otarios", "p0rra", "p4lhaço", "pa1haço",
    "palaço", "palhaç0", "palhaça", "palhaças", "palhaçinho", "palhaçinhos", "palhaço", "palhaços", "pau",
    "pinto", "piroca", "porr4", "porra", "porras", "porrinha", "porrinhas", "pqp", "put4", "puta", "putas",
    "putinha", "putinhas", "rola", "vadia", "vagabunda", "vagabundo", "veado", "viado", "vsf", "vtnc", "xereca"
  ];

  function validateUsername(value) {
    const trimmed = value.trim();
    const rules = {
      length: trimmed.length >= 5 && trimmed.length <= 20,
      special: /^[A-Za-z0-9_]*$/.test(trimmed),
      firstUpper: /^[A-Z]/.test(trimmed),
      noNumberStart: !/^[0-9]/.test(trimmed),
      badwords: !BADWORDS.some((bad) => trimmed.toLowerCase().includes(bad)),
    };

    Object.entries(rules).forEach(([rule, isValid]) => {
      const id = `rule-username-${rule === "length" ? "length" : rule === "firstUpper" ? "first-upper" : rule === "noNumberStart" ? "no-number-start" : rule}`;
      const el = document.getElementById(id);
      if (el) isValid ? el.classList.add("valid") : el.classList.remove("valid");
    });
  }

  function validateEmail(value) {
    const ruleEl = document.getElementById("rule-email-format");
    if (ruleEl) {
      const isValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
      isValid ? ruleEl.classList.add("valid") : ruleEl.classList.remove("valid");
    }
  }

  function validatePassword(value) {
    const trimmed = value.trim();
    const rules = {
      length: trimmed.length >= 8,
      upper: /[A-Z]/.test(trimmed),
      lower: /[a-z]/.test(trimmed),
      number: /[0-9]/.test(trimmed),
      special: /[!@#$%^&*]/.test(trimmed),
    };

    Object.entries(rules).forEach(([rule, isValid]) => {
      const el = document.getElementById(`rule-password-${rule}`);
      if (el) isValid ? el.classList.add("valid") : el.classList.remove("valid");
    });
  }

  function isCommentClean(comment) {
    return !BADWORDS.some((word) => comment.toLowerCase().includes(word));
  }

  const usernameInput = document.getElementById("username");
  const emailInput = document.getElementById("email");
  const passwordInput = document.getElementById("password");
  const usernameTooltip = document.getElementById("username-tooltip");
  const emailTooltip = document.getElementById("email-tooltip");
  const passwordTooltip = document.getElementById("password-tooltip");

  if (usernameInput) {
    usernameInput.addEventListener("focus", () => usernameTooltip?.classList.add("show"));
    usernameInput.addEventListener("blur", () => usernameTooltip?.classList.remove("show"));
    usernameInput.addEventListener("input", (e) => validateUsername(e.target.value));
  }

  if (emailInput) {
    emailInput.addEventListener("focus", () => emailTooltip?.classList.add("show"));
    emailInput.addEventListener("blur", () => emailTooltip?.classList.remove("show"));
    emailInput.addEventListener("input", (e) => validateEmail(e.target.value));
  }

  if (passwordInput) {
    passwordInput.addEventListener("focus", () => passwordTooltip?.classList.add("show"));
    passwordInput.addEventListener("blur", () => passwordTooltip?.classList.remove("show"));
    passwordInput.addEventListener("input", (e) => validatePassword(e.target.value));
  }

  // ==================== FORMULÁRIO REGISTRAR ====================

  const registerBtnSubmit = document.querySelector("#register-popup .auth-btn");
  const checkbox = document.querySelector("#register-popup .auth-checkbox input");

  function isRegisterFormValid() {
    const usernameValid = document.getElementById("rule-username-length")?.classList.contains("valid") &&
      document.getElementById("rule-username-special")?.classList.contains("valid") &&
      document.getElementById("rule-username-first-upper")?.classList.contains("valid") &&
      document.getElementById("rule-username-no-number-start")?.classList.contains("valid") &&
      document.getElementById("rule-username-badwords")?.classList.contains("valid");

    const emailValid = document.getElementById("rule-email-format")?.classList.contains("valid");

    const passwordValid = document.getElementById("rule-password-length")?.classList.contains("valid") &&
      document.getElementById("rule-password-upper")?.classList.contains("valid") &&
      document.getElementById("rule-password-lower")?.classList.contains("valid") &&
      document.getElementById("rule-password-number")?.classList.contains("valid") &&
      document.getElementById("rule-password-special")?.classList.contains("valid");

    const hasValues = usernameInput.value.trim() && emailInput.value.trim() && passwordInput.value.trim() && checkbox.checked;

    return hasValues && usernameValid && emailValid && passwordValid;
  }

  registerBtnSubmit.addEventListener("click", (e) => {
    e.preventDefault();

    if (!isRegisterFormValid()) {
      showQuickWarning("Preencha todos os campos corretamente.", "error");
      return;
    }

    const payload = {
      username: usernameInput.value.trim(),
      email: emailInput.value.trim(),
      password: passwordInput.value.trim(),
    };

    fetch("/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.status === "success") {
          showQuickWarning(data.message, "success");
          LOGGED_USER.username = payload.username;
          LOGGED_USER.email = payload.email;
          LOGGED_USER.is_admin = data.is_admin || false;

          usernameInput.value = emailInput.value = passwordInput.value = "";
          checkbox.checked = false;

          setTimeout(() => authOverlay.classList.remove("show"), 1000);
          setTimeout(() => location.reload(), 100);
        } else {
          showQuickWarning(data.message, "error");
        }
      })
      .catch((err) => {
        console.error(err);
        showQuickWarning("Erro ao registrar usuário.", "error");
      });
  });

  // ==================== FORMULÁRIO LOGIN ====================

  const loginPopupBtn = document.querySelector("#login-popup .auth-btn");
  const loginEmailInput = document.querySelector("#login-popup input[type='email']");
  const loginPasswordInput = document.querySelector("#login-popup input[type='password']");

  loginPopupBtn.addEventListener("click", (e) => {
    e.preventDefault();
    const emailVal = loginEmailInput.value.trim();
    const passwordVal = loginPasswordInput.value.trim();

    if (!emailVal || !passwordVal) {
      showQuickWarning("Preencha email e senha.", "error");
      return;
    }

    fetch("/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: emailVal, password: passwordVal }),
    })
      .then((res) => res.json())
      .then((data) => {
        showQuickWarning(data.message, data.status === "success" ? "success" : "error");

        if (data.status === "success") {
          authOverlay.classList.remove("show");
          LOGGED_USER.username = data.username;
          LOGGED_USER.email = emailVal;
          LOGGED_USER.is_admin = data.is_admin || false;

          let buttonsHTML = `<span class="welcome-message">Olá, ${data.username}!</span><button class="btn-logout" onclick="location.href='/logout'">Sair</button>`;
          if (data.is_admin) buttonsHTML += `<button class="btn-admin" onclick="location.href='/admin'">Admin</button>`;
          document.querySelector(".auth-buttons").innerHTML = buttonsHTML;

          setTimeout(() => location.reload(), 100);
          updateCommentInterface();
        }
      })
      .catch((err) => {
        console.error(err);
        showQuickWarning("Erro ao fazer login.", "error");
      });
  });

  // ==================== SIDEBAR ====================

  const menuBtn = document.getElementById("menu-btn");
  const sidebar = document.getElementById("sidebar");
  const sidebarOverlay = document.getElementById("sidebar-overlay");
  const sidebarClose = document.getElementById("sidebar-close");

  function openSidebar() {
    sidebar.classList.add("open");
    sidebarOverlay.classList.add("show");
    menuBtn.classList.add("open");
  }

  function closeSidebar() {
    sidebar.classList.remove("open");
    sidebarOverlay.classList.remove("show");
    menuBtn.classList.remove("open");
  }

  menuBtn.addEventListener("click", () => sidebar.classList.contains("open") ? closeSidebar() : openSidebar());
  sidebarClose.addEventListener("click", closeSidebar);
  sidebarOverlay.addEventListener("click", closeSidebar);

  // Quem Somos
  const btnWhoUs = document.getElementById("btn-who-us");
  const whoUsOverlay = document.getElementById("who-us-popup-overlay");
  const whoUsClose = document.getElementById("who-us-popup-close");

  if (btnWhoUs && whoUsOverlay && whoUsClose) {
    btnWhoUs.addEventListener("click", () => {
      closeSidebar();
      whoUsOverlay.classList.add("show");
    });

    whoUsClose.addEventListener("click", () => whoUsOverlay.classList.remove("show"));
    whoUsOverlay.addEventListener("click", (e) => {
      if (e.target === whoUsOverlay) whoUsOverlay.classList.remove("show");
    });
  }

  // ==================== CONTA ====================

  const accountBtn = document.getElementById("btn-user-account");
  const accountOverlay = document.getElementById("account-popup-overlay");
  const accountPopupClose = document.getElementById("account-popup-close");

  accountBtn.addEventListener("click", () => {
    if (!LOGGED_USER.username) {
      closeSidebar();
      showLogin();
      showQuickWarning("Faça login primeiro.", "error");
      return;
    }
    closeSidebar();
    accountOverlay.classList.add("show");
    updateAccountPopupFields(LOGGED_USER.username, LOGGED_USER.email, LOGGED_USER.password_masked);
  });

  accountPopupClose.addEventListener("click", () => accountOverlay.classList.remove("show"));
  accountOverlay.addEventListener("click", (e) => {
    if (e.target === accountOverlay) accountOverlay.classList.remove("show");
  });

  // ==================== DELETAR CONTA ====================

  const deleteAccountBtn = document.getElementById("btn-delete-account");
  const deleteAccountOverlay = document.getElementById("delete-account-popup-overlay");
  const confirmDeleteBtn = document.getElementById("confirm-delete-account");
  const cancelDeleteBtn = document.getElementById("cancel-delete-account");

  if (deleteAccountBtn) deleteAccountBtn.addEventListener("click", () => deleteAccountOverlay.classList.add("show"));
  if (cancelDeleteBtn) cancelDeleteBtn.addEventListener("click", () => deleteAccountOverlay.classList.remove("show"));

  if (confirmDeleteBtn) {
    confirmDeleteBtn.addEventListener("click", () => {
      fetch("/delete_account", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: LOGGED_USER.username }),
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.status === "success") {
            showQuickWarning("Conta deletada.", "success");
            setTimeout(() => window.location.href = "/", 1000);
          } else {
            showQuickWarning(data.message, "error");
          }
        })
        .catch((err) => {
          console.error(err);
          showQuickWarning("Erro ao deletar conta.", "error");
        });
    });
  }

  if (deleteAccountOverlay) {
    deleteAccountOverlay.addEventListener("click", (e) => {
      if (e.target === deleteAccountOverlay) deleteAccountOverlay.classList.remove("show");
    });
  }

  // ==================== RESET SENHA ====================

  const forgotLink = document.getElementById("forgot-password-link");
  const forgotOverlay = document.getElementById("forgot-password-overlay");
  const forgotBtn = document.getElementById("forgot-password-btn");
  const forgotEmailInput = document.getElementById("forgot-password-email");
  const forgotLoading = document.getElementById("forgot-password-loading");
  const closeForgot = document.getElementById("close-forgot-password");

  if (forgotLink) {
    forgotLink.addEventListener("click", (e) => {
      e.preventDefault();
      authOverlay.classList.remove("show");
      forgotOverlay.classList.add("show");
      updateScrollLock();
    });
  }

  if (closeForgot) {
    closeForgot.addEventListener("click", () => {
      forgotOverlay.classList.remove("show");
      authOverlay.classList.add("show");
      loginPopup.style.display = "flex";
      registerPopup.style.display = "none";
      updateScrollLock();
    });
  }

  // Clicando fora do popup de recuperação de senha, volta para login
  forgotOverlay.addEventListener("click", (e) => {
    if (e.target === forgotOverlay) {
      forgotOverlay.classList.remove("show");
      authOverlay.classList.add("show");
      loginPopup.style.display = "flex";
      registerPopup.style.display = "none";
      updateScrollLock();
    }
  });

  if (forgotBtn) {
    forgotBtn.addEventListener("click", async () => {
      const emailVal = forgotEmailInput.value.trim();
      if (!emailVal) {
        showQuickWarning("Digite um email.", "error");
        return;
      }

      forgotLoading.style.display = "flex";
      forgotBtn.disabled = true;

      try {
        const res = await fetch("/forgot_password", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: emailVal }),
        });

        const data = await res.json();
        if (res.ok && data.status === "success") {
          showQuickWarning(data.message, "success");
          forgotOverlay.classList.remove("show");
          authOverlay.classList.add("show");
          loginPopup.style.display = "flex";
          updateScrollLock();
        } else {
          showQuickWarning(data.message || "Erro ao enviar.", "error");
        }
      } catch (err) {
        console.error(err);
        showQuickWarning("Erro de conexão.", "error");
      } finally {
        forgotLoading.style.display = "none";
        forgotBtn.disabled = false;
      }
    });
  }

  // ==================== COMENTÁRIOS ====================

  const commentsContainer = document.getElementById("comments-container");
  const commentInput = document.getElementById("comment-input");
  const commentBtn = document.getElementById("comment-submit");

  function loadComments(cardFileName) {
    if (!cardFileName) return;

    fetch(`/api/comments/${encodeURIComponent(cardFileName)}`, {
      credentials: "same-origin",
      cache: "no-store",
    })
      .then((res) => res.json())
      .then((data) => {
        commentsContainer.innerHTML = "";

        if (!data || Object.keys(data).length === 0) {
          commentsContainer.innerHTML = `<p style="color:gray; padding-top:8px;">Nenhum comentário ainda.</p>`;
          return;
        }

        for (const [user, comment] of Object.entries(data)) {
          const div = document.createElement("div");
          div.classList.add("comment");
          div.innerHTML = `<strong>${user}:</strong> ${comment}`;

          if (LOGGED_USER.username === user || LOGGED_USER.is_admin) {
            const delBtn = document.createElement("button");
            delBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="red" viewBox="0 0 16 16"><path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0z"/><path d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4zM2.5 3h11V2h-11z"/></svg>`;
            delBtn.style.cssText = "margin-left:10px; cursor:pointer; background:none; border:none; padding:4px; outline:none; border-radius:4px;";

            delBtn.addEventListener("click", () => {
              fetch(`/api/delete_comment`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ card: cardFileName, user: user }),
              })
                .then((res) => res.json())
                .then((resp) => {
                  if (resp.status === "success") {
                    div.remove();
                    showQuickWarning("Deletado.", "success");
                  } else {
                    showQuickWarning(resp.message, "error");
                  }
                })
                .catch((err) => console.error(err));
            });

            div.appendChild(delBtn);
          }

          commentsContainer.appendChild(div);
        }
      })
      .catch((err) => console.error("Erro ao carregar comentários:", err));
  }

  if (commentBtn) {
    commentBtn.addEventListener("click", () => {
      if (!LOGGED_USER.username) return showQuickWarning("Faça login.", "error");

      const commentText = commentInput.value.trim();
      if (!commentText) return showQuickWarning("Digite algo.", "error");
      if (!isCommentClean(commentText)) return showQuickWarning("Palavras proibidas.", "error");

      const cardFileName = popupImage.src.split("/").pop();

      fetch(`/api/comments/${cardFileName}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ comment: commentText }),
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.status === "success") {
            commentInput.value = "";
            loadComments(cardFileName);
            showQuickWarning("Enviado!", "success");
          } else {
            showQuickWarning(data.message, "error");
          }
        })
        .catch((err) => {
          console.error(err);
          showQuickWarning("Erro ao enviar.", "error");
        });
    });
  }

  const loginLink = document.getElementById("login-link");
  if (loginLink) {
    loginLink.addEventListener("click", () => {
      if (popupOverlay.classList.contains("show")) popupOverlay.classList.remove("show");
      hideAllOverlays();
      authOverlay.classList.add("show");
      loginPopup.style.display = "flex";
      registerPopup.style.display = "none";
    });
  }

  updateCommentInterface();

  // ==================== LIKES ====================

  const btnLike = document.getElementById("btn-like");
  const likeCount = document.getElementById("like-count");

  btnLike.addEventListener("click", () => {
    if (!LOGGED_USER.username) {
      showQuickWarning("Faça login.", "error");
      return;
    }

    fetch(`/like/${currentCardFile}`, { method: "POST" })
      .then((res) => res.json())
      .then((data) => {
        if (data.status === "success") {
          likeCount.textContent = data.likes;
          data.action === "liked" ? btnLike.classList.add("liked") : btnLike.classList.remove("liked");
          userLiked = data.action === "liked";
        } else {
          showQuickWarning(data.message, "error");
        }
      })
      .catch((err) => console.error("Erro likes:", err));
  });

  // ==================== PARCEIROS ====================

  const partnerOverlay = document.getElementById("partner-popup-overlay");

  document.querySelectorAll(".parceiro").forEach(parceiro => {
    parceiro.addEventListener("click", () => {
      const { file, nome, descricao, site, instagram, twitter } = parceiro.dataset;

      document.getElementById("partner-logo").src = `/static/images/parceiros/logo/${file}.png`;
      document.getElementById("partner-nome").textContent = nome;
      document.getElementById("partner-descricao").textContent = descricao;

      const toggleLink = (id, url) => {
        const el = document.getElementById(id);
        if (url?.trim()) {
          el.href = url;
          el.style.display = "flex";
        } else {
          el.style.display = "none";
        }
      };

      toggleLink("partner-site", site);
      toggleLink("partner-instagram", instagram);
      toggleLink("partner-twitter", twitter);

      partnerOverlay.style.display = "flex";
      setTimeout(() => partnerOverlay.classList.add("show"), 10);
    });
  });

  document.getElementById("partner-popup-close").addEventListener("click", () => {
    partnerOverlay.classList.remove("show");
    setTimeout(() => partnerOverlay.style.display = "none", 300);
  });

  partnerOverlay.addEventListener("click", (e) => {
    if (e.target === partnerOverlay) {
      partnerOverlay.classList.remove("show");
      setTimeout(() => partnerOverlay.style.display = "none", 300);
    }
  });

  // ==================== FAQ ====================

  const faqBtn = document.getElementById("faq-btn");
  const faqPopup = document.getElementById("faq-popup");
  const closeFaq = document.getElementById("close-faq");

  function openFaq() {
    faqPopup.style.display = "block";
    blockScroll();
  }

  function closeFaqPopup() {
    faqPopup.style.display = "none";
    unblockScroll();
  }

  faqBtn.addEventListener("click", (e) => {
    e.preventDefault();
    openFaq();
  });

  closeFaq.addEventListener("click", () => {
    closeFaqPopup();
  });

  window.addEventListener("click", (e) => {
    if (e.target === faqPopup) closeFaqPopup();
  });

  // ==================== SORTING ====================

  const sortSelect = document.getElementById("sort-select");
  const cardsContainer = document.querySelector(".cards-container");
  const sortedCardsOrder = Array.from(cardsContainer.children);

  sortSelect.addEventListener("change", () => {
    const value = sortSelect.value;
    let cards = Array.from(sortedCardsOrder);

    if (value === "az") {
      cards.sort((a, b) => a.dataset.title.localeCompare(b.dataset.title, "pt-BR"));
    } else if (value === "za") {
      cards.sort((a, b) => b.dataset.title.localeCompare(a.dataset.title, "pt-BR"));
    } else if (value === "recent") {
      cards.reverse();
    } else if (value === "default") {
      cards = [...sortedCardsOrder];
    }

    cardsContainer.innerHTML = "";
    cards.forEach((card) => cardsContainer.appendChild(card));
  });

  // ==================== NOTÍCIAS ====================

  const newsBtn = document.getElementById("news-btn");
  const newsOverlay = document.getElementById("news-popup-overlay");
  const newsClose = document.getElementById("news-popup-close");
  const newsList = document.getElementById("news-list");

  const NEWS_STORAGE_KEY = "apzm_news_last_open";
  const NEWS_COOLDOWN_MS = 1000 * 60 * 60 * 24 * 14;

  function parseDateSafe(s) {
    const t = Date.parse(s);
    return Number.isFinite(t) ? t : 0;
  }

  function sortNewsNewestFirst(items) {
    return (items || []).slice().sort((a, b) => {
      const ta = parseDateSafe(a.created_at);
      const tb = parseDateSafe(b.created_at);
      return tb - ta;
    });
  }

  function openNewsPopup() {
    if (!newsOverlay) return;
    newsOverlay.classList.add("show");
    updateScrollLock();
    localStorage.setItem(NEWS_STORAGE_KEY, String(Date.now()));
  }

  function closeNewsPopup() {
    if (!newsOverlay) return;
    newsOverlay.classList.remove("show");
    updateScrollLock();
  }

  function renderNews(items) {
    if (!newsList) return;

    if (!items || items.length === 0) {
      newsList.innerHTML = `<div class="news-item"><p>Nenhuma notícia no momento.</p></div>`;
      return;
    }

    const html = items.map((n) => {
      const title = escapeHtml(n.title || "");
      const subtitle = escapeHtml(n.subtitle || "");
      const text = escapeHtml(n.text || "");
      const img = (n.image || "").trim();
      const imgHtml = img ? `<img src="/static/images/news/${encodeURIComponent(img)}" alt="${title}">` : "";

    let buttonHtml = "";
    if (n.button && typeof n.button === "object") {
      const bText = escapeHtml(n.button.text || "Abrir");
      const bType = (n.button.type || "url").trim();
      const bTarget = (n.button.target || n.button.url || "").trim();

      if (bTarget) {
        buttonHtml = `
          <button
            class="news-btn-link"
            type="button"
            data-action="${escapeHtml(bType)}"
            data-target="${escapeHtml(bTarget)}"
          >${bText}</button>
        `;
      }
    }

      return `
        <div class="news-item">
          <h3>${title}</h3>
          ${subtitle ? `<h4>${subtitle}</h4>` : ""}
          ${imgHtml}
          ${text ? `<p>${text}</p>` : ""}
          ${buttonHtml}
        </div>
      `;
    }).join("");

    function openPartnerByFile(partnerFile) {
      const el = document.querySelector(`.parceiro[data-file="${CSS.escape(partnerFile)}"]`);
      if (!el) {
        showQuickWarning("Parceiro não encontrado.", "error");
        return;
      }
      el.click(); // reaproveita seu listener atual
    }

    function openCardByFile(cardFile) {
      // tenta achar o card pelo arquivo (se você guardar o file em dataset, melhor ainda)
      const cardEl = Array.from(document.querySelectorAll(".card")).find((c) => {
        const img = c.querySelector("img");
        const file = (img?.src || "").split("/").pop();
        return file === cardFile;
      });

      if (!cardEl) {
        showQuickWarning("Mapa/História não encontrado.", "error");
        return;
      }

      // reaproveita o fluxo atual
      cardEl.click();
    }

    function handleNewsAction(type, target) {
      const t = String(type || "").toLowerCase();
      const trg = String(target || "").trim();
      if (!trg) return;

      if (t === "url") {
        if (!isValidHttpUrl(trg)) return showQuickWarning("Link inválido.", "error");
        window.open(trg, "_blank", "noopener,noreferrer");
        return;
      }

      if (t === "partner") {
        closeNewsPopup();          // opcional: fecha notícias antes
        openPartnerByFile(trg);
        return;
      }

      if (t === "card") {
        closeNewsPopup();          // opcional
        openCardByFile(trg);
        return;
      }

      if (t === "news") {
        openNewsPopup();
        return;
      }

      showQuickWarning("Ação do botão desconhecida.", "error");
    }

    if (newsList) {
      newsList.addEventListener("click", (e) => {
        const btn = e.target.closest(".news-btn-link[data-action][data-target]");
        if (!btn) return;

        const action = btn.getAttribute("data-action");
        const target = btn.getAttribute("data-target");
        handleNewsAction(action, target);
      });
    }

    newsList.innerHTML = html;
  }

  async function loadNewsAndMaybeOpen() {
    try {
      const res = await fetch("/api/news.json", { cache: "no-store" });
      const data = await res.json();
      const sorted = sortNewsNewestFirst(Array.isArray(data) ? data : []);
      renderNews(sorted);

      // abrir automaticamente na 1ª visita ou depois de um tempo
      const lastOpen = Number(localStorage.getItem(NEWS_STORAGE_KEY) || "0");
      const now = Date.now();

      const shouldAutoOpen = !lastOpen || (now - lastOpen) > NEWS_COOLDOWN_MS;

      if (shouldAutoOpen) {
        openNewsPopup();
      }
    } catch (err) {
      console.error("Erro ao carregar notícias:", err);
      // fallback visual
      renderNews([]);
    }
  }

  if (newsBtn) {
    newsBtn.addEventListener("click", () => {
      // sempre recarrega ao abrir (garante notícia nova sem F5)
      loadNewsAndMaybeOpen().then(() => openNewsPopup());
    });
  }

  if (newsClose) newsClose.addEventListener("click", closeNewsPopup);

  if (newsOverlay) {
    newsOverlay.addEventListener("click", (e) => {
      if (e.target === newsOverlay) closeNewsPopup();
    });
  }

  const sidebarNewsBtn = document.getElementById("btn-news");

  if (sidebarNewsBtn) {
    sidebarNewsBtn.addEventListener("click", () => {
      // fecha o menu lateral (se já existir essa função)
      if (typeof closeSidebar === "function") {
        closeSidebar();
      } else {
        // fallback: remove a classe manualmente
        const sidebar = document.getElementById("sidebar");
        if (sidebar) sidebar.classList.remove("open");
        updateScrollLock();
      }

      // abre o popup de notícias
      openNewsPopup();
    });
  }

  // Carrega ao entrar no site (para abrir automaticamente quando necessário)
  loadNewsAndMaybeOpen();
});
