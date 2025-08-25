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
const listUsersItem = usersSubmenu.querySelector("li:first-child"); // "Listar Usuários"

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
  if (adminContainer) adminContainer.style.display = "none";
  usersListContainer.innerHTML = "";
  usersListContainer.style.display = "grid";
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
                <span class="created-at">Criado em: ${user.created_at}</span>
            `;
      usersListContainer.appendChild(card);
    });
  } catch (err) {
    console.error("Erro ao listar usuários:", err);
  }
}

// ===========================
// Elementos do DOM - Alterar Usuários
// ===========================
const alterarUsersItem = usersSubmenu.querySelector("li:last-child"); // "Alterar Usuários"

// ===========================
// Função: Criar popup rápido customizado
// ===========================
function showQuickWarning(message, color = "#ff5555") {
  let popup = document.getElementById("quick-warning");
  if (!popup) {
    popup = document.createElement("div");
    popup.id = "quick-warning";
    popup.style.position = "fixed";
    popup.style.top = "20px";
    popup.style.left = "50%";
    popup.style.transform = "translateX(-50%)";
    popup.style.background = color;
    popup.style.color = "white";
    popup.style.padding = "12px 20px";
    popup.style.borderRadius = "8px";
    popup.style.boxShadow = "0 5px 15px rgba(0,0,0,0.3)";
    popup.style.zIndex = "9999";
    popup.style.opacity = "0";
    popup.style.transition = "opacity 0.5s";
    document.body.appendChild(popup);
  }
  popup.textContent = message;
  popup.style.background = color;
  popup.style.display = "block";
  setTimeout(() => {
    popup.style.opacity = "1";
  }, 10);
  setTimeout(() => {
    popup.style.opacity = "0";
    setTimeout(() => {
      popup.style.display = "none";
    }, 500);
  }, 2000);
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
async function alterarUsuarios() {
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
                <div class="user-actions">
                    <button class="promote">&#x25B2;</button>
                    <button class="demote">&#x25BC;</button>
                    <button class="delete">&#128465;</button>
                </div>
            `;

      const btnPromote = card.querySelector(".promote");
      const btnDemote = card.querySelector(".demote");
      const btnDelete = card.querySelector(".delete");

      // ===========================
      // Bloqueios de botão conforme admin
      // ===========================
      if (user.is_admin) {
        btnPromote.disabled = true;
        btnPromote.style.opacity = "0.5";
      } else {
        btnDemote.disabled = true;
        btnDemote.style.opacity = "0.5";
      }

      // ===========================
      // Tooltips customizados
      // ===========================
      createTooltip(btnPromote, "Promover para Admin", "#3498db"); // azul
      createTooltip(btnDemote, "Remover Admin", "#e74c3c"); // vermelho
      createTooltip(btnDelete, "Deletar Usuário", "#e74c3c"); // vermelho

      // ===========================
      // Promover
      // ===========================
      btnPromote.addEventListener("click", async () => {
        if (btnPromote.disabled)
          return showQuickWarning("Usuário já é admin!", "#3498db");
        await fetch(`/admin/promote/${user.id}`, { method: "POST" });
        showQuickWarning(`${user.username} promovido a admin!`, "#3498db");
        alterarUsuarios(); // refresh
      });

      // ===========================
      // Remover admin
      // ===========================
      btnDemote.addEventListener("click", async () => {
        if (user.username === loggedInUser) {
          return showQuickWarning(
            "Você não pode remover seu próprio admin!",
            "#e74c3c"
          );
        }
        if (btnDemote.disabled)
          return showQuickWarning("Usuário não é admin!", "#e74c3c");
        await fetch(`/admin/demote/${user.id}`, { method: "POST" });
        showQuickWarning(`${user.username} removido de admin!`, "#e74c3c");
        alterarUsuarios(); // refresh
      });

      // ===========================
      // Deletar usuário
      // ===========================
      btnDelete.addEventListener("click", async () => {
        if (user.username === loggedInUser) {
          return showQuickWarning(
            "Você não pode deletar sua própria conta!",
            "#e74c3c"
          );
        }
        const confirmDelete = await showDeletePopup(user.username);
        if (confirmDelete) {
          await fetch(`/admin/delete/${user.id}`, { method: "DELETE" });
          card.remove();
          showQuickWarning(`${user.username} deletado!`, "#e74c3c");
        }
      });

      usersListContainer.appendChild(card);
    });
  } catch (err) {
    console.error("Erro ao alterar usuários:", err);
  }
}

