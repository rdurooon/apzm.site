// ===========================
// Elementos do DOM
// ===========================
const hamburger = document.getElementById("hamburger");
const sidebar = document.getElementById("sidebar");
const mapsItem = document.getElementById("maps-stories");
const mapsSubmenu = document.getElementById("maps-submenu");
const usersItem = document.getElementById("users");
const usersSubmenu = document.getElementById("users-submenu");

const adminContainer = document.querySelector(".admin-container"); // logo + título
const usersListContainer = document.getElementById("users-list-container");
let subguiaAtiva = null; // ou um valor inicial adequado

// ===========================
// Função: Abrir/Fechar Sidebar
// ===========================
function toggleSidebar() {
  sidebar.classList.toggle("active");

  if (sidebar.classList.contains("active")) {
    hamburger.innerHTML = "✖";
    hamburger.style.color = "white";
  } else {
    hamburger.innerHTML = "&#9776;";
    hamburger.style.color = "darkgreen";
  }
}

// ===========================
// Fechar sidebar automaticamente
// ===========================
function fecharSidebar() {
  if (sidebar.classList.contains("active")) {
    sidebar.classList.remove("active");
    hamburger.innerHTML = "&#9776;";
    hamburger.style.color = "darkgreen";
  }
}

// ===========================
// Função: Toggle Submenu Mapas/Historias
// ===========================
function toggleMapsSubmenu() {
  const isVisible = mapsSubmenu.style.display === "block";
  mapsSubmenu.style.display = isVisible ? "none" : "block";
  mapsItem.classList.toggle("open");
}

// ===========================
// Função: Toggle Submenu Usuários
// ===========================
function toggleUsersSubmenu() {
  const isVisible = usersSubmenu.style.display === "block";
  usersSubmenu.style.display = isVisible ? "none" : "block";
  usersItem.classList.toggle("open");
}

// ===========================
// Limpa todo conteúdo principal (logo, título e container de usuários)
// ===========================
function limparConteudoPrincipal() {
  // Esconde container padrão
  if (adminContainer) adminContainer.style.display = "none";

  // Limpa container de usuários
  if (usersListContainer) {
    usersListContainer.innerHTML = "";
    usersListContainer.style.display = "grid";
  }

  // Limpa container de cards para remover / reorganizar / linkar
  if (cardsListContainer) {
    cardsListContainer.innerHTML = "";
  }

  // Limpa container da subguia "Linkar"
  if (linkarContainer) {
    linkarContainer.innerHTML = "";
  }
}

// ===========================
// Renderiza usuários
// ===========================
async function listarUsuarios() {
  limparConteudoPrincipal();
  fecharSidebar(); // fecha sidebar ao clicar

  try {
    const res = await fetch("/admin/list_users");
    const users = await res.json();

    users.forEach((user) => {
      const card = document.createElement("div");
      card.classList.add("user-card");

      card.innerHTML = `
                <span class="username">${user.username}</span>
                <span class="created-at">${user.created_at}</span>
            `;
      usersListContainer.appendChild(card);
    });
  } catch (err) {
    console.error("Erro ao listar usuários:", err);
  }
}

// ===========================
// Elementos do DOM - Gerenciar Usuários
// ===========================
const gerenciarUsersItem = usersSubmenu.querySelector("li#gerenciar-usuarios"); // "Gerenciar"

