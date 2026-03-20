/**
 * Sistema de formatação de texto
 * Símbolos:
 * - ** para negrito
 * - -- para itálico
 * - __ para sublinhado
 * - ~~ para riscado
 * - || para censurado
 */

function formatTextToHtml(text) {
  if (!text) return "";
  
  // Escapar HTML
  text = escapeHtml(text);
  
  // Aplicar formatações (ordem importa!)
  text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  text = text.replace(/--(.+?)--/g, '<em>$1</em>');
  text = text.replace(/__(.+?)__/g, '<u>$1</u>');
  text = text.replace(/~~(.+?)~~/g, '<s>$1</s>');
  text = text.replace(/\|\|(.+?)\|\|/g, '<span class="text-censored">$1</span>');
  
  return text;
}

function escapeHtml(text) {
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return text.replace(/[&<>"']/g, m => map[m]);
}

function createFormattingToolbar(textareaSelector) {
  const textarea = document.querySelector(textareaSelector);
  if (!textarea) {
    console.error(`Textarea não encontrado: ${textareaSelector}`);
    return;
  }

  // Verificar se já foi envolvido
  if (textarea.parentNode.classList.contains("textarea-with-toolbar")) {
    return; // Já foi processado
  }

  // Encontrar o container pai (pode ser uma div ou o parentNode direto)
  const parentContainer = textarea.parentNode;
  
  // Criar wrapper para posicionar a toolbar
  const wrapper = document.createElement("div");
  wrapper.className = "textarea-with-toolbar";

  // Mover o textarea para dentro do wrapper
  parentContainer.insertBefore(wrapper, textarea);
  wrapper.appendChild(textarea);

  // Criar toolbar
  const toolbar = document.createElement("div");
  toolbar.className = "formatting-toolbar";

  const buttons = [
    { letter: "N", symbol: "**", title: "Negrito: **texto**", html: "<strong>N</strong>" },
    { letter: "I", symbol: "--", title: "Itálico: --texto--", html: "<em>I</em>" },
    { letter: "S", symbol: "__", title: "Sublinhado: __texto__", html: "<u>S</u>" },
    { letter: "R", symbol: "~~", title: "Riscado: ~~texto~~", html: "<s>R</s>" },
    { letter: "C", symbol: "||", title: "Censurado: ||texto||", html: '<span class="text-censored" style="padding: 0 2px;">C</span>' },
  ];

  buttons.forEach(btn => {
    const button = document.createElement("button");
    button.type = "button";
    button.innerHTML = btn.html;
    button.title = btn.title;
    button.className = "fmt-btn";
    
    button.addEventListener("mouseover", () => {
      button.style.backgroundColor = "#2980b9";
    });
    button.addEventListener("mouseout", () => {
      button.style.backgroundColor = "#3498db";
    });
    button.addEventListener("click", (e) => {
      e.preventDefault();
      insertFormattingSymbols(textarea, btn.symbol);
    });
    toolbar.appendChild(button);
  });

  // Inserir toolbar DENTRO do wrapper, ANTES do textarea
  wrapper.insertBefore(toolbar, textarea);
}

function insertFormattingSymbols(textarea, symbol) {
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const text = textarea.value;
  
  let selectedText = text.substring(start, end);
  if (!selectedText) {
    selectedText = "texto";
  }

  const before = text.substring(0, start);
  const after = text.substring(end);
  
  textarea.value = before + symbol + selectedText + symbol + after;
  textarea.focus();
  
  // Atualizar seleção para o texto inserido
  const newStart = start + symbol.length;
  const newEnd = newStart + selectedText.length;
  textarea.setSelectionRange(newStart, newEnd);
}

function previewFormattedText(rawText, previewElementSelector) {
  const previewEl = document.querySelector(previewElementSelector);
  if (!previewEl) return;
  
  previewEl.innerHTML = formatTextToHtml(rawText);
}

// Exportar para uso global
window.TextFormatter = {
  formatTextToHtml,
  createFormattingToolbar,
  insertFormattingSymbols,
  previewFormattedText,
};
