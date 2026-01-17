# Amapá Zombies

Acesse o site oficial: [amapazombies.com.br](https://amapazombies.com.br)

---

## Sobre

**Amapá Zombies** é um site interativo dedicado a fãs de um projeto que une zumbis com o estado do Amapá. A plataforma oferece uma experiência imersiva com exploração de mapas e histórias, comentários da comunidade, sistema de avaliações e gerenciamento de conta com painel administrativo completo.

### Funcionalidades Principais

**Exploração de Conteúdo**
- Cards interativos de Mapas e Histórias com popups detalhados
- Imagens, títulos e descrições exclusivas acessíveis ao clicar
- Sistema de comentários integrado para comunidade
- Avaliações por estrelas para cada card
- Sistema de "likes" para conteúdo favorito
- Suporte a parceiros com perfis e redes sociais

**Interface e Experiência do Usuário**
- Fundo com slideshow dinâmico e aleatório
- Popups com efeito fade-in e transições suaves
- Notificações visuais para feedback de ações
- Design responsivo e otimizado para mobile, tablet e desktop
- Animações CSS fluidas e envolventes

**Autenticação e Segurança**
- Sistema completo de registro e login
- Validação em tempo real de nome de usuário, email e senha
- Criptografia de dados sensíveis com Fernet (cryptography)
- Verificação de sessão e autenticação de usuário
- Suporte a múltiplas funções (usuário comum e administrador)
- Sistema de recuperação de senha por email

**Painel Administrativo**
- Gerenciamento de usuários (promoção e degradação de permissões)
- Gerenciamento de cards (criar, editar, deletar, controlar visibilidade)
- Gerenciamento de links para histórias e mapas
- Upload de imagens para cards e títulos
- Controle de status do site
- Visualização de comentários e avaliações
- Sinalizador "NOVO" que expira automaticamente após 7 dias

**Funcionalidades de Email**
- Sistema de recuperação de senha com tokens de 1 hora
- Emails HTML estilizados e responsivos
- Configuração dinâmica via credenciais SMTP
- Integração com Gmail SMTP

---

## Tecnologias

### Backend
- **Framework:** Flask (Python)
- **Renderização:** Jinja2
- **Autenticação:** Sessões Flask com criptografia Fernet
- **Criptografia:** cryptography (Fernet para dados sensíveis)
- **Email:** smtplib com Gmail SMTP
- **Servidor de Produção:** Werkzeug (desenvolvimento)

### Frontend
- **Marcação:** HTML5
- **Estilização:** CSS3 com animações
- **Interatividade:** JavaScript (ES6+)
- **Requisições:** Fetch API (AJAX)
- **Tipografia:** Google Fonts
- **Responsividade:** Mobile-first design

### Estrutura de Dados
- **Armazenamento:** JSON (arquivos)
- **Gerenciamento:** Python (leitura/escrita com encoding UTF-8)

---

## Estrutura do Projeto

```
apzm.site/
├── main.py                 # Aplicação principal e configuração Flask
├── requirements.txt        # Dependências do projeto
├── README.md              # Este arquivo
│
├── routes/                # Blueprints e rotas da aplicação
│   ├── __init__.py        # Registro de blueprints
│   ├── home.py            # Rotas de página inicial e conteúdo
│   ├── auth.py            # Rotas de logout
│   ├── register.py        # Rotas de login, registro e gestão de usuários
│   ├── admin.py           # Rotas administrativas
│   └── email.py           # Rotas de email e recuperação de senha
│
├── tools/                 # Utilitários e funções auxiliares
│   ├── crypto_utils.py    # Criptografia de dados (Fernet)
│   ├── decorators.py      # Decoradores para autenticação e permissões
│   ├── users_manip.py     # Manipulação de dados de usuário
│   └── secret_key.py      # Geração e gerenciamento de chaves secretas
│
├── templates/             # Templates Jinja2
│   ├── home.html          # Página principal
│   ├── admin.html         # Painel administrativo
│   ├── off.html           # Página de manutenção/offline
│   ├── session_denied.html # Página de acesso negado
│   └── sitemap.xml        # Sitemap para SEO
│
├── static/                # Arquivos estáticos
│   ├── robots.txt         # Configuração de crawlers
│   ├── css/
│   │   ├── home.css       # Estilos da página inicial
│   │   └── admin.css      # Estilos do painel administrativo
│   ├── js/
│   │   ├── home.js        # Scripts da página inicial
│   │   └── admin.js       # Scripts do painel administrativo
│   └── images/
│       ├── background/    # Imagens de fundo (slideshow)
│       ├── cards/         # Imagens dos cards
│       ├── titles/        # Imagens dos títulos
│       ├── common/        # Imagens comuns
│       └── parceiros/     # Imagens de parceiros
│           ├── logo/      # Logos dos parceiros
│           └── background/ # Backgrounds dos parceiros
│
└── data/                  # Arquivos de dados (JSON)
    ├── cards.json         # Dados dos cards (mapas/histórias)
    ├── comments.json      # Comentários da comunidade
    ├── likes.json         # Dados de "likes"
    ├── ratings.json       # Avaliações por estrelas
    ├── links.json         # Links para histórias e mapas
    ├── parceiros.json     # Dados dos parceiros
    ├── users.json         # Dados dos usuários (criptografado)
    ├── site_status.json   # Status do site
    ├── fernet.key         # Chave de criptografia (gerada automaticamente)
    └── email_creds.key    # Credenciais SMTP (EMAIL e PW_APP)
```

---

## Instalação e Configuração

### Pré-requisitos
- Python 3.8+
- pip (gerenciador de pacotes Python)

### Passos de Instalação

1. **Clone o repositório:**
   ```bash
   git clone <url-do-repositorio>
   cd apzm.site
   ```

2. **Crie um ambiente virtual (recomendado):**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/macOS
   source venv/bin/activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure as credenciais de email (opcional):**
   - Edite `data/email_creds.key`
   - Preencha com seu email Gmail e senha de aplicativo
   - Formato: `EMAIL=seu_email@gmail.com` e `PW_APP=sua_senha_app`

5. **Inicie a aplicação:**
   ```bash
   python main.py
   ```

6. **Acesse no navegador:**
   ```
   http://localhost:5000
   ```

---

## Dependências

As seguintes bibliotecas Python são necessárias:

- **cryptography**: Criptografia Fernet para dados sensíveis
- **Flask**: Framework web
- **Werkzeug**: Utilidades para WSGI e segurança

Instale todas com:
```bash
pip install -r requirements.txt
```

---

## Uso

### Página Principal
- Visualize cards interativos de mapas e histórias
- Clique nos cards para abrir popups com mais detalhes
- Comente em cada card (requer login)
- Avalie cards com sistema de estrelas
- "Curta" cards favoritos
- Explore parceiros e suas redes sociais

### Login e Registro
- Crie uma conta fornecendo nome de usuário, email e senha
- Faça login com suas credenciais
- Recupere sua senha usando o email cadastrado

### Painel Administrativo
- Acesso apenas para usuários com permissão de admin
- Gerencie cards: crie, edite, delete e controle visibilidade
- Gerencie usuários: promova, degrade ou delete contas
- Visualize comentários e avaliações
- Gerencie links para histórias e mapas
- Upload de imagens para cards

---

## Segurança

- Senhas são criptografadas usando Fernet antes de serem armazenadas
- Emails são criptografados no banco de dados
- Sessões são validadas a cada requisição
- Tokens de recuperação de senha expiram em 1 hora
- CORS e validações de entrada implementadas
- Decoradores protegem rotas administrativas

---

## Avisos Legais

- Todo o conteúdo (textos, imagens, lore, código) é propriedade exclusiva do Amapá Zombies
- Não copie, distribua ou reutilize sem permissão explícita
- O uso não autorizado de conteúdo resultará em ações legais

---

## Redes Sociais

Acompanhe Amapá Zombies nas redes sociais:

- Instagram: [@amapazombies](https://instagram.com/amapazombies)
- X (Twitter): [@amapazombies](https://x.com/amapazombies)
- Wattpad: [AmapaZombies](https://wattpad.com/user/AmapaZombies)

---

## Suporte

Para dúvidas, reportar problemas ou sugestões, entre em contato através das redes sociais ou envie um email para suporte@amapazombies.com.br

---