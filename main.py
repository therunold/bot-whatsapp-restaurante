"""
Bot de Atendimento para Restaurante - WhatsApp Cloud API
==========================================================
Bot completo para atendimento automatizado via WhatsApp oficial (Meta)
com fluxo de pedidos, cardápio interativo e confirmação.
"""

from flask import Flask, request, jsonify
import requests
import json
from datetime import datetime

app = Flask(__name__)


WHATSAPP_TOKEN = "EAAVHW48h15wBQH0Li9FYYp08reUZAXeKNbBDgctJQkBP99gdobO1ZBPjwWJrfPOPw0lnMXPYUOxVWksk2ZA0fMB9ZAaCSEXUZAxOYaqDO5C2YPUMjRwz0gpbqA4uQv7VmbfGgtoCJCLijLNlvENwDSYJB8ewIGUNtYIKUhX008gZAtO22mewCLs2a5WOSiYe0otClAYMeiQDwBhgZBzqWEFY5ZCA23wM9vL02vBWRXrRIDRsI23YZCSshsaktuKQU0hb3U5n6V7QPDPk0XQ3A6oPhDRJy"
PHONE_NUMBER_ID = "1555027735"
VERIFY_TOKEN = "1020"
WHATSAPP_API_URL = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"


CARDAPIO = {
    "lanches": [
        {"id": "1", "nome": "X-Burger", "preco": 14.90},
        {"id": "2", "nome": "X-Bacon", "preco": 16.90},
        {"id": "3", "nome": "X-Tudo", "preco": 19.90},
        {"id": "4", "nome": "X-Salada", "preco": 15.90}
    ],
    "acompanhamentos": [
        {"id": "5", "nome": "Batata Frita", "preco": 9.90},
        {"id": "6", "nome": "Onion Rings", "preco": 11.90},
        {"id": "7", "nome": "Nuggets", "preco": 12.90}
    ],
    "bebidas": [
        {"id": "8", "nome": "Refrigerante Lata", "preco": 6.00},
        {"id": "9", "nome": "Suco Natural", "preco": 8.00},
        {"id": "10", "nome": "Água Mineral", "preco": 4.00}
    ]
}


usuarios = {}


class Usuario:
    """Classe para gerenciar o estado de cada usuário"""
    def __init__(self, telefone):
        self.telefone = telefone
        self.nome = None
        self.estado = "INICIO"
        self.pedido = []
        self.categoria_atual = None
        self.item_temporario = None
        self.total = 0.0

    def resetar_pedido(self):
        """Reseta o pedido atual"""
        self.pedido = []
        self.total = 0.0
        self.item_temporario = None


def obter_usuario(telefone):
    """Obtém ou cria um usuário no sistema"""
    if telefone not in usuarios:
        usuarios[telefone] = Usuario(telefone)
    return usuarios[telefone]


def enviar_mensagem(telefone, mensagem):
    """Envia mensagem de texto simples para o WhatsApp"""
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": telefone,
        "type": "text",
        "text": {"body": mensagem}
    }

    try:
        response = requests.post(WHATSAPP_API_URL, headers=headers, json=payload)
        return response.json()
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")
        return None


def enviar_botoes(telefone, mensagem, botoes):
    """
    Envia mensagem com botões interativos
    botoes: lista de dicts com 'id' e 'title'
    Exemplo: [{"id": "btn1", "title": "Opção 1"}]
    """
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    buttons_formatted = []
    for botao in botoes[:3]:
        buttons_formatted.append({
            "type": "reply",
            "reply": {
                "id": botao["id"],
                "title": botao["title"]
            }
        })

    payload = {
        "messaging_product": "whatsapp",
        "to": telefone,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": mensagem},
            "action": {
                "buttons": buttons_formatted
            }
        }
    }

    try:
        response = requests.post(WHATSAPP_API_URL, headers=headers, json=payload)
        return response.json()
    except Exception as e:
        print(f"Erro ao enviar botões: {e}")
        return None