// ===========================
// Evento de clique - Alterar Usuários
// ===========================
alterarUsersItem.addEventListener("click", alterarUsuarios);

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
listUsersItem.addEventListener("click", listarUsuarios);

// ===========================
// Elementos do popup adicionar
// ===========================
const addPopupOverlay = document.getElementById("add-popup-overlay");
const addPopupClose = document.getElementById("add-popup-close");
const saveMapStoryBtn = document.getElementById("save-map-story");

// Subguia "Adicionar"
const addMapStoryItem = mapsSubmenu.querySelector("li.add-map-story"); // crie essa li no HTML do menu

// ===========================
// Abrir popup adicionar mapa/história
// ===========================
addMapStoryItem.addEventListener("click", () => {
  addPopupOverlay.classList.add("show");
  fecharSidebar(); // fecha sidebar ao abrir popup
});

// ===========================
// Fechar popup adicionar
// ===========================
addPopupClose.addEventListener("click", () => {
  addPopupOverlay.classList.remove("show");
});

// ===========================
// Clique fora do popup fecha
// ===========================
addPopupOverlay.addEventListener("click", (e) => {
  if (e.target === addPopupOverlay) {
    addPopupOverlay.classList.remove("show");
  }
});

// ===========================
// Upload de imagens para Card e Título
// ===========================
function setupImageUpload(el) {
  const fileInput = document.createElement("input");
  fileInput.type = "file";
  fileInput.accept = "image/*"; // permite qualquer imagem
  fileInput.style.display = "none";
  document.body.appendChild(fileInput);

  el.addEventListener("click", () => {
    fileInput.click();
  });

  fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      // Remove o "+" e insere a imagem
      el.innerHTML = `<img src="${e.target.result}" style="width:100%; height:100%; object-fit:cover; border-radius:8px;">`;
    };
    reader.readAsDataURL(file);
  });
}

// Seleciona elementos
const cardPlaceholder = document.getElementById("add-popup-image");
const titlePlaceholder = document.getElementById("add-popup-title");

setupImageUpload(cardPlaceholder);
setupImageUpload(titlePlaceholder);

// ===========================
// Salvar mapa/história (corrigido fallback do título)
// ===========================
saveMapStoryBtn.addEventListener("click", async () => {
  const titleImgEl = titlePlaceholder.querySelector("img");
  const cardImgEl = cardPlaceholder.querySelector("img");

  if (!cardImgEl) {
    showQuickWarning("Selecione a imagem do card!", "darkorange");
    return;
  }

  // Se não houver imagem de título, usa o card como fallback
  if (!titleImgEl) {
    showQuickWarning(
      "Título não enviado, usando imagem do card como título.",
      "darkorange"
    );
    // Cria temporariamente uma referência à imagem do card
    const img = document.createElement("img");
    img.src = cardImgEl.src;
    img.file = cardImgEl.file;
    titlePlaceholder.innerHTML = "";
    titlePlaceholder.appendChild(img);
  }

  const finalTitleImgEl = titlePlaceholder.querySelector("img");

  const description = document
    .getElementById("add-popup-description")
    .value.trim();
  if (!description) {
    showQuickWarning("Preencha a descrição!", "darkorange");
    return;
  }

  const formData = new FormData();
  formData.append("description", description);
  formData.append("card_image", cardImgEl.file);
  formData.append("title_image", finalTitleImgEl.file);

  try {
    const res = await fetch("/admin/add_map_story", {
      method: "POST",
      body: formData,
    });

    const data = await res.json();
    if (data.success) {
      showQuickWarning("Mapa/História salvo com sucesso!", "darkgreen");
      addPopupOverlay.classList.remove("show");

      // Limpar popup
      document.getElementById("add-popup-description").value = "";
      cardPlaceholder.innerHTML =
        '<span>+</span><div class="tooltip">Inserir card</div>';
      titlePlaceholder.innerHTML =
        '<span>+</span><div class="tooltip">Inserir título</div>';
    } else {
      showQuickWarning("Erro ao salvar!", "red");
    }
  } catch (err) {
    console.error(err);
    showQuickWarning("Erro ao salvar!", "red");
  }
});