// ===========================
// Função: Gerenciar usuários (unificada)
// ===========================
async function gerenciarUsuarios() {
  limparConteudoPrincipal();
  fecharSidebar();

  try {
    const res = await fetch("/admin/list_users");
    const allUsers = await res.json();

    // Remover barra de pesquisa anterior se existir
    const existingSearchContainer = document.querySelector("#users-search-container");
    if (existingSearchContainer) {
      existingSearchContainer.remove();
    }

    // Criar container com barra de pesquisa
    const searchContainer = document.createElement("div");
    searchContainer.id = "users-search-container";
    searchContainer.style.width = "100%";
    searchContainer.style.padding = "20px";
    searchContainer.style.boxSizing = "border-box";
    searchContainer.style.display = "flex";
    searchContainer.style.justifyContent = "center";
    searchContainer.style.marginBottom = "20px";

    const searchBar = document.createElement("div");
    searchBar.style.width = "100%";
    searchBar.style.maxWidth = "500px";
    searchBar.style.position = "relative";
    searchBar.style.display = "flex";
    searchBar.style.alignItems = "center";

    const searchIcon = document.createElement("span");
    searchIcon.textContent = "🔍";
    searchIcon.style.position = "absolute";
    searchIcon.style.left = "12px";
    searchIcon.style.fontSize = "18px";
    searchIcon.style.color = "#999";
    searchIcon.style.pointerEvents = "none";

    const searchInput = document.createElement("input");
    searchInput.type = "text";
    searchInput.placeholder = "Pesquisar usuário...";
    searchInput.style.width = "100%";
    searchInput.style.padding = "12px 12px 12px 45px";
    searchInput.style.border = "2px solid #ddd";
    searchInput.style.borderRadius = "8px";
    searchInput.style.fontSize = "16px";
    searchInput.style.boxSizing = "border-box";
    searchInput.style.transition = "border-color 0.3s";

    searchInput.addEventListener("focus", () => {
      searchInput.style.borderColor = "darkgreen";
    });
    searchInput.addEventListener("blur", () => {
      searchInput.style.borderColor = "#ddd";
    });

    searchBar.appendChild(searchIcon);
    searchBar.appendChild(searchInput);
    searchContainer.appendChild(searchBar);
    adminContainer.parentNode.insertBefore(searchContainer, usersListContainer);

    // Função para renderizar cards com base na pesquisa
    function renderUsers(usersToRender) {
      usersListContainer.innerHTML = "";

      if (usersToRender.length === 0) {
        usersListContainer.innerHTML = "<p style='text-align: center; color: #999;'>Nenhum usuário encontrado</p>";
        return;
      }

      usersToRender.forEach((user) => {
        const card = document.createElement("div");
        card.classList.add("user-card");

        card.innerHTML = `
                  <span class="username">${user.username}</span>
                  <span class="created-at">${user.created_at}</span>
                  <div class="user-actions">
                      <button class="admin-toggle">Promover Admin</button>
                      <button class="delete">&#128465;</button>
                  </div>
              `;

        const btnAdminToggle = card.querySelector(".admin-toggle");
        const btnDelete = card.querySelector(".delete");

        // ===========================
        // Atualizar estado do botão
        // ===========================
        function updateAdminButton() {
          if (user.is_admin) {
            btnAdminToggle.textContent = "Remover Admin";
            btnAdminToggle.style.background = "#e74c3c";
            createTooltip(btnAdminToggle, "Remover Admin", "#e74c3c");
          } else {
            btnAdminToggle.textContent = "Promover Admin";
            btnAdminToggle.style.background = "#3498db";
            createTooltip(btnAdminToggle, "Promover para Admin", "#3498db");
          }
        }

        updateAdminButton();

        // ===========================
        // Toggle Admin
        // ===========================
        btnAdminToggle.addEventListener("click", async () => {
          if (user.username === loggedInUser) {
            return showQuickWarning(
              "Você não pode mudar seu próprio status de admin!",
              "error"
            );
          }

          try {
            if (user.is_admin) {
              // Remover admin
              await fetch(`/admin/demote/${user.id}`, { method: "POST" });
              user.is_admin = false;
              showQuickWarning(`${user.username} removido de admin!`, "success");
            } else {
              // Promover admin
              await fetch(`/admin/promote/${user.id}`, { method: "POST" });
              user.is_admin = true;
              showQuickWarning(`${user.username} promovido a admin!`, "success");
            }
            updateAdminButton();
          } catch (err) {
            console.error(err);
            showQuickWarning("Erro ao alterar status de admin!", "error");
          }
        });

        // ===========================
        // Deletar usuário
        // ===========================
        btnDelete.addEventListener("click", async () => {
          if (user.username === loggedInUser) {
            return showQuickWarning(
              "Você não pode deletar sua própria conta!",
              "error"
            );
          }
          const confirmDelete = await showDeletePopup(user.username);
          if (confirmDelete) {
            await fetch(`/admin/delete/${user.id}`, { method: "DELETE" });
            card.remove();
            showQuickWarning(`${user.username} deletado!`, "success");
          }
        });

        createTooltip(btnDelete, "Deletar Usuário", "#e74c3c");

        usersListContainer.appendChild(card);
      });
    }

    // Renderizar todos inicialmente
    renderUsers(allUsers);

    // ===========================
    // Filtro em tempo real
    // ===========================
    searchInput.addEventListener("input", (e) => {
      const searchTerm = e.target.value.toLowerCase();
      const filteredUsers = allUsers.filter((user) =>
        user.username.toLowerCase().startsWith(searchTerm)
      );
      renderUsers(filteredUsers);
    });
  } catch (err) {
    console.error("Erro ao gerenciar usuários:", err);
  }
}

// ===========================
// Evento de clique - Gerenciar Usuários
// ===========================
gerenciarUsersItem.addEventListener("click", gerenciarUsuarios);