def enviar_lista(telefone, mensagem, titulo_botao, secoes):
    """
    Envia mensagem com lista interativa
    secoes: lista de dicts com 'title' e 'rows'
    """
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": telefone,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": mensagem},
            "action": {
                "button": titulo_botao,
                "sections": secoes
            }
        }
    }

    try:
        response = requests.post(WHATSAPP_API_URL, headers=headers, json=payload)
        return response.json()
    except Exception as e:
        print(f"Erro ao enviar lista: {e}")
        return None


def formatar_cardapio():
    """Formata o cardápio completo em texto"""
    texto = "📋 *CARDÁPIO RESTAURANTE* 📋\n\n"

    texto += "🍔 *LANCHES*\n"
    for item in CARDAPIO["lanches"]:
        texto += f"  • {item['nome']} — R$ {item['preco']:.2f}\n"

    texto += "\n🍟 *ACOMPANHAMENTOS*\n"
    for item in CARDAPIO["acompanhamentos"]:
        texto += f"  • {item['nome']} — R$ {item['preco']:.2f}\n"

    texto += "\n🥤 *BEBIDAS*\n"
    for item in CARDAPIO["bebidas"]:
        texto += f"  • {item['nome']} — R$ {item['preco']:.2f}\n"

    return texto


def boas_vindas(usuario):
    """Envia mensagem de boas-vindas e solicita o nome"""
    mensagem = "Olá! 👋 Seja bem-vindo ao *Restaurante Sabor & Companhia*!\n\nPara começar, qual é o seu *nome*?"
    enviar_mensagem(usuario.telefone, mensagem)
    usuario.estado = "AGUARDANDO_NOME"


def menu_principal(usuario):
    """Envia menu principal com botões"""
    mensagem = f"Prazer, *{usuario.nome}*! 😊\n\nO que você gostaria de fazer?"

    botoes = [
        {"id": "ver_cardapio", "title": "📋 Ver Cardápio"},
        {"id": "fazer_pedido", "title": "🛒 Fazer Pedido"},
        {"id": "falar_atendente", "title": "👤 Atendente"}
    ]

    enviar_botoes(usuario.telefone, mensagem, botoes)
    usuario.estado = "MENU_PRINCIPAL"


def mostrar_cardapio(usuario):
    """Mostra o cardápio completo"""
    cardapio_texto = formatar_cardapio()
    enviar_mensagem(usuario.telefone, cardapio_texto)

    mensagem = "\nO que deseja fazer agora?"
    botoes = [
        {"id": "fazer_pedido", "title": "🛒 Fazer Pedido"},
        {"id": "voltar_menu", "title": "⬅️ Voltar"}
    ]
    enviar_botoes(usuario.telefone, mensagem, botoes)


def iniciar_pedido(usuario):
    """Inicia o fluxo de pedido com categorias"""
    usuario.resetar_pedido()

    mensagem = "🛒 *FAZER PEDIDO*\n\nEscolha uma categoria para começar:"

    botoes = [
        {"id": "cat_lanches", "title": "🍔 Lanches"},
        {"id": "cat_acompanhamentos", "title": "🍟 Acompanhamentos"},
        {"id": "cat_bebidas", "title": "🥤 Bebidas"}
    ]

    enviar_botoes(usuario.telefone, mensagem, botoes)
    usuario.estado = "ESCOLHENDO_CATEGORIA"


def mostrar_itens_categoria(usuario, categoria):
    """Mostra os itens de uma categoria específica"""
    usuario.categoria_atual = categoria

    categorias_nome = {
        "lanches": "🍔 Lanches",
        "acompanhamentos": "🍟 Acompanhamentos",
        "bebidas": "🥤 Bebidas"
    }

    mensagem = f"*{categorias_nome[categoria]}*\n\nEscolha um item:"

    rows = []
    for item in CARDAPIO[categoria]:
        rows.append({
            "id": f"item_{item['id']}",
            "title": item['nome'],
            "description": f"R$ {item['preco']:.2f}"
        })

    secoes = [{"title": categorias_nome[categoria], "rows": rows}]

    enviar_lista(usuario.telefone, mensagem, "Ver Itens", secoes)
    usuario.estado = "ESCOLHENDO_ITEM"


def obter_item_por_id(item_id):
    """Busca um item no cardápio pelo ID"""
    for categoria in CARDAPIO.values():
        for item in categoria:
            if item['id'] == item_id:
                return item
    return None


