// ===========================
// Elementos do DOM
// ===========================
const hamburger = document.getElementById('hamburger');
const sidebar = document.getElementById('sidebar');
const mapsItem = document.getElementById('maps-stories');
const mapsSubmenu = document.getElementById('maps-submenu');

// ===========================
// Função: Abrir/Fechar Sidebar
// ===========================
function toggleSidebar() {
    sidebar.classList.toggle('active');

    if (sidebar.classList.contains('active')) {
        // Sidebar aberto: muda hambúrguer para X branco
        hamburger.innerHTML = '✖';
        hamburger.style.color = 'white';
    } else {
        // Sidebar fechado: volta para hambúrguer
        hamburger.innerHTML = '&#9776;';
        hamburger.style.color = 'darkgreen';
    }
}

// ===========================
// Função: Toggle Submenu Mapas/Historias
// ===========================
function toggleMapsSubmenu() {
    const isVisible = mapsSubmenu.style.display === 'block';
    mapsSubmenu.style.display = isVisible ? 'none' : 'block';
    mapsItem.classList.toggle('open');
}

// ===========================
// Evento: Clique no Hambúrguer
// ===========================
hamburger.addEventListener('click', toggleSidebar);

// ===========================
// Evento: Clique na aba Mapas/Historias
// ===========================
mapsItem.addEventListener('click', toggleMapsSubmenu);

// ===========================
// Inicialização: Página Carregada
// ===========================
window.addEventListener('DOMContentLoaded', () => {
    // Abre sidebar automaticamente na primeira vez
    toggleSidebar();

    // OBS: não abrir submenus automaticamente
});
