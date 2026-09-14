# 🎮 Loja DayZ — Bot Discord + Painel Web Administrativo em Python

Sistema completo de loja para servidores de DayZ baseado em **Coins** (moeda virtual interna).

---

## 💡 Fluxo Central da Economia

```text
Dinheiro Real (R$) ➔ Coins ➔ Produtos na Loja
```

1. O jogador compra pacotes de **Coins** com dinheiro real.
2. As Coins são creditadas automaticamente no saldo do jogador.
3. O jogador navega pela loja no Discord e compra itens/veículos utilizando seu saldo de Coins.
4. O valor é descontado e um pedido é criado com status **🟡 Aguardando processamento**.
5. A administração processa a entrega pelo **Painel Web** e altera o status para **🟢 Entregue**.

---

## 🚀 Requisitos e Instalação

### Requisitos:
- Python 3.10 ou superior
- Pip e Git

### Instalação das Dependências:

```bash
pip install -r requirements.txt
```

---

## 🗄️ Inicialização do Banco de Dados

Para criar a estrutura de tabelas SQLite e semear dados de demonstração (pacotes de coins, categorias de armas/equipamentos/veículos, produtos e cupons), execute:

```bash
python -m database.seed
```

---

## 🌐 Como Executar o Painel Web Administrativo

O painel web permite administrar faturamento, pacotes de coins, ajuste manual de saldo, cadastro de produtos, gerenciamento de pedidos, cupons promocionais e logs de auditoria.

Execute o comando:

```bash
PYTHONPATH=. python web/app.py
```

Acesse no navegador:
👉 **[http://localhost:5000](http://localhost:5000)**

---

## 🤖 Como Executar o Bot de Discord

1. Crie uma aplicação no [Discord Developer Portal](https://discord.com/developers/applications).
2. Obtenha o **Token do Bot** e ative a **Message Content Intent**.
3. Crie um arquivo `.env` na raiz do projeto contendo:

```env
DISCORD_BOT_TOKEN=SEU_TOKEN_AQUI
FLASK_SECRET_KEY=sua_chave_secreta
```

4. Execute o bot:

```bash
python -m bot.main
```

---

## 🧪 Executando os Testes Automatizados

Para rodar todos os testes de integração do fluxo econômico:

```bash
PYTHONPATH=. pytest -v
```