def solicitar_quantidade(usuario, item_id):
    """Solicita a quantidade do item escolhido"""
    item = obter_item_por_id(item_id)

    if item:
        usuario.item_temporario = item
        mensagem = f"Você escolheu: *{item['nome']}* (R$ {item['preco']:.2f})\n\nQuantas unidades deseja?"
        enviar_mensagem(usuario.telefone, mensagem)
        usuario.estado = "AGUARDANDO_QUANTIDADE"
    else:
        enviar_mensagem(usuario.telefone, "Desculpe, item não encontrado. Tente novamente.")


def adicionar_ao_pedido(usuario, quantidade):
    """Adiciona item ao pedido com a quantidade especificada"""
    if usuario.item_temporario:
        item = usuario.item_temporario
        subtotal = item['preco'] * quantidade

        usuario.pedido.append({
            "nome": item['nome'],
            "preco": item['preco'],
            "quantidade": quantidade,
            "subtotal": subtotal
        })

        usuario.total += subtotal

        resumo = f"✅ *{quantidade}x {item['nome']}* adicionado!\n"
        resumo += f"Subtotal: R$ {subtotal:.2f}\n\n"
        resumo += f"Total do pedido: R$ {usuario.total:.2f}\n\n"
        resumo += "O que deseja fazer?"

        botoes = [
            {"id": "finalizar_pedido", "title": "✅ Finalizar"},
            {"id": "adicionar_mais", "title": "➕ Adicionar Mais"},
            {"id": "cancelar_pedido", "title": "❌ Cancelar"}
        ]

        enviar_botoes(usuario.telefone, resumo, botoes)
        usuario.estado = "PEDIDO_EM_ANDAMENTO"
        usuario.item_temporario = None


def mostrar_resumo_pedido(usuario):
    """Mostra o resumo completo do pedido"""
    if not usuario.pedido:
        enviar_mensagem(usuario.telefone, "Seu pedido está vazio.")
        return

    resumo = "🧾 *RESUMO DO PEDIDO*\n\n"

    for item in usuario.pedido:
        resumo += f"{item['quantidade']}x {item['nome']}\n"
        resumo += f"   R$ {item['preco']:.2f} x {item['quantidade']} = R$ {item['subtotal']:.2f}\n\n"

    resumo += f"━━━━━━━━━━━━━━━━\n"
    resumo += f"*TOTAL: R$ {usuario.total:.2f}*"

    enviar_mensagem(usuario.telefone, resumo)


def finalizar_pedido(usuario):
    """Finaliza o pedido e envia confirmação"""
    mostrar_resumo_pedido(usuario)

    confirmacao = f"\n🎉 *PEDIDO CONFIRMADO!*\n\n"
    confirmacao += f"Olá {usuario.nome}, seu pedido foi registrado com sucesso!\n\n"
    confirmacao += f"⏰ *Tempo estimado:* 25–35 minutos\n"
    confirmacao += f"💰 *Total:* R$ {usuario.total:.2f}\n\n"
    confirmacao += f"Obrigado por pedir conosco! 😊"

    enviar_mensagem(usuario.telefone, confirmacao)

    usuario.resetar_pedido()
    usuario.estado = "PEDIDO_FINALIZADO"

    mensagem = "\nDeseja fazer outro pedido?"
    botoes = [
        {"id": "fazer_pedido", "title": "🛒 Novo Pedido"},
        {"id": "voltar_menu", "title": "⬅️ Menu Principal"}
    ]
    enviar_botoes(usuario.telefone, mensagem, botoes)


