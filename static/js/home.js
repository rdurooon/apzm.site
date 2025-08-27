document.addEventListener("DOMContentLoaded", () => {
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
  function openPopup(cardImgSrc, titleImgSrc, description) {
    popupImage.src = cardImgSrc;

    if (titleImgSrc) {
      popupTitle.innerHTML = `<img src="${titleImgSrc}" alt="Título do Card" style="width:100%; height:auto;">`;
    } else {
      popupTitle.innerHTML = ""; // evita erro se não houver título
    }

    popupDescription.textContent =
      description || "Aqui vai o resumo ou sinopse do mapa/história.";
    popupOverlay.classList.add("show");
  }

  // Evento de clique em cada card
  cards.forEach((card) => {
    card.addEventListener("click", () => {
      const img = card.querySelector("img");
      const cardImgSrc = img ? img.src : "";

      // 🔹 Nome base do arquivo (sem extensão)
      const baseName = cardImgSrc.split("/").pop().split(".")[0];

      // 🔹 Primeiro tenta pegar título automaticamente
      let titleImgSrc = getTitleImage(baseName);

      // 🔹 Se não achar, usa o data-title (compatibilidade com cards antigos)
      if (!titleImgSrc) {
        titleImgSrc = card.dataset.title;
      }

      const description = card.dataset.description;

      openPopup(cardImgSrc, titleImgSrc, description);
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
    .then(res => res.json())
    .then(data => {
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
        });
      });
    })
    .catch(err => console.error("Erro ao carregar links:", err));


  // ================= AUTH POPUPS =================
  const authOverlay = document.getElementById("auth-popup-overlay");
  const authClose = document.getElementById("auth-popup-close");

  const loginBtn = document.querySelector(".btn-login");
  const registerBtn = document.querySelector(".btn-register");

  const loginPopup = document.getElementById("login-popup");
  const registerPopup = document.getElementById("register-popup");

  const switchToRegister = document.getElementById("switch-to-register");
  const switchToLogin = document.getElementById("switch-to-login");

  // Abrir popups
  loginBtn.addEventListener("click", () => {
    loginPopup.style.display = "flex";
    registerPopup.style.display = "none";
    authOverlay.classList.add("show");
  });

  registerBtn.addEventListener("click", () => {
    registerPopup.style.display = "flex";
    loginPopup.style.display = "none";
    authOverlay.classList.add("show");
  });

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

  const ruleLength = document.getElementById("rule-length");
  const ruleSpecial = document.getElementById("rule-special");
  const ruleFirstUpper = document.getElementById("rule-first-upper");
  const ruleNoNumberStart = document.getElementById("rule-no-number-start");
  const ruleBadwords = document.getElementById("rule-badwords");

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

    // Regra 1: comprimento entre 5 e 20 caracteres
    if (trimmed.length >= 5 && trimmed.length <= 20) {
      ruleLength.classList.add("valid");
    } else {
      ruleLength.classList.remove("valid");
    }

    // Regra 2: apenas letras, números e underscores
    if (/^[A-Za-z0-9_]*$/.test(trimmed)) {
      ruleSpecial.classList.add("valid");
    } else {
      ruleSpecial.classList.remove("valid");
    }

    // Regra 3: primeira letra maiúscula
    if (trimmed.length > 0 && /^[A-Z]/.test(trimmed)) {
      ruleFirstUpper.classList.add("valid");
    } else {
      ruleFirstUpper.classList.remove("valid");
    }

    // Regra 4: não começar com número
    if (trimmed.length > 0 && !/^[0-9]/.test(trimmed)) {
      ruleNoNumberStart.classList.add("valid");
    } else {
      ruleNoNumberStart.classList.remove("valid");
    }

    // Regra 5: sem palavras proibidas
    const hasBadword = badwords.some((bad) =>
      trimmed.toLowerCase().includes(bad)
    );
    if (!hasBadword) {
      ruleBadwords.classList.add("valid");
    } else {
      ruleBadwords.classList.remove("valid");
    }
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
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (regex.test(value.trim())) {
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

    // Verifica se todos os campos estão preenchidos
    const usernameVal = usernameInput.value.trim();
    const emailVal = emailInput.value.trim();
    const passwordVal = passwordInput.value.trim();
    const allFilled =
      usernameVal && emailVal && passwordVal && checkbox.checked;

    // Verifica se todas as regras estão validadas
    const usernameValid =
      document.querySelectorAll("#username-tooltip .valid").length === 5;
    const emailValid = ruleEmailFormat.classList.contains("valid");
    const passwordValid =
      document.querySelectorAll("#password-tooltip .valid").length === 5;
    const checkboxValid = checkbox.checked;

    if (
      !allFilled ||
      !usernameValid ||
      !emailValid ||
      !passwordValid ||
      !checkboxValid
    ) {
      showQuickWarning(
        "Por favor, preencha todos os campos corretamente e marque a checkbox."
      );
      return; // bloqueia cadastro
    }

    // Se passar tudo, pode enviar ou continuar com lógica de cadastro
    // Preparar dados
    const payload = {
      username: usernameVal,
      email: emailVal,
      password: passwordVal,
    };

    // Enviar via fetch para o Flask
    fetch("/register", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.status === "success") {
          showQuickWarning(data.message);

          // Limpa campos
          usernameInput.value = "";
          emailInput.value = "";
          passwordInput.value = "";
          checkbox.checked = false;

          // Fecha popup
          authOverlay.classList.remove("show");

          // Atualiza interface para mostrar que usuário está logado
          document.querySelector(".auth-buttons").innerHTML = `
                    <span class="welcome-message">Olá, ${usernameVal}!</span>
                    <button class="btn-logout" onclick="location.href='/logout'">Sair</button>
                `;
        } else {
          showQuickWarning(data.message);
        }
      })
      .catch((err) => {
        console.error(err);
        showQuickWarning("Erro ao registrar usuário.");
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
        // Exibe a mensagem do servidor no popup
        showQuickWarning(
          data.message,
          data.status === "success" ? "success" : "error"
        );

        if (data.status === "success") {
          authOverlay.classList.remove("show");
          const username = data.message.split(", ")[1].replace("!", "");

          let buttonsHTML = `
                    <span class="welcome-message">Olá, ${username}!</span>
                    <button class="btn-logout" onclick="location.href='/logout'">Sair</button>
                `;

          if (data.is_admin) {
            buttonsHTML += `<button class="btn-admin" onclick="location.href='/admin'">Admin</button>`;
          }

          document.querySelector(".auth-buttons").innerHTML = buttonsHTML;
        }
      })
      .catch((err) => {
        console.error(err);
        showQuickWarning("Erro ao realizar login.", "error");
      });
  });
});