// ===========================
// Modifica o setupImageUpload para salvar referência ao file
// ===========================
function setupImageUpload(el) {
  const fileInput = document.createElement("input");
  fileInput.type = "file";
  fileInput.accept = "image/*";
  fileInput.style.display = "none";
  document.body.appendChild(fileInput);

  el.addEventListener("click", () => fileInput.click());

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
      img.file = file; // salva referência do File
      el.innerHTML = "";
      el.appendChild(img);
    };
    reader.readAsDataURL(file);
  });
}

document
  .querySelectorAll(".popup-image-placeholder, .popup-title")
  .forEach((el) => {
    const tooltip = el.querySelector(".tooltip");

    el.addEventListener("mouseenter", () => {
      tooltip.style.opacity = 1;
    });

    el.addEventListener("mouseleave", () => {
      tooltip.style.opacity = 0;
    });

    el.addEventListener("mousemove", (e) => {
      const rect = el.getBoundingClientRect();
      tooltip.style.left = `${rect.left + rect.width / 2}px`;
      tooltip.style.top = `${rect.top - 10}px`;
      tooltip.style.transform = "translate(-50%, -100%)";
    });
  });

// ===========================
// Função: Listar e remover cards
// ===========================
const cardsListContainer = document.getElementById("cards-list-container");

async function removerCards() {
  limparConteudoPrincipal();
  fecharSidebar();

  cardsListContainer.innerHTML = ""; // limpa antes

  try {
    const res = await fetch("/admin/list_cards");
    const cards = await res.json();

    if (!cards.length) {
      cardsListContainer.innerHTML = "<p>Nenhum card encontrado.</p>";
      return;
    }

    cards.forEach((card) => {
      const div = document.createElement("div");
      div.classList.add("remover-card");
      div.innerHTML = `
        <img src="/static/images/cards/${card.file}" alt="Card">
        <div class="trash-overlay">
            <span>&#128465;</span>
        </div>
      `;

      div.addEventListener("click", async () => {
        const confirmar = await showDeletePopup(card.title); // pode usar o título capitalizado do JSON
        if (confirmar) {
          const resp = await fetch(`/admin/delete_map_story/${card.file}`, {
            method: "DELETE",
          });
          const data = await resp.json();
          if (data.success) {
            div.remove();
            showQuickWarning(`Card ${data.card_name} removido!`, "darkred");
          } else {
            showQuickWarning(`Erro: ${data.error}`, "#e74c3c");
          }
        }
      });

      cardsListContainer.appendChild(div);
    });
  } catch (err) {
    console.error("Erro ao listar/remover cards:", err);
    showQuickWarning("Erro ao carregar cards!", "#e74c3c");
  }
}

const removerMapStoryItem = mapsSubmenu.querySelector("li:nth-child(2)"); // "Remover"

// Evento de clique - Remover Cards
removerMapStoryItem.addEventListener("click", removerCards);

// ===========================
// Inicialização: Página Carregada
// ===========================
window.addEventListener("DOMContentLoaded", () => {
  toggleSidebar(); // abre sidebar automaticamente na primeira vez
});