def processar_mensagem(telefone, mensagem, tipo_mensagem="text", button_id=None):
    """Processa mensagens recebidas e gerencia o fluxo da conversa"""
    usuario = obter_usuario(telefone)

    print(f"[{datetime.now()}] Estado atual de {telefone}: {usuario.estado}")
    print(f"Mensagem recebida: {mensagem} | Tipo: {tipo_mensagem} | Button: {button_id}")

    if usuario.estado == "INICIO":
        boas_vindas(usuario)

    elif usuario.estado == "AGUARDANDO_NOME":
        usuario.nome = mensagem.strip()
        menu_principal(usuario)

    elif usuario.estado == "MENU_PRINCIPAL":
        if button_id == "ver_cardapio":
            mostrar_cardapio(usuario)
        elif button_id == "fazer_pedido":
            iniciar_pedido(usuario)
        elif button_id == "falar_atendente":
            enviar_mensagem(telefone, "Aguarde, você será transferido para um atendente em breve. ⏳")

    elif usuario.estado == "ESCOLHENDO_CATEGORIA":
        if button_id == "cat_lanches":
            mostrar_itens_categoria(usuario, "lanches")
        elif button_id == "cat_acompanhamentos":
            mostrar_itens_categoria(usuario, "acompanhamentos")
        elif button_id == "cat_bebidas":
            mostrar_itens_categoria(usuario, "bebidas")

    elif usuario.estado == "ESCOLHENDO_ITEM":
        if button_id and button_id.startswith("item_"):
            item_id = button_id.replace("item_", "")
            solicitar_quantidade(usuario, item_id)

    elif usuario.estado == "AGUARDANDO_QUANTIDADE":
        try:
            quantidade = int(mensagem.strip())
            if quantidade > 0:
                adicionar_ao_pedido(usuario, quantidade)
            else:
                enviar_mensagem(telefone, "Por favor, envie um número válido maior que zero.")
        except ValueError:
            enviar_mensagem(telefone, "Por favor, envie apenas números para a quantidade.")

    elif usuario.estado == "PEDIDO_EM_ANDAMENTO":
        if button_id == "finalizar_pedido":
            finalizar_pedido(usuario)
        elif button_id == "adicionar_mais":
            iniciar_pedido(usuario)
        elif button_id == "cancelar_pedido":
            usuario.resetar_pedido()
            enviar_mensagem(telefone, "❌ Pedido cancelado.")
            menu_principal(usuario)

    elif button_id == "voltar_menu" or button_id == "fazer_pedido":
        if button_id == "fazer_pedido":
            iniciar_pedido(usuario)
        else:
            menu_principal(usuario)


@app.route("/webhook", methods=["GET"])
def webhook_verify():
    """Verificação do webhook (Meta requer isso)"""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("Webhook verificado com sucesso!")
        return challenge, 200
    else:
        return "Verificação falhou", 403


@app.route("/webhook", methods=["POST"])
def webhook_receive():
    """Recebe mensagens do WhatsApp via webhook"""
    try:
        data = request.get_json()

        print("Webhook recebido:")
        print(json.dumps(data, indent=2))

        if data.get("object") == "whatsapp_business_account":
            entries = data.get("entry", [])

            for entry in entries:
                changes = entry.get("changes", [])

                for change in changes:
                    value = change.get("value", {})
                    messages = value.get("messages", [])

                    for message in messages:
                        telefone = message.get("from")
                        tipo = message.get("type")

                        mensagem_texto = None
                        button_id = None

                        if tipo == "text":
                            mensagem_texto = message.get("text", {}).get("body", "")

                        elif tipo == "interactive":
                            interactive = message.get("interactive", {})

                            if interactive.get("type") == "button_reply":
                                button_id = interactive.get("button_reply", {}).get("id")
                                mensagem_texto = interactive.get("button_reply", {}).get("title")

                            elif interactive.get("type") == "list_reply":
                                button_id = interactive.get("list_reply", {}).get("id")
                                mensagem_texto = interactive.get("list_reply", {}).get("title")

                        if telefone:
                            processar_mensagem(telefone, mensagem_texto, tipo, button_id)

        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"Erro no webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/", methods=["GET"])
def home():
    """Rota inicial para verificar se a API está funcionando"""
    return jsonify({
        "status": "online",
        "service": "Bot de Atendimento para Restaurante",
        "platform": "WhatsApp Cloud API",
        "version": "1.0.0"
    }), 200


if __name__ == "__main__":
    print("=" * 50)
    print("🤖 BOT DE ATENDIMENTO - RESTAURANTE")
    print("=" * 50)
    print("Plataforma: WhatsApp Cloud API (Meta)")
    print("Status: Iniciando servidor...")
    print("=" * 50)

    app.run(debug=True, host="0.0.0.0", port=5000)
