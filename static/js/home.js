document.addEventListener("DOMContentLoaded", () => {
  // 🔹 Armazena dados do usuário logado globalmente
  let LOGGED_USER = {
    username: null,
    email: null,
    password_masked: null,
    is_admin: false,
  };

  function hideAllOverlays() {
      const overlays = document.querySelectorAll(".overlay"); // todas as divs de overlay
      overlays.forEach(ov => ov.classList.remove("show"));
  }

  function updateCommentInterface() {
    if (IS_LOGGED_IN && LOGGED_USER.username) {
      commentInput.disabled = false;
      commentBtn.disabled = false;
      commentInput.placeholder = "Escreva seu comentário...";
    } else {
      commentInput.disabled = true;
      commentBtn.disabled = true;
      commentInput.placeholder = "Faça login para comentar";
    }
  }

  // Carregar contagem ao abrir popup
  function loadLikes(cardFileName) {
    currentCardFile = cardFileName;
    fetch(`/get_likes/${cardFileName}`)
      .then(res => res.json())
      .then(data => {
        likeCount.textContent = data.likes;

        // ✅ Atualiza botão de like baseado no que o usuário já fez
        userLiked = data.user_liked;
        if (userLiked) {
          btnLike.classList.add("liked");
        } else {
          btnLike.classList.remove("liked");
        }
      })
      .catch(err => console.error("Erro ao carregar likes:", err));
  }
  
  // Atualiza quando o login é bem-sucedido
  function onLoginSuccess(data) {
    const username = data.message.split(", ")[1].replace("!", "");
    LOGGED_USER.username = username;
    LOGGED_USER.email = data.email || "";
    LOGGED_USER.password_masked = data.password_masked || "";
    LOGGED_USER.is_admin = data.is_admin === true || data.is_admin === "true";

    // Atualiza campos do popup "Sua Conta" imediatamente
    updateAccountPopupFields(
      LOGGED_USER.username,
      LOGGED_USER.email,
      LOGGED_USER.password_masked
    );
  }

  function updateLoggedUser(username, email = "", password_masked = "") {
    LOGGED_USER.username = username;
    LOGGED_USER.email = email;
    LOGGED_USER.password_masked = password_masked;
  }

  const loginPopup = document.getElementById("login-popup");
  const registerPopup = document.getElementById("register-popup");

  // ================= SLIDES =================
  const slideshowContainer = document.getElementById("background-slideshow");

  // Cria as divs dinamicamente
  slideImages.forEach((src) => {
    const div = document.createElement("div");
    div.classList.add("bg-slide");
    div.style.backgroundImage = `url(${src})`;
    div.style.opacity = "0"; // inicial invisível
    slideshowContainer.appendChild(div);
  });

  const slides = document.querySelectorAll(".bg-slide");
  let current = 0;

  // Mostra slide específico
  function showSlide(index) {
    slides.forEach((slide, i) => {
      slide.style.opacity = i === index ? "1" : "0";
    });
  }

  // Gera índice aleatório, diferente do atual
  function getNextIndex() {
    let next;
    do {
      next = Math.floor(Math.random() * slides.length);
    } while (next === current);
    return next;
  }

  function nextSlide() {
    current = getNextIndex();
    showSlide(current);
  }

  // Inicializa
  showSlide(current);
  setInterval(nextSlide, 5000);

  // ================= POPUP =================
  const popupOverlay = document.getElementById("popup-overlay");
  const popupImage = document.getElementById("popup-image");
  const popupTitle = document.getElementById("popup-title"); // agora será uma img
  const popupDescription = document.getElementById("popup-description");
  const popupClose = document.getElementById("popup-close");

  // Seleciona todos os cards
  const cards = document.querySelectorAll(".card");

  // Oculta cards invisíveis (com base no atributo salvo no JSON)
  cards.forEach((card) => {
    const isVisible = card.dataset.visible === "true";
    if (!isVisible) {
      card.style.display = "none";
    }
  });

  // Função auxiliar para verificar se imagem existe
  function imageExists(url) {
    const xhr = new XMLHttpRequest();
    xhr.open("HEAD", url, false);
    xhr.send();
    return xhr.status === 200;
  }

  // Função que tenta buscar automaticamente a imagem de título
  function getTitleImage(baseName) {
    const exts = ["png", "jpg", "jpeg", "webp"];
    for (let ext of exts) {
      let path = `/static/images/titles/${baseName}.${ext}`;
      if (imageExists(path)) return path;
    }
    return null; // se não existir, retorna null
  }

  // Função para abrir popup
  function openPopup(cardImgSrc, titleImgSrc, description, cardFileName) {
    popupImage.src = cardImgSrc;
    popupImage.classList.add("card-image");

    if (titleImgSrc) {
      popupTitle.innerHTML = `<img src="${titleImgSrc}" alt="Título do Card" style="width:100%; height:auto;">`;
    } else {
      popupTitle.innerHTML = "";
    }

    popupDescription.textContent =
      description || "Aqui vai o resumo ou sinopse do mapa/história.";
    popupOverlay.classList.add("show");
    updateScrollLock();

    updateCommentInterface();

    loadComments(cardFileName);
  }

  // Evento de clique em cada card
  cards.forEach((card) => {
    card.addEventListener("click", () => {
      const img = card.querySelector("img");
      const cardImgSrc = img ? img.src : "";

      const baseName = cardImgSrc.split("/").pop().split(".")[0];
      let titleImgSrc = getTitleImage(baseName);
      if (!titleImgSrc) titleImgSrc = card.dataset.title;
      
      const description = card.dataset.description;

      const cardFileName = cardImgSrc.split("/").pop(); // ✅ adiciona isso
      openPopup(cardImgSrc, titleImgSrc, description, cardFileName); // ✅ passa para a função
    });
  });

  // Fecha popup ao clicar no "X"
  popupClose.addEventListener("click", () => {
    popupOverlay.classList.remove("show");
  });

  // Fecha popup ao clicar fora da caixa do popup
  popupOverlay.addEventListener("click", (e) => {
    if (e.target === popupOverlay) {
      popupOverlay.classList.remove("show");
    }
  });

  // ================= LINKS DOS CARDS =================
  let cardLinks = {};

  // Seleciona botões do popup
  const btnDownloadMap = document.getElementById("btn-download-map");
  const btnReadStory = document.getElementById("btn-read-story");

  // Função para atualizar links quando abrir popup
  function setPopupLinks(cardTitle) {
    const links = cardLinks[cardTitle];

    // Baixar mapa
    if (links && links.mapa) {
      btnDownloadMap.onclick = () => window.open(links.mapa, "_blank");
      btnDownloadMap.classList.remove("disabled");
    } else {
      btnDownloadMap.onclick = null;
      btnDownloadMap.classList.add("disabled");
    }

    // Ler história
    if (links && links.historia) {
      btnReadStory.onclick = () => window.open(links.historia, "_blank");
      btnReadStory.classList.remove("disabled");
    } else {
      btnReadStory.onclick = null;
      btnReadStory.classList.add("disabled");
    }
  }

  // Carrega JSON com fetch
  fetch("/api/links.json")
    .then((res) => res.json())
    .then((data) => {
      cardLinks = data;

      // Só depois de carregar links, adiciona clique nos cards
      cards.forEach((card) => {
        card.addEventListener("click", () => {
          const img = card.querySelector("img");
          const cardImgSrc = img ? img.src : "";

          // 🔹 Pega o nome do arquivo do card
          const cardFileName = cardImgSrc.split("/").pop(); // ex: bacabeiras.jpg

          let titleImgSrc = getTitleImage(cardFileName.split(".")[0]);
          if (!titleImgSrc) titleImgSrc = card.dataset.title;

          const description = card.dataset.description;

          openPopup(cardImgSrc, titleImgSrc, description);

          // Atualiza links usando o nome do arquivo completo
          setPopupLinks(cardFileName);
          loadLikes(cardFileName);
        });
      });
    })
    .catch((err) => console.error("Erro ao carregar links:", err));

  // ================= AUTH POPUPS =================
  const authOverlay = document.getElementById("auth-popup-overlay");
  const authClose = document.getElementById("auth-popup-close");

  const loginBtn = document.querySelector(".btn-login");
  const registerBtn = document.querySelector(".btn-register");

  if (loginBtn) {
    loginBtn.addEventListener("click", () => {
      loginPopup.style.display = "flex";
      registerPopup.style.display = "none";
      authOverlay.classList.add("show");
    });
  }

  if (registerBtn) {
    registerBtn.addEventListener("click", () => {
      registerPopup.style.display = "flex";
      loginPopup.style.display = "none";
      authOverlay.classList.add("show");
    });
  }

  const switchToRegister = document.getElementById("switch-to-register");
  const switchToLogin = document.getElementById("switch-to-login");

  // Alternar entre login e cadastro
  switchToRegister.addEventListener("click", () => {
    loginPopup.style.display = "none";
    registerPopup.style.display = "flex";
  });

  switchToLogin.addEventListener("click", () => {
    loginPopup.style.display = "flex";
    registerPopup.style.display = "none";
  });

  // Fechar popup
  authClose.addEventListener("click", () => {
    authOverlay.classList.remove("show");
  });

  // Fechar clicando fora
  authOverlay.addEventListener("click", (e) => {
    if (e.target === authOverlay) {
      authOverlay.classList.remove("show");
    }
  });

  // ================= VALIDACAO DE USUARIO =================
  const usernameInput = document.getElementById("username");
  const usernameTooltip = document.getElementById("username-tooltip");

  const ruleUsernameLength = document.getElementById("rule-username-length");
  const ruleUsernameSpecial = document.getElementById("rule-username-special");
  const ruleUsernameFirstUpper = document.getElementById(
    "rule-username-first-upper"
  );
  const ruleUsernameNoNumberStart = document.getElementById(
    "rule-username-no-number-start"
  );
  const ruleUsernameBadwords = document.getElementById(
    "rule-username-badwords"
  );

  // Lista simples de palavras proibidas
  const badwords = [
    "burro",
    "idiota",
    "otario",
    "palhaco",
    "lixo",
    "puta",
    "caralho",
    "porra",
    "merda",
    "bosta",
    "cu",
  ];

  // Função de validação

  function validateUsername(value) {
    const trimmed = value.trim();

    trimmed.length >= 5 && trimmed.length <= 20
      ? ruleUsernameLength.classList.add("valid")
      : ruleUsernameLength.classList.remove("valid");

    /^[A-Za-z0-9_]*$/.test(trimmed)
      ? ruleUsernameSpecial.classList.add("valid")
      : ruleUsernameSpecial.classList.remove("valid");

    /^[A-Z]/.test(trimmed)
      ? ruleUsernameFirstUpper.classList.add("valid")
      : ruleUsernameFirstUpper.classList.remove("valid");

    !/^[0-9]/.test(trimmed)
      ? ruleUsernameNoNumberStart.classList.add("valid")
      : ruleUsernameNoNumberStart.classList.remove("valid");

    const hasBadword = badwords.some((bad) =>
      trimmed.toLowerCase().includes(bad)
    );
    !hasBadword
      ? ruleUsernameBadwords.classList.add("valid")
      : ruleUsernameBadwords.classList.remove("valid");
  }

  // Mostrar tooltip ao focar
  usernameInput.addEventListener("focus", () => {
    usernameTooltip.classList.add("show");
  });

  // Esconder tooltip ao sair do foco
  usernameInput.addEventListener("blur", () => {
    usernameTooltip.classList.remove("show");
  });

  // Validar em tempo real
  usernameInput.addEventListener("input", (e) => {
    validateUsername(e.target.value);
  });

  // ================= VALIDACAO DE EMAIL =================
  const emailInput = document.getElementById("email");
  const emailTooltip = document.getElementById("email-tooltip");
  const ruleEmailFormat = document.getElementById("rule-email-format");

  // Regex básica para email válido
  function validateEmail(value) {
    if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim())) {
      ruleEmailFormat.classList.add("valid");
    } else {
      ruleEmailFormat.classList.remove("valid");
    }
  }

  // Mostrar tooltip ao focar
  emailInput.addEventListener("focus", () => {
    emailTooltip.classList.add("show");
  });

  // Esconder tooltip ao sair do foco
  emailInput.addEventListener("blur", () => {
    emailTooltip.classList.remove("show");
  });

  // Validar em tempo real
  emailInput.addEventListener("input", (e) => {
    validateEmail(e.target.value);
    emailTooltip.classList.add("show");
  });

  // ================= VALIDACAO DE SENHA =================
  const passwordInput = document.getElementById("password");
  const passwordTooltip = document.getElementById("password-tooltip");

  const rulePasswordLength = document.getElementById("rule-password-length");
  const rulePasswordUpper = document.getElementById("rule-password-upper");
  const rulePasswordLower = document.getElementById("rule-password-lower");
  const rulePasswordNumber = document.getElementById("rule-password-number");
  const rulePasswordSpecial = document.getElementById("rule-password-special");

  // Função de validação
  function validatePassword(value) {
    const trimmed = value.trim();

    // Regra 1: mínimo 8 caracteres
    if (trimmed.length >= 8) {
      rulePasswordLength.classList.add("valid");
    } else {
      rulePasswordLength.classList.remove("valid");
    }

    // Regra 2: pelo menos uma letra maiúscula
    if (/[A-Z]/.test(trimmed)) {
      rulePasswordUpper.classList.add("valid");
    } else {
      rulePasswordUpper.classList.remove("valid");
    }

    // Regra 3: pelo menos uma letra minúscula
    if (/[a-z]/.test(trimmed)) {
      rulePasswordLower.classList.add("valid");
    } else {
      rulePasswordLower.classList.remove("valid");
    }

    // Regra 4: pelo menos um número
    if (/[0-9]/.test(trimmed)) {
      rulePasswordNumber.classList.add("valid");
    } else {
      rulePasswordNumber.classList.remove("valid");
    }

    // Regra 5: pelo menos um caractere especial
    if (/[!@#$%^&*]/.test(trimmed)) {
      rulePasswordSpecial.classList.add("valid");
    } else {
      rulePasswordSpecial.classList.remove("valid");
    }
  }

  // Mostrar tooltip ao focar
  passwordInput.addEventListener("focus", () => {
    passwordTooltip.classList.add("show");
  });

  // Esconder tooltip ao sair do foco
  passwordInput.addEventListener("blur", () => {
    passwordTooltip.classList.remove("show");
  });

  // Validar em tempo real
  passwordInput.addEventListener("input", (e) => {
    validatePassword(e.target.value);
  });

  const registerBtnSubmit = document.querySelector("#register-popup .auth-btn");
  const checkbox = document.querySelector(
    "#register-popup .auth-checkbox input"
  );

  registerBtnSubmit.addEventListener("click", (e) => {
    e.preventDefault(); // evita envio padrão

    const usernameVal = usernameInput.value.trim();
    const emailVal = emailInput.value.trim();
    const passwordVal = passwordInput.value.trim();
    const allFilled =
      usernameVal && emailVal && passwordVal && checkbox.checked;

    const usernameValid =
      ruleUsernameLength.classList.contains("valid") &&
      ruleUsernameSpecial.classList.contains("valid") &&
      ruleUsernameFirstUpper.classList.contains("valid") &&
      ruleUsernameNoNumberStart.classList.contains("valid") &&
      ruleUsernameBadwords.classList.contains("valid");

    const emailValid = ruleEmailFormat.classList.contains("valid");

    const passwordValid =
      rulePasswordLength.classList.contains("valid") &&
      rulePasswordUpper.classList.contains("valid") &&
      rulePasswordLower.classList.contains("valid") &&
      rulePasswordNumber.classList.contains("valid") &&
      rulePasswordSpecial.classList.contains("valid");

    const checkboxValid = checkbox.checked;

    if (
      !allFilled ||
      !usernameValid ||
      !emailValid ||
      !passwordValid ||
      !checkboxValid
    ) {
      showQuickWarning(
        "Preencha todos os campos corretamente e marque a checkbox.",
        "error"
      );
      return;
    }

    const payload = {
      username: usernameVal,
      email: emailVal,
      password: passwordVal,
    };

    fetch("/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.status === "success") {
          IS_LOGGED_IN = true;
          // Mostra aviso de sucesso ANTES de fechar popup
          showQuickWarning(data.message, "success");

          // Limpa campos
          usernameInput.value = "";
          emailInput.value = "";
          passwordInput.value = "";
          checkbox.checked = false;

          // Fecha popup de registro com delay curto pra usuário ver o aviso
          setTimeout(() => authOverlay.classList.remove("show"), 1000);

          // 🔹 Atualiza variáveis globais
          IS_LOGGED_IN = true;
          LOGGED_USER.username = usernameVal;
          LOGGED_USER.email = emailVal;
          LOGGED_USER.password_masked = passwordVal.replace(/./g, "*"); // opcional, mantém mascarada
          LOGGED_USER.is_admin = data.is_admin || false;

          // Atualiza interface para mostrar que usuário está logado
          document.querySelector(".auth-buttons").innerHTML = `
          <span class="welcome-message">Olá, ${usernameVal}!</span>
          <button class="btn-logout" onclick="location.href='/logout'">Sair</button>
          `;
          setTimeout(() => location.reload(), 100);
          updateCommentInterface();
        } else {
          showQuickWarning(data.message, "error");
        }
      })
      .catch((err) => {
        console.error(err);
        showQuickWarning("Erro ao registrar usuário.", "error");
      });
  });

  // ================= AVISO RÁPIDO =================
  function showQuickWarning(message, type = "error") {
    const warning = document.getElementById("quick-warning");
    warning.textContent = message;

    // Ajusta cor conforme tipo
    warning.style.background = type === "success" ? "#4CAF50" : "#ff5555";

    // Inicializa posição acima da tela e opacidade 0
    warning.style.display = "block";
    warning.style.opacity = "0";
    warning.style.transform = "translate(-50%, -50px)"; // sobe 50px acima

    // Aplica transição de slide + fade
    setTimeout(() => {
      warning.style.opacity = "1";
      warning.style.transform = "translate(-50%, 0)"; // desce para posição
    }, 10);

    // Fade-out e slide-up após 2,5s
    setTimeout(() => {
      warning.style.opacity = "0";
      warning.style.transform = "translate(-50%, -50px)";
      setTimeout(() => {
        warning.style.display = "none";
      }, 500); // remove do DOM após fade-out
    }, 2500);
  }

  // ================ LOGIN =====================
  function updateAccountPopupFields(username, email, password_masked) {
    const inputUsername = document.getElementById("account-username-popup");
    const inputEmail = document.getElementById("account-email-popup");
    const inputPassword = document.getElementById("account-password");

    inputUsername.value = username;
    inputUsername.dataset.username = username;

    if (email) {
      inputEmail.value = email;
      inputEmail.dataset.email = email;
    }

    if (password_masked) {
      inputPassword.value = password_masked;
      inputPassword.dataset.password = password_masked;
    }
  }

  // ➡️ Aqui, adicione a chamada fetch
  fetch("/api/current_user")
    .then((res) => res.json())
    .then((data) => {
      if (data.logged_in) {
        LOGGED_USER.username = data.username;
        LOGGED_USER.email = data.email || "";
        LOGGED_USER.password_masked = data.password_masked || "";
        LOGGED_USER.is_admin = data.is_admin === true || data.is_admin === "true"; // ✅

        updateAccountPopupFields(
          LOGGED_USER.username,
          LOGGED_USER.email,
          LOGGED_USER.password_masked
        );
      }
    })
    .catch((err) => console.error("Erro ao carregar usuário atual:", err));

  const loginPopupBtn = document.querySelector("#login-popup .auth-btn");
  const loginEmailInput = document.querySelector(
    "#login-popup input[type='email']"
  );
  const loginPasswordInput = document.querySelector(
    "#login-popup input[type='password']"
  );

  loginPopupBtn.addEventListener("click", (e) => {
    e.preventDefault();
    const emailVal = loginEmailInput.value.trim();
    const passwordVal = loginPasswordInput.value.trim();
    if (!emailVal || !passwordVal) {
      showQuickWarning("Preencha email e senha corretamente.", "error");
      return;
    }

    fetch("/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: emailVal, password: passwordVal }),
    })
      .then((res) => res.json())
      .then((data) => {
        showQuickWarning(
          data.message,
          data.status === "success" ? "success" : "error"
        );
        if (data.status === "success") {
          authOverlay.classList.remove("show");
          IS_LOGGED_IN = true;

          let buttonsHTML = `<span class="welcome-message">Olá, ${data.message
            .split(", ")[1]
            .replace("!", "")}!</span>
                  <button class="btn-logout" onclick="location.href='/logout'">Sair</button>`;
          if (data.is_admin)
            buttonsHTML += `<button class="btn-admin" onclick="location.href='/admin'">Admin</button>`;
          document.querySelector(".auth-buttons").innerHTML = buttonsHTML;

          onLoginSuccess(data); // 🔹 Atualiza global e campos do popup

          setTimeout(() => location.reload(), 100);
          updateCommentInterface();
        }
      })
      .catch((err) => {
        console.error(err);
        showQuickWarning("Erro ao realizar login.", "error");
      });
  });

  // ================= SIDEBAR =================
  const menuBtn = document.getElementById("menu-btn");
  const sidebar = document.getElementById("sidebar");
  const sidebarOverlay = document.getElementById("sidebar-overlay");
  const sidebarClose = document.getElementById("sidebar-close");

  // Funções para abrir e fechar
  function openSidebar() {
    sidebar.classList.add("open");
    sidebarOverlay.classList.add("show");
    menuBtn.textContent = "";
    menuBtn.classList.add("open");
  }

  function closeSidebar() {
    sidebar.classList.remove("open");
    sidebarOverlay.classList.remove("show");
    menuBtn.textContent = "☰";
    menuBtn.classList.remove("open");
  }

  // Event listeners
  menuBtn.addEventListener("click", () => {
    sidebar.classList.contains("open") ? closeSidebar() : openSidebar();
  });

  sidebarClose.addEventListener("click", closeSidebar);
  sidebarOverlay.addEventListener("click", closeSidebar);

  // ======================= SIDEBAR =========================
  // Quem Somos Popup
  const btnWhoUs = document.getElementById('btn-who-us');
  const whoUsOverlay = document.getElementById('who-us-popup-overlay');
  const whoUsClose = document.getElementById('who-us-popup-close');

  if (btnWhoUs && whoUsOverlay && whoUsClose) {
    btnWhoUs.addEventListener('click', () => {
        closeSidebar();
        whoUsOverlay.classList.add('show');
    });

    whoUsClose.addEventListener('click', () => {
        whoUsOverlay.classList.remove('show');
    });

    // Fecha ao clicar fora do popup
    whoUsOverlay.addEventListener('click', (e) => {
        if (e.target === whoUsOverlay) {
            whoUsOverlay.classList.remove('show');
        }
    });
  }
  // ================= SUA CONTA =================
  const accountBtn = document.getElementById("btn-user-account");
  const accountOverlay = document.getElementById("account-popup-overlay");
  const accountPopupClose = document.getElementById("account-popup-close");
  const inputUsername = document.getElementById("account-username");
  const inputEmail = document.getElementById("account-email");
  const inputPassword = document.getElementById("account-password");
  const passwordLabel = document.querySelector('label[for="account-password"]');

  // Abre popup de conta
  accountBtn.addEventListener("click", () => {
    if (!IS_LOGGED_IN) {
      closeSidebar();
      authOverlay.classList.add("show");
      loginPopup.style.display = "flex";
      registerPopup.style.display = "none";
      showQuickWarning("Você precisa fazer login primeiro.", "error");
      return;
    }
    closeSidebar();
    accountOverlay.classList.add("show");

    // Atualiza inputs com dados do login atual
    updateAccountPopupFields(
      LOGGED_USER.username,
      LOGGED_USER.email,
      LOGGED_USER.password_masked
    );
  });

  // Fecha popup ao clicar no X
  accountPopupClose.addEventListener("click", () => {
    accountOverlay.classList.remove("show");
  });

  // Fecha clicando fora do popup
  accountOverlay.addEventListener("click", (e) => {
    if (e.target === accountOverlay) {
      accountOverlay.classList.remove("show");
    }
  });

  /*// ======================= EDITAR CONTA =========================
  const btnEditAccount = document.getElementById("btn-edit-account");
  const btnSaveAccount = document.getElementById("btn-save-account");
  const btnCancelEdit = document.getElementById("btn-cancel-edit");
  const btnDeleteAccount = document.getElementById("btn-delete-account"); // 🔹 novo

  // ================= SUA CONTA / TOOLTIP =================
  const accountUsernameTooltip = document.getElementById(
    "account-username-tooltip"
  );
  const accountEmailTooltip = document.getElementById("account-email-tooltip");

  // Mostrar tooltip ao focar
  inputUsername.addEventListener("focus", () => {
    if (!inputUsername.hasAttribute("readonly")) {
      accountUsernameTooltip.classList.add("show");
    }
  });
  inputUsername.addEventListener("blur", () =>
    accountUsernameTooltip.classList.remove("show")
  );

  inputEmail.addEventListener("focus", () => {
    if (!inputEmail.hasAttribute("readonly")) {
      accountEmailTooltip.classList.add("show");
    }
  });
  inputEmail.addEventListener("blur", () =>
    accountEmailTooltip.classList.remove("show")
  );

  // Entrar em modo edição
  btnEditAccount.addEventListener("click", () => {
    inputUsername.removeAttribute("readonly");
    inputEmail.removeAttribute("readonly");

    // Limpa senha e troca o label
    inputPassword.value = "";
    inputPassword.removeAttribute("readonly");
    inputPassword.placeholder = "Digite sua senha atual";
    passwordLabel.textContent = "Senha Atual";

    btnEditAccount.style.display = "none";
    btnSaveAccount.style.display = "inline-block";
    btnCancelEdit.style.display = "inline-block";

    // 🔹 Oculta botão deletar
    if (btnDeleteAccount) btnDeleteAccount.style.display = "none";

    // 🔹 Validação em tempo real
    inputUsername.addEventListener("input", (e) =>
      validateUsername(e.target.value)
    );
    inputEmail.addEventListener("input", (e) => validateEmail(e.target.value));
    inputPassword.addEventListener("input", (e) =>
      validatePassword(e.target.value)
    );
  });

  // Cancelar edição
  btnCancelEdit.addEventListener("click", () => {
    inputUsername.value = inputUsername.dataset.username;
    inputEmail.value = inputEmail.dataset.email;
    inputPassword.type = "password";
    inputPassword.value = inputPassword.dataset.password;
    inputPassword.setAttribute("readonly", true);
    passwordLabel.textContent = "Senha";

    inputUsername.setAttribute("readonly", true);
    inputEmail.setAttribute("readonly", true);

    // 🔹 Volta visibilidade corretamente
    btnEditAccount.style.display = "inline-block";
    btnSaveAccount.style.display = "none";
    btnCancelEdit.style.display = "none";
    if (btnDeleteAccount) btnDeleteAccount.style.display = "inline-block";
  });

  // Salvar edição
  btnSaveAccount.addEventListener("click", () => {
    if (btnDeleteAccount) btnDeleteAccount.style.display = "inline-block";
    const usernameVal = inputUsername.value.trim();
    const emailVal = inputEmail.value.trim();
    const currentPassword = inputPassword.value.trim();

    if (!usernameVal || !emailVal || !currentPassword) {
      showQuickWarning("Preencha todos os campos.", "error");
      return;
    }

    validateUsername(usernameVal);
    validateEmail(emailVal);

    const usernameValid =
      document.querySelectorAll("#username-tooltip .valid").length === 5;
    const emailValid = document
      .getElementById("rule-email-format")
      .classList.contains("valid");

    if (!usernameValid || !emailValid) {
      showQuickWarning("Usuário ou Email inválidos.", "error");
      return;
    }

    fetch("/update_user", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: usernameVal,
        email: emailVal,
        password: currentPassword,
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        // ✅ Retorno visual
        showQuickWarning(
          data.message,
          data.status === "success" ? "success" : "error"
        );

        if (data.status === "success") {
          // Atualiza valores originais para evitar undefined
          inputUsername.dataset.username = usernameVal;
          inputEmail.dataset.email = emailVal;
          inputPassword.dataset.password = ""; // senha não é exibida

          btnCancelEdit.click();
          document.querySelector(
            ".welcome-message"
          ).textContent = `Olá, ${usernameVal}!`;
        }
      })
      .catch((err) => {
        console.error(err);
        showQuickWarning("Erro ao atualizar conta.", "error");
      });
  });*/
  // ================= DELETE ACCOUNT =================
  const deleteAccountBtn = document.getElementById("btn-delete-account");
  const deleteAccountOverlay = document.getElementById("delete-account-popup-overlay");
  const confirmDeleteBtn = document.getElementById("confirm-delete-account");
  const cancelDeleteBtn = document.getElementById("cancel-delete-account");

  if (deleteAccountBtn) {
    deleteAccountBtn.addEventListener("click", () => {
      deleteAccountOverlay.classList.add("show"); // mostra overlay
    });
  }

  if (cancelDeleteBtn) {
    cancelDeleteBtn.addEventListener("click", () => {
      deleteAccountOverlay.classList.remove("show"); // fecha overlay
    });
  }

  if (confirmDeleteBtn) {
    confirmDeleteBtn.addEventListener("click", () => {
      fetch("/delete_account", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"   // 🔹 avisa que é JSON
        },
        body: JSON.stringify({ username: LOGGED_USER.username }) // 🔹 manda um body qualquer
      })
        .then(res => {
          if (!res.ok) throw new Error("Falha na requisição");
          return res.json();
        })
        .then(data => {
          if (data.status === "success") {
            showQuickWarning("Conta deletada com sucesso.", "success");
            window.location.href = "/"; // redireciona
          } else {
            showQuickWarning(data.message, "error");
          }
        })
        .catch(err => {
          console.error(err);
          showQuickWarning("Erro ao deletar conta.", "error");
        });
    });
  }
  // também fecha ao clicar fora
  if (deleteAccountOverlay) {
    deleteAccountOverlay.addEventListener("click", (e) => {
      if (e.target === deleteAccountOverlay) {
        deleteAccountOverlay.classList.remove("show");
      }
    });
  }

  // ================= RESET DE SENHA =================
  const forgotLink = document.getElementById("forgot-password-link");
  const forgotOverlay = document.getElementById("forgot-password-overlay");
  const forgotBtn = document.getElementById("forgot-password-btn");
  const forgotEmailInput = document.getElementById("forgot-password-email");
  const forgotLoading = document.getElementById("forgot-password-loading");
  const closeForgot = document.getElementById("close-forgot-password");

  if (forgotLink) {
    forgotLink.addEventListener("click", (e) => {
        e.preventDefault();
        hideAllOverlays(); // fecha outros popups
        authOverlay.classList.add("show"); // garante que o overlay geral esteja visível
        forgotOverlay.classList.add("show"); // abre o popup de reset
        loginPopup.style.display = "none";
        registerPopup.style.display = "none";
    });
  }


  if (closeForgot) {
    closeForgot.addEventListener("click", () => {
        forgotOverlay.classList.remove("show");
        authOverlay.classList.add("show");
        loginPopup.style.display = "flex";
        registerPopup.style.display = "none";
    });
  }

  if (forgotBtn) {
    forgotBtn.addEventListener("click", async () => {
        const emailVal = forgotEmailInput.value.trim();
        if (!emailVal) {
            showQuickWarning("Digite um email válido.", "error");
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
            } else {
                showQuickWarning(data.message || "Erro ao enviar email.", "error");
            }
        } catch (err) {
            console.error(err);
            showQuickWarning("Erro de conexão ao enviar email.", "error");
        } finally {
            forgotLoading.style.display = "none";
            forgotBtn.disabled = false;
        }
    });
  }

  // ===========================
  // Sistema de Comentários
  // ===========================
  const commentsContainer = document.getElementById("comments-container");
  const commentInput = document.getElementById("comment-input");
  const commentBtn = document.getElementById("comment-submit");

  // Função para carregar comentários de um card
  function loadComments(cardFileName) {
    console.log(LOGGED_USER.is_admin)
    if (!cardFileName) return;
    
    fetch(`/api/comments/${cardFileName}`)
      .then(res => res.json())
      .then(data => {
        commentsContainer.innerHTML = "";
        if (!data || Object.keys(data).length === 0) {
          commentsContainer.innerHTML = `<p class="no-comments" style="color:gray; padding-top: 8px;">Nenhum comentário ainda.</p>`;
          return;
        }

        for (const [user, comment] of Object.entries(data)) {
          const div = document.createElement("div");
          div.classList.add("comment");

          // Conteúdo do comentário
          div.innerHTML = `<strong>${user}:</strong> ${comment}`;

          // 🔹 Adiciona botão de deletar apenas se for o usuário logado ou admin
          if (LOGGED_USER.username === user || LOGGED_USER.is_admin) {
            const delBtn = document.createElement("button");
            delBtn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="red" class="bi bi-trash" viewBox="0 0 16 16">
              <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0z"/>
              <path d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4zM2.5 3h11V2h-11z"/>
            </svg>
            `;

            delBtn.style.marginLeft = "10px";
            delBtn.style.cursor = "pointer";
            delBtn.style.background = "none";
            delBtn.style.border = "none";
            delBtn.style.padding = "4px"; // adiciona área clicável
            delBtn.style.outline = "none";
            delBtn.style.borderRadius = "4px"; // cantos arredondados
            delBtn.style.transition = "all 0.2s ease"; // transição suave

            // Hover effect
            delBtn.addEventListener("mouseenter", () => {
                delBtn.style.backgroundColor = "rgba(255, 77, 77, 0.2)";
                delBtn.querySelector("svg").setAttribute("fill", "#ff1a1a");
            });
            delBtn.addEventListener("mouseleave", () => {
                delBtn.style.backgroundColor = "transparent";
                delBtn.querySelector("svg").setAttribute("fill", "#ff4d4d");
            });

            // 🔹 Envia o username correto (dono do comentário) para deletar
            delBtn.addEventListener("click", () => {
              fetch(`/api/delete_comment`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ card: cardFileName, user: user }) // ✅ aqui
              })
                .then(res => res.json())
                .then(resp => {
                  if (resp.status === "success") {
                    div.remove(); // remove do DOM imediatamente
                    showQuickWarning("Comentário deletado.", "success");
                  } else {
                    showQuickWarning(resp.message, "error");
                  }
                })
                .catch(err => console.error(err));
            });

            div.appendChild(delBtn);
          }

          commentsContainer.appendChild(div);
        }
      })
      .catch(err => console.error("Erro ao carregar comentários:", err));
  }

  const badwordsComments = [
    "puta", "caralho", "merda", "porra", "cu", "bosta",
    "idiota", "burro", "otario", "palhaco", "lixo"
  ];

  // Função para validar comentário
  function isCommentClean(comment) {
    const lower = comment.toLowerCase();
    return !badwordsComments.some(word => lower.includes(word));
  }

  // Enviar comentário
  if (commentBtn) {
    commentBtn.addEventListener("click", () => {
      if (!IS_LOGGED_IN) {
        showQuickWarning("Faça login para comentar.", "error");
        return;
      }

      const commentText = commentInput.value.trim();
      if (!commentText) {
        showQuickWarning("Digite um comentário.", "error");
        return;
      }

      // 🔹 Validação de palavras inapropriadas
      if (!isCommentClean(commentText)) {
        showQuickWarning("Comentário contém palavras proibidas.", "error");
        return;
      }

      // 🔹 Pega card atualmente aberto
      const cardFileName = popupImage.src.split("/").pop(); // seu card_id

      fetch(`/api/comments/${cardFileName}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          card: cardFileName, 
          user: LOGGED_USER.username, 
          comment: commentText 
        })
      })
      .then(res => res.json())
      .then(data => {
        if (data.status === "success") {
          commentInput.value = "";
          loadComments(cardFileName); // recarrega comentários
          showQuickWarning("Comentário enviado!", "success");
        } else {
          showQuickWarning(data.message, "error");
        }
      })
      .catch(err => {
        console.error(err);
        showQuickWarning("Erro ao enviar comentário.", "error");
      });
    });
  }

  const loginLink = document.getElementById("login-link");

  if (loginLink) {
    loginLink.addEventListener("click", () => {
      // Fecha popup do card, se estiver aberto
      if (popupOverlay.classList.contains("show")) {
        popupOverlay.classList.remove("show");
      }

      // Fecha outros overlays de comentários, se houver
      hideAllOverlays();

      // Abre o popup de login
      authOverlay.classList.add("show");
      loginPopup.style.display = "flex";
      registerPopup.style.display = "none";
    });
  }

  function blockScroll() {
    document.body.classList.add("no-scroll");
  }

  function unblockScroll() {
    document.body.classList.remove("no-scroll");
  }

  // Função para verificar se há algum overlay visível
  function updateScrollLock() {
    const anyOverlayShown = document.querySelectorAll(".overlay.show, #auth-popup-overlay.show, #who-us-popup-overlay.show, #account-popup-overlay.show, #delete-account-popup-overlay.show, #forgot-password-overlay.show").length > 0;
    if (anyOverlayShown) {
      blockScroll();
    } else {
      unblockScroll();
    }
  }

  // =====================
  // Atualiza interface de comentários
  // =====================

  // Chamada inicial ao carregar a página
  
  updateCommentInterface();

  // ================= LIKES =================
  const btnLike = document.getElementById("btn-like");
  const likeCount = document.getElementById("like-count");
  let currentCardFile = null;
  let userLiked = false;

    // Evento de clique no botão de like
    btnLike.addEventListener("click", () => {
      if (!IS_LOGGED_IN || !LOGGED_USER.username) {
        showQuickWarning("Faça login para dar Like!", "error");
        return;
      }

      fetch(`/like/${currentCardFile}`, { method: "POST" })
        .then(res => res.json())
        .then(data => {
          if (data.status === "success") {
            likeCount.textContent = data.likes;

            if (data.action === "liked") {
              btnLike.classList.add("liked");
              userLiked = true;
            } else {
              btnLike.classList.remove("liked");
              userLiked = false;
            }
          } else {
            showQuickWarning(data.message, "error");
          }
        })
        .catch(err => console.error("Erro ao dar Like:", err));
    });
  });