// ===========================
// Função: Criar popup rápido customizado (Toast)
// ===========================
function showQuickWarning(message, type = "error") {
  const toastContainer = document.getElementById("toast-container") || createToastContainer();
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
    <span class="toast-icon">${icons[type] || icons.error}</span>
    <span class="toast-message">${escapeHtmlAdmin(message)}</span>
    <button class="toast-close" aria-label="Fechar notificação">×</button>
  `;
  
  toastContainer.appendChild(toastEl);
  
  // Trigger animação de entrada
  setTimeout(() => {
    toastEl.classList.add("show");
  }, 10);
  
  // Fechar pelo botão
  toastEl.querySelector(".toast-close").addEventListener("click", () => {
    removeToastAdmin(toastId);
  });
  
  // Fechar automaticamente após 3.5s
  const autoCloseTimer = setTimeout(() => {
    removeToastAdmin(toastId);
  }, 3500);
  
  // Remover timer se o toast for fechado manualmente
  toastEl.addEventListener("transitionend", () => {
    if (!toastEl.classList.contains("show")) {
      clearTimeout(autoCloseTimer);
      toastEl.remove();
    }
  });
}

function createToastContainer() {
  const container = document.createElement("div");
  container.id = "toast-container";
  container.className = "toast-container";
  document.body.appendChild(container);
  return container;
}

function removeToastAdmin(toastId) {
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

function escapeHtmlAdmin(text) {
  const map = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;"
  };
  return text.replace(/[&<>"']/g, (char) => map[char]);
}

// ===========================
// Função: Criar tooltip customizado
// ===========================
function createTooltip(button, text, color = "#ccc") {
  const tooltip = document.createElement("span");
  tooltip.classList.add("custom-tooltip");
  tooltip.textContent = text;
  tooltip.style.position = "absolute";
  tooltip.style.padding = "5px 10px";
  tooltip.style.borderRadius = "6px";
  tooltip.style.background = color;
  tooltip.style.color = "white";
  tooltip.style.fontSize = "0.9rem";
  tooltip.style.whiteSpace = "nowrap";
  tooltip.style.top = "-35px";
  tooltip.style.left = "50%";
  tooltip.style.transform = "translateX(-50%)";
  tooltip.style.pointerEvents = "none";
  tooltip.style.opacity = "0";
  tooltip.style.transition = "opacity 0.3s";
  button.style.position = "relative";
  button.appendChild(tooltip);

  button.addEventListener("mouseenter", () => {
    tooltip.style.opacity = "1";
  });
  button.addEventListener("mouseleave", () => {
    tooltip.style.opacity = "0";
  });
}

// ===========================
// Função: Criar popup de confirmação
// ===========================
function showDeletePopup(username) {
  return new Promise((resolve) => {
    // Cria overlay
    const overlay = document.createElement("div");
    overlay.style.position = "fixed";
    overlay.style.top = "0";
    overlay.style.left = "0";
    overlay.style.width = "100vw";
    overlay.style.height = "100vh";
    overlay.style.background = "rgba(0,0,0,0.5)";
    overlay.style.display = "flex";
    overlay.style.justifyContent = "center";
    overlay.style.alignItems = "center";
    overlay.style.zIndex = "10000";

    // Cria popup
    const popup = document.createElement("div");
    popup.style.background = "white";
    popup.style.borderRadius = "10px";
    popup.style.padding = "20px 30px";
    popup.style.boxShadow = "0 5px 15px rgba(0,0,0,0.3)";
    popup.style.textAlign = "center";
    popup.style.minWidth = "300px";

    // Pergunta
    const question = document.createElement("p");
    question.textContent = `Deseja realmente deletar ${username}?`;
    question.style.marginBottom = "20px";
    question.style.fontWeight = "500";
    popup.appendChild(question);

    // Botões
    const btnContainer = document.createElement("div");
    btnContainer.style.display = "flex";
    btnContainer.style.justifyContent = "space-around";

    const btnConfirm = document.createElement("button");
    btnConfirm.textContent = "Confirmar";
    btnConfirm.style.background = "#2ecc71"; // verde
    btnConfirm.style.color = "white";
    btnConfirm.style.border = "none";
    btnConfirm.style.padding = "10px 20px";
    btnConfirm.style.borderRadius = "8px";
    btnConfirm.style.cursor = "pointer";
    btnConfirm.style.fontWeight = "500";

    const btnCancel = document.createElement("button");
    btnCancel.textContent = "Cancelar";
    btnCancel.style.background = "#e74c3c"; // vermelho
    btnCancel.style.color = "white";
    btnCancel.style.border = "none";
    btnCancel.style.padding = "10px 20px";
    btnCancel.style.borderRadius = "8px";
    btnCancel.style.cursor = "pointer";
    btnCancel.style.fontWeight = "500";

    btnContainer.appendChild(btnConfirm);
    btnContainer.appendChild(btnCancel);
    popup.appendChild(btnContainer);
    overlay.appendChild(popup);
    document.body.appendChild(overlay);

    // Eventos
    btnConfirm.addEventListener("click", () => {
      document.body.removeChild(overlay);
      resolve(true);
    });
    btnCancel.addEventListener("click", () => {
      document.body.removeChild(overlay);
      resolve(false);
    });
  });
}

// ===========================
// Função: Alterar usuários (promover/remover admin e deletar) - atualizado
// ===========================


// ===========================
// Eventos de clique
// ===========================
hamburger.addEventListener("click", toggleSidebar);
mapsItem.addEventListener("click", () => {
  toggleMapsSubmenu();
});
usersItem.addEventListener("click", () => {
  toggleUsersSubmenu();
});

// ===========================
// Subguia "Adicionar" - Handler
// ===========================
const addMapStoryItem = mapsSubmenu.querySelector("li.add-map-story");
addMapStoryItem.addEventListener("click", adicionarCards);

// ===========================
// Função: Listar e remover cards
// ===========================
const cardsListContainer = document.getElementById("cards-list-container");

// ===========================
// Função: Editar cards - SEM AUTO-SAVE
// ===========================
async function editarCards() {
  limparConteudoPrincipal();
  fecharSidebar();

  cardsListContainer.innerHTML = "";

  try {
    const res = await fetch("/admin/list_cards");
    const cards = await res.json();

    if (!cards.length) {
      cardsListContainer.innerHTML = "<p>Nenhum card encontrado.</p>";
      return;
    }

    cards.forEach((card, index) => {
      // Wrapper para card + botão de remover
      const cardWrapper = document.createElement("div");
      cardWrapper.className = "card-wrapper";

      // Card principal
      const cardDiv = document.createElement("div");
      cardDiv.classList.add("reorganizar-card");
      cardDiv.dataset.index = index;
      cardDiv.dataset.file = card.file;
      cardDiv.dataset.cardTitle = card.title;

      // Estado de visibilidade
      const isInitiallyVisible = card.hasOwnProperty("visible")
        ? !!card.visible
        : true;
      cardDiv.dataset.visible = isInitiallyVisible ? "true" : "false";
      if (!isInitiallyVisible) cardDiv.classList.add("invisible");

      // Imagem e botões
      cardDiv.innerHTML = `
        <img src="/static/images/cards/${card.file}" alt="${card.title}">
        <button class="btn-left">&lt;</button>
        <button class="btn-right">&gt;</button>
      `;

      cardDiv.dataset.newSince = card.new_since || "";

      // ========== BOTÃO "NOVO!" ==========
      // NÃO sofre interferência do toggle overlay
      const badgeBtn = document.createElement("div");
      badgeBtn.className = "new-badge-toggle" + (card.is_new ? " active" : "");
      badgeBtn.textContent = "Novo!";
      
      // Listener APENAS para o badge (não para o card inteiro)
      badgeBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        e.preventDefault();
        
        // Toggle visual local
        badgeBtn.classList.toggle("active");
        
        showQuickWarning(
          `Card ${card.title} ${
            badgeBtn.classList.contains("active")
              ? "marcado como 'Novo!'"
              : "removido de 'Novo!'"
          }. Clique em "Salvar Alterações" para confirmar.`,
          "info"
        );
      });
      
      cardDiv.appendChild(badgeBtn);

      // ========== OVERLAY PARA TOGGLE DE VISIBILIDADE ==========
      const toggleOverlay = document.createElement("div");
      toggleOverlay.className = "toggle-overlay";
      
      // Listener para o overlay (não interfere com badge nem com botões)
      toggleOverlay.addEventListener("click", (e) => {
        e.stopPropagation();
        
        // Toggle visibilidade
        const currentlyVisible = cardDiv.dataset.visible === "true";
        cardDiv.dataset.visible = currentlyVisible ? "false" : "true";
        cardDiv.classList.toggle("invisible", currentlyVisible);

        showQuickWarning(
          `Card ${currentlyVisible ? "marcado para desaparecer" : "marcado para aparecer"}. Clique em "Salvar Alterações" para confirmar.`,
          "info"
        );
      });
      
      cardDiv.appendChild(toggleOverlay);

      // ========== BOTÕES DE NAVEGAÇÃO (SETAS) ==========
      const btnLeft = cardDiv.querySelector(".btn-left");
      btnLeft.addEventListener("click", (e) => {
        e.stopPropagation();
        moverCard(cardDiv, -1);
        atualizarBotoes();
      });

      const btnRight = cardDiv.querySelector(".btn-right");
      btnRight.addEventListener("click", (e) => {
        e.stopPropagation();
        moverCard(cardDiv, 1);
        atualizarBotoes();
      });

      // ========== BOTÃO REMOVER (FORA DO CARD) ==========
      const removeBtn = document.createElement("button");
      removeBtn.className = "btn-remove-card";
      removeBtn.innerHTML = "🗑️ Remover";
      removeBtn.style.backgroundColor = "#e74c3c";
      removeBtn.style.color = "white";
      removeBtn.style.border = "none";
      removeBtn.style.padding = "10px 15px";
      removeBtn.style.borderRadius = "6px";
      removeBtn.style.cursor = "pointer";
      removeBtn.style.fontSize = "14px";
      removeBtn.style.fontWeight = "bold";
      removeBtn.style.transition = "background-color 0.3s ease";
      removeBtn.style.width = "100%";
      removeBtn.style.marginTop = "8px";
      
      removeBtn.addEventListener("mouseenter", () => {
        removeBtn.style.backgroundColor = "#c0392b";
      });
      removeBtn.addEventListener("mouseleave", () => {
        removeBtn.style.backgroundColor = "#e74c3c";
      });
      removeBtn.addEventListener("click", async (e) => {
        e.stopPropagation();
        const confirmar = await showDeletePopup(card.title);
        if (confirmar) {
          // Marca para remover (não remove ainda)
          cardWrapper.dataset.markedForDelete = "true";
          cardWrapper.style.opacity = "0.5";
          removeBtn.innerHTML = "✓ Marcado para Remover";
          removeBtn.style.backgroundColor = "#27ae60";
          showQuickWarning(
            `Card ${card.title} marcado para remover. Clique em "Salvar Alterações" para confirmar.`,
            "info"
          );
        }
      });

      // Montar wrapper
      cardWrapper.appendChild(cardDiv);
      cardWrapper.appendChild(removeBtn);
      cardsListContainer.appendChild(cardWrapper);
    });

    atualizarBotoes();

    // ========== BOTÃO SALVAR ALTERAÇÕES ==========
    const existingSaveBtn = cardsListContainer.querySelector(".btn-save-cards");
    if (existingSaveBtn) existingSaveBtn.remove();

    const saveBtn = document.createElement("button");
    saveBtn.textContent = "Salvar Alterações";
    saveBtn.classList.add("btn-save-cards");
    saveBtn.addEventListener("click", () => salvarAlteracoes(cards));
    cardsListContainer.appendChild(saveBtn);
  } catch (err) {
    console.error("Erro ao listar/editar cards:", err);
    showQuickWarning("Erro ao carregar cards!", "error");
  }

  initNewBadgeTimers();
}

// ===========================
// Função: Salvar alterações (visibilidade, ordem e badges)
// ===========================
async function salvarAlteracoes(originalCards) {
  try {
    // ========== DELETAR CARDS MARCADOS ==========
    const cardWrappersMarkedForDelete = Array.from(cardsListContainer.querySelectorAll(".card-wrapper[data-marked-for-delete='true']"));
    
    for (const wrapper of cardWrappersMarkedForDelete) {
      const cardDiv = wrapper.querySelector(".reorganizar-card");
      const file = cardDiv.dataset.file;
      
      try {
        const resp = await fetch(`/admin/delete_map_story/${file}`, {
          method: "DELETE",
        });
        const data = await resp.json();
        if (data.success) {
          wrapper.remove();
          showQuickWarning(`Card ${data.card_name} removido!`, "success");
        } else {
          showQuickWarning(`Erro ao remover card: ${data.error}`, "error");
        }
      } catch (err) {
        console.error("Erro ao remover card:", err);
        showQuickWarning("Erro ao remover card!", "error");
      }
    }

    // ========== SALVAR ORDEM E VISIBILIDADE ==========
    const cardDivs = Array.from(cardsListContainer.querySelectorAll(".reorganizar-card:not([data-marked-for-delete])"));
    
    const cardsData = cardDivs.map((cardDiv) => {
      const file = cardDiv.dataset.file;
      const originalCard = originalCards.find(c => c.file === file);
      const badgeBtn = cardDiv.querySelector(".new-badge-toggle");
      
      return {
        file: file,
        visible: cardDiv.dataset.visible === "true",
        is_new: badgeBtn ? badgeBtn.classList.contains("active") : (originalCard?.is_new || false),
      };
    });

    // Salvar ordem e visibilidade
    const resOrder = await fetch("/admin/save_cards_order", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(cardsData.map(c => ({ file: c.file, visible: c.visible }))),
    });

    const dataOrder = await resOrder.json();
    if (!dataOrder.success) {
      showQuickWarning("Erro ao salvar ordem e visibilidade!", "error");
      return;
    }

    // ========== SALVAR BADGES "NOVO!" ==========
    for (const card of cardsData) {
      const originalCard = originalCards.find(c => c.file === card.file);
      if (card.is_new !== (originalCard?.is_new || false)) {
        try {
          await fetch(`/admin/toggle_card_new/${card.file}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ is_new: card.is_new }),
          });
        } catch (err) {
          console.error(`Erro ao salvar badge para ${card.file}:`, err);
        }
      }
    }

    showQuickWarning("Alterações salvas com sucesso!", "success");
  } catch (err) {
    console.error("Erro ao salvar alterações:", err);
    showQuickWarning("Erro de rede ao salvar!", "error");
  }
}


