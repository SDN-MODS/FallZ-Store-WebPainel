# 🎮 Loja DayZ — Bot Discord + Painel Web Administrativo em Python

Sistema completo e integrado de loja para servidores de DayZ baseado no modelo de **Coins** (moeda virtual interna).

---

## 💡 Regra Central da Economia

```text
Dinheiro Real (R$) ➔ Coins ➔ Produtos na Loja
```

1. **Moeda Virtual:** O jogador compra pacotes de **Coins** com dinheiro real.
2. **Saldo Instantâneo:** As Coins entram imediatamente no saldo do jogador.
3. **Loja do Discord:** O jogador navega pelas categorias no Bot usando botões e menus suspensos (sem comandos de texto), escolhe os produtos ou kits e confirma a compra.
4. **Desconto Automático:** As Coins são abatidas e o pedido é criado com status `🟡 Aguardando processamento`.
5. **Entrega Administrativa:** A equipe administra as entregas pelo **Painel Web** e altera o status para `🟢 Entregue`.

---

## 🚀 Como Enviar a Loja para o Discord em 3 Passos (Pelo Painel Web)

Desenvolvemos uma forma **100% prática e direta pelo Painel Web** para você enviar e publicar o painel da loja no seu canal do Discord com apenas **1 clique**:

1. **Acesse as Configurações no Painel Web:**
   - Abra [http://localhost:5000/settings](http://localhost:5000/settings).
2. **Preencha as Credenciais do Discord:**
   - **ID do Cliente do Bot:** Cole o *Application Client ID* do seu bot.
   - **Token do Bot:** Cole o *Bot Token* (Discord Developer Portal ➔ Bot ➔ Reset Token).
   - **ID do Canal da Loja:** Cole o ID do canal do Discord onde a loja deve aparecer (clique com botão direito no canal no Discord ➔ *Copiar ID do Canal*).
   - Clique em **Salvar Configurações**.
3. **Clique no Botão de Publicação Instantânea:**
   - Clique no botão azul **"🚀 Publicar Painel da Loja no Discord"**.
   - A loja com a mensagem de boas-vindas, logo, saldo e todos os **botões interativos (`🛒 Loja`, `🪙 Comprar Coins`, `💰 Meu Saldo`, `📦 Meus Pedidos`, `🎁 Cupons`, `🎫 Suporte`)** aparecerá fixada imediatamente no seu canal do Discord!

---

## 🛠️ Requisitos e Instalação

- **Python 3.10 ou superior**
- **Pip e Git**

### Instalar Dependências

```bash
pip install -r requirements.txt
```

---

## 🧪 Como Executar os Testes Automatizados

O sistema possui uma suíte completa de testes de integração cobrindo:
- Compra de Coins e acréscimo de saldo.
- Compra de produtos com Coins e abatimento do saldo.
- Impedimento de compra quando o saldo em Coins é insuficiente.
- Edição de pacotes de coins e upload de imagem.
- Parser do `types.xml` do DayZ e cadastro de Kits com múltiplos itens (validade e uso único).
- Envio do painel da loja via API REST do Discord.

Para executar os testes, rode no terminal:

```bash
PYTHONPATH=. pytest -v
```

---

## 🗄️ Inicialização do Banco de Dados

Para gerar as tabelas no banco SQLite e popular dados iniciais de demonstração (pacotes de coins, categorias de armas, equipamentos e veículos, produtos e cupons):

```bash
python -m database.seed
```

---

## 🌐 Como Subir o Painel Web Administrativo

```bash
PYTHONPATH=. python web/app.py
```

Acesse no seu navegador:
👉 **[http://localhost:5000](http://localhost:5000)**

---

## 🤖 Como Manter o Bot Online para Interações Continuas

Após enviar o painel da loja pelo painel web, para que os botões respondam quando os jogadores clicarem, mantenha o processo do Bot rodando no terminal:

```bash
python -m bot.main
```