// ===========================
// Função: Adicionar Mapa/História
// ===========================
async function adicionarCards() {
  limparConteudoPrincipal();
  fecharSidebar();

  const container = document.createElement("div");
  container.className = "adicionar-card-page";
  container.style.padding = "40px";
  container.style.display = "flex";
  container.style.flexDirection = "column";
  container.style.height = "100%";

  container.innerHTML = `
    <h2 style="text-align: center; margin-bottom: 30px; color: #333;">Adicionar Mapa/História</h2>
    
    <div style="display: flex; gap: 40px; flex: 1; align-items: stretch;">
      <!-- Card Image - Left Column (Full Height) -->
      <div class="add-card-image" style="
        flex: 0 0 350px;
        border: 3px dashed #ccc;
        border-radius: 8px;
        cursor: pointer;
        background-color: #f9f9f9;
        position: relative;
        transition: all 0.3s ease;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
      ">
        <div style="text-align: center;">
          <span style="font-size: 60px; color: #999; display: block;">+</span>
          <div style="font-size: 14px; color: #999; margin-top: 10px;">Inserir card</div>
        </div>
      </div>

      <!-- Right Column -->
      <div style="display: flex; flex-direction: column; gap: 20px; flex: 1;">
        <!-- Title Image -->
        <div class="add-title-image" style="
          width: 100%;
          height: 150px;
          border: 3px dashed #ccc;
          border-radius: 8px;
          cursor: pointer;
          background-color: #f9f9f9;
          position: relative;
          transition: all 0.3s ease;
          overflow: hidden;
          display: flex;
          align-items: center;
          justify-content: center;
        ">
          <div style="text-align: center;">
            <span style="font-size: 40px; color: #999; display: block;">+</span>
            <div style="font-size: 14px; color: #999; margin-top: 5px;">Inserir título</div>
          </div>
        </div>

        <!-- Texto do Título -->
        <input id="add-title-text" type="text" placeholder="Inserir texto do título aqui..." style="
          padding: 12px;
          border: 2px solid #ddd;
          border-radius: 8px;
          font-family: Arial, sans-serif;
          font-size: 16px;
        ">

        <!-- Description -->
        <textarea id="add-description" placeholder="Inserir descrição aqui..." style="
          flex: 1;
          padding: 12px;
          border: 2px solid #ddd;
          border-radius: 8px;
          font-family: Arial, sans-serif;
          resize: none;
          min-height: 100px;
        "></textarea>

        <!-- Buttons -->
        <div style="display: flex; gap: 10px; justify-content: center;">
          <button id="add-save-btn" style="
            padding: 12px 30px;
            background-color: #2ecc71;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            font-size: 16px;
            transition: background-color 0.3s ease;
          ">Salvar</button>
          <button id="add-cancel-btn" style="
            padding: 12px 30px;
            background-color: #e74c3c;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            font-size: 16px;
            transition: background-color 0.3s ease;
          ">Cancelar</button>
        </div>
      </div>
    </div>
  `;

  adminContainer.style.display = "flex";
  adminContainer.style.flexDirection = "column";
  adminContainer.innerHTML = "";
  adminContainer.appendChild(container);

  // Setup image uploads
  const cardImageEl = container.querySelector(".add-card-image");
  const titleImageEl = container.querySelector(".add-title-image");
  const titleTextEl = container.querySelector("#add-title-text");
  const saveBtn = container.querySelector("#add-save-btn");
  const cancelBtn = container.querySelector("#add-cancel-btn");

  function setupImageUploadPage(el) {
    const fileInput = document.createElement("input");
    fileInput.type = "file";
    fileInput.accept = "image/*";
    fileInput.style.display = "none";
    document.body.appendChild(fileInput);

    el.addEventListener("click", () => fileInput.click());
    el.addEventListener("mouseenter", () => {
      el.style.borderColor = "#27ae60";
      el.style.backgroundColor = "#ecf0f1";
    });
    el.addEventListener("mouseleave", () => {
      el.style.borderColor = "#ccc";
      el.style.backgroundColor = "#f9f9f9";
    });

    fileInput.addEventListener("change", () => {
      const file = fileInput.files[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (e) => {
        const img = document.createElement("img");
        img.src = e.target.result;
        img.style.width = "100%";
        img.style.height = "100%";
        img.style.objectFit = "cover";
        img.style.borderRadius = "8px";
        img.file = file; // save file reference
        el.innerHTML = "";
        el.appendChild(img);
      };
      reader.readAsDataURL(file);
    });

    return fileInput;
  }

  const cardFileInput = setupImageUploadPage(cardImageEl);
  const titleFileInput = setupImageUploadPage(titleImageEl);

  // Handle buttons
  saveBtn.addEventListener("click", async () => {
    const cardImg = cardImageEl.querySelector("img");
    const titleImg = titleImageEl.querySelector("img");
    const titleText = titleTextEl.value.trim();
    const description = container.querySelector("#add-description").value.trim();

    if (!cardImg) {
      showQuickWarning("Selecione a imagem do card!", "warning");
      return;
    }

    if (!titleText) {
      showQuickWarning("Preencha o texto do título!", "warning");
      return;
    }

    if (!description) {
      showQuickWarning("Preencha a descrição!", "warning");
      return;
    }

    // If no title image, use card image as fallback
    let titleImageFile = titleImg ? titleImg.file : cardImg.file;

    const formData = new FormData();
    formData.append("title_text", titleText);
    formData.append("description", description);
    formData.append("card_image", cardImg.file);
    formData.append("title_image", titleImageFile);

    try {
      saveBtn.disabled = true;
      const res = await fetch("/admin/add_map_story", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (data.success) {
        showQuickWarning("Mapa/História salvo com sucesso!", "success");

        // Clear form
        cardImageEl.innerHTML = '<div style="text-align: center;"><span style="font-size: 60px; color: #999; display: block;">+</span><div style="font-size: 14px; color: #999; margin-top: 10px;">Inserir card</div></div>';
        titleImageEl.innerHTML = '<div style="text-align: center;"><span style="font-size: 40px; color: #999; display: block;">+</span><div style="font-size: 14px; color: #999; margin-top: 5px;">Inserir título</div></div>';
        titleTextEl.value = "";
        container.querySelector("#add-description").value = "";
      } else {
        showQuickWarning(`Erro: ${data.error || "Não foi possível salvar"}`, "error");
      }
    } catch (err) {
      console.error(err);
      showQuickWarning("Erro ao salvar!", "error");
    } finally {
      saveBtn.disabled = false;
    }
  });

  cancelBtn.addEventListener("click", () => {
    // Clear only the form content, keep the page open
    cardImageEl.innerHTML = '<div style="text-align: center;"><span style="font-size: 60px; color: #999; display: block;">+</span><div style="font-size: 14px; color: #999; margin-top: 10px;">Inserir card</div></div>';
    titleImageEl.innerHTML = '<div style="text-align: center;"><span style="font-size: 40px; color: #999; display: block;">+</span><div style="font-size: 14px; color: #999; margin-top: 5px;">Inserir título</div></div>';
    titleTextEl.value = "";
    container.querySelector("#add-description").value = "";
  });
}

const editarMapStoryItem = mapsSubmenu.querySelector("li:nth-child(2)"); // "Editar" (antes era "Remover" e "Reorganizar")

// Evento de clique - Editar Cards
editarMapStoryItem.addEventListener("click", editarCards);

// ===========================
// Função: Reorganizar cards (REMOVIDA - AGORA INTEGRADA EM editarCards)
// ===========================
// ===========================
// Função: mover card na tela
// ===========================
function moverCard(cardEl, direction) {
  // cardEl é .reorganizar-card, seu parent é .card-wrapper
  const cardWrapper = cardEl.parentElement;
  const allWrappers = Array.from(cardsListContainer.querySelectorAll(".card-wrapper"));
  const currentIndex = allWrappers.indexOf(cardWrapper);
  const newIndex = currentIndex + direction;

  if (newIndex < 0 || newIndex >= allWrappers.length) return;

  if (direction === -1) {
    cardsListContainer.insertBefore(cardWrapper, allWrappers[newIndex]);
  } else {
    cardsListContainer.insertBefore(cardWrapper, allWrappers[newIndex].nextSibling);
  }
}

// ===========================
// Função: Atualizar visibilidade dos botões
// ===========================
function atualizarBotoes() {
  const cardWrappers = Array.from(cardsListContainer.querySelectorAll(".card-wrapper"));

  cardWrappers.forEach((wrapper, idx) => {
    const cardDiv = wrapper.querySelector(".reorganizar-card");
    const btnLeft = cardDiv.querySelector(".btn-left");
    const btnRight = cardDiv.querySelector(".btn-right");

    // Se for o primeiro, não tem esquerda
    if (idx === 0) {
      btnLeft.style.display = "none";
    } else {
      btnLeft.style.display = "block";
    }

    // Se for o último, não tem direita
    if (idx === cardWrappers.length - 1) {
      btnRight.style.display = "none";
    } else {
      btnRight.style.display = "block";
    }
  });
}

// ===========================
// Função: salvarOrdemCards() - DESCONTINUADA
// Substituída por salvarAlteracoes() que é chamada pelo botão "Salvar Alterações"
// ===========================


const linkarMapStoryItem = mapsSubmenu.querySelector("li:nth-child(3)"); // "Linkar"
const linkarContainer = document.getElementById("linkarContainer");

async function abrirSubguiaLinkar() {
  limparConteudoPrincipal();
  fecharSidebar();

  linkarContainer.innerHTML = ""; // limpa container

  try {
    const res = await fetch("/admin/list_links");
    const cards = await res.json();

    if (!cards.length) {
      linkarContainer.innerHTML = "<p>Nenhum card encontrado.</p>";
      return;
    }

    cards.forEach((card) => {
      const div = document.createElement("div");
      div.classList.add("linkar-card-container");

      div.innerHTML = `
              <div class="linkar-card-left">
                  <img src="/static/images/cards/${card.file}" alt="${
        card.title
      }">
              </div>
              <div class="linkar-card-right">
                  <h3 class="linkar-card-title">${card.title}</h3>
                  <div class="link-fields">
                      <label>Linkar História</label>
                      <input type="text" placeholder="Cole o link da história" value="${
                        card.link_historia || ""
                      }" class="historia-link">
                      
                      <label>Linkar Mapa</label>
                      <input type="text" placeholder="Cole o link do mapa" value="${
                        card.link_mapa || ""
                      }" class="mapa-link">
                  </div>
                  <button class="save-links">Salvar Alterações</button>
              </div>
          `;

      const btnSave = div.querySelector(".save-links");
      const inputHistoria = div.querySelector(".historia-link");
      const inputMapa = div.querySelector(".mapa-link");

      btnSave.addEventListener("click", async () => {
        btnSave.disabled = true;
        btnSave.textContent = "Salvando...";
        try {
          const res = await fetch(`/admin/save_card_links/${card.file}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              historia: inputHistoria.value.trim(),
              mapa: inputMapa.value.trim(),
            }),
          });
          const data = await res.json();
          if (data.success)
            showQuickWarning("Links salvos com sucesso!", "green");
          else showQuickWarning("Erro ao salvar links!", "red");
        } catch (err) {
          console.error(err);
          showQuickWarning("Erro de rede!", "red");
        } finally {
          btnSave.disabled = false;
          btnSave.textContent = "Salvar Alterações";
        }
      });

      linkarContainer.appendChild(div);
    });
  } catch (err) {
    console.error(err);
    showQuickWarning("Erro ao carregar cards!", "red");
  }
}

linkarMapStoryItem.addEventListener("click", abrirSubguiaLinkar);

// ===========================
// Site Online/Offline Toggle
// ===========================
const siteToggleContainer = document.createElement("div");
siteToggleContainer.style.position = "absolute";
siteToggleContainer.style.top = "20px";
siteToggleContainer.style.right = "20px";
siteToggleContainer.style.display = "none";
siteToggleContainer.style.alignItems = "center";
siteToggleContainer.style.gap = "10px";

const siteToggleLabel = document.createElement("span");
siteToggleLabel.textContent = "Site Online:";
siteToggleContainer.appendChild(siteToggleLabel);

const siteToggle = document.createElement("input");
siteToggle.type = "checkbox";
siteToggle.style.width = "40px";
siteToggle.style.height = "20px";
siteToggleContainer.appendChild(siteToggle);

document.body.appendChild(siteToggleContainer);

// Inicializa estado
fetch("/api/site_status.json")
  .then((res) => res.json())
  .then((data) => {
    siteToggle.checked = data.online;
  })
  .catch((err) => console.error(err));

// Evento de mudança
siteToggle.addEventListener("change", async () => {
  const online = siteToggle.checked;
  try {
    const res = await fetch("/admin/toggle_site", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ online }),
    });
    const data = await res.json();
    if (data.success) {
      showQuickWarning(
        `Site ${online ? "online" : "offline"}!`,
        online ? "green" : "red"
      );
    } else {
      showQuickWarning("Erro ao alterar status do site!", "red");
    }
  } catch (err) {
    console.error(err);
    showQuickWarning("Erro de rede!", "red");
  }
});

if (subguiaAtiva === "visao-geral") {
  siteToggleContainer.style.display = "flex";
} else {
  siteToggleContainer.style.display = "none";
}

const visaoGeralItem = document.querySelector(
  ".sidebar-menu li:first-child .menu-item"
);
visaoGeralItem.addEventListener("click", () => {
  // Alterna visibilidade do toggle
  if (siteToggleContainer.style.display === "none") {
    siteToggleContainer.style.display = "flex";
    subguiaAtiva = "visao-geral";
  } else {
    siteToggleContainer.style.display = "none";
    subguiaAtiva = null;
  }
});

// ===========================
// Inicialização: Página Carregada
// ===========================
// Força estado inicial
window.addEventListener("DOMContentLoaded", () => {
  sidebar.classList.add("active");
  hamburger.innerHTML = "✖";
  hamburger.style.color = "white";
});

function initNewBadgeTimers() {
  const cards = document.querySelectorAll(".reorganizar-card");
  cards.forEach((card) => {
    const badge = card.querySelector(".new-badge-toggle");
    if (!badge) return;

    // Só ativa se is_new estiver true
    if (!badge.classList.contains("active")) return;

    const newSince = card.dataset.newSince;
    if (!newSince) return;

    const badgeTime = new Date(newSince).getTime();
    updateBadge(card, badge, badgeTime);

    const interval = setInterval(() => {
      updateBadge(card, badge, badgeTime, interval);
    }, 1000);
  });
}

async function updateBadge(card, badge, badgeTime, interval = null) {
  const now = Date.now();
  const diffSeconds = (now - badgeTime) / 1000;

  // Remove se passou 7 dias (ou 5 segundos para teste)
  if (diffSeconds >= 5 && badge.classList.contains("active")) {
    badge.classList.remove("active");
    badge.style.pointerEvents = "none";
    if (interval) clearInterval(interval);

    try {
      await fetch(`/admin/toggle_card_new/${card.dataset.file}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_new: false }),
      });
    } catch (err) {
      console.error("Erro ao atualizar badge Novo!", err);
    }
  }
}

// ===========================
// Elementos do DOM - Parceiros
// ===========================
const partnersItem = document.getElementById("partners");
const partnersSubmenu = document.getElementById("partners-submenu");

// ===========================
// Função: Toggle Submenu Parceiros
// ===========================
function togglePartnersSubmenu() {
  const isVisible = partnersSubmenu.style.display === "block";
  partnersSubmenu.style.display = isVisible ? "none" : "block";
  partnersItem.classList.toggle("open");
}

// ===========================
// Eventos de clique - Parceiros
// ===========================
partnersItem.addEventListener("click", () => {
  togglePartnersSubmenu();
});

// Selecionando subguias
const addPartnerItem = partnersSubmenu.querySelector(".add-partner");
const removePartnerItem = partnersSubmenu.querySelector(".remove-partner");
const editPartnerItem = partnersSubmenu.querySelector(".edit-partner");
const reorderPartnerItem = partnersSubmenu.querySelector(".reorder-partner");

// ===========================
// Ações de exemplo (ainda placeholders)
// ===========================
addPartnerItem.addEventListener("click", () => {
  limparConteudoPrincipal();
  fecharSidebar();

  const main = document.querySelector("admin-content");

  main.innerHTML = `
    <div class="partner-form" style="display: flex;">
      <h2 class="form-title">Adicionar Parceiro</h2>

      <!-- Upload Logo -->
      <label class="upload-box">
        <input type="file" accept="image/*" hidden id="partner-logo">
        <span class="plus">+</span>
        <img id="preview-logo" class="preview hidden" />
        <p>Adicionar Logo</p>
      </label>

      <!-- Upload Fundo -->
      <label class="upload-box">
        <input type="file" accept="image/*" hidden id="partner-bg">
        <span class="plus">+</span>
        <img id="preview-bg" class="preview hidden" />
        <p>Adicionar Fundo</p>
      </label>

      <!-- Descrição -->
      <textarea id="partner-desc" placeholder="Descrição do parceiro..."></textarea>

      <!-- Links -->
      <div class="links">
        <label>Website: <input type="url" id="partner-site" placeholder="https://"></label>
        <label>Instagram: <input type="url" id="partner-insta" placeholder="https://instagram.com/..."></label>
        <label>Twitter/X: <input type="url" id="partner-twitter" placeholder="https://x.com/..."></label>
      </div>

      <button class="btn-save-partner">Salvar</button>
    </div>
  `;

  // Função de preview
  function handlePreview(inputId, previewId) {
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);

    input.addEventListener("change", () => {
      const file = input.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = e => {
          preview.src = e.target.result;
          preview.classList.remove("hidden");
          preview.previousElementSibling.style.display = "none"; // esconde o "+"
        };
        reader.readAsDataURL(file);
      }
    });
  }

  handlePreview("partner-logo", "preview-logo");
  handlePreview("partner-bg", "preview-bg");
});

removePartnerItem.addEventListener("click", () => {
  limparConteudoPrincipal();
  fecharSidebar();
});

editPartnerItem.addEventListener("click", () => {
  limparConteudoPrincipal();
  fecharSidebar();
});

reorderPartnerItem.addEventListener("click", () => {
  limparConteudoPrincipal();
  fecharSidebar();
});
