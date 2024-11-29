import random  # Para realizar o sorteio de maneira aleatória
import os  # Para manipulação de variáveis de ambiente
import sqlite3  # Para interagir com o banco de dados SQLite
from dotenv import load_dotenv  # Para carregar variáveis de ambiente de um arquivo .env
from telegram import Update  # Para trabalhar com objetos de atualização do Telegram
from telegram.ext import Application, CommandHandler, ContextTypes  # Para gerenciar comandos e contexto no bot do Telegram

# Carregar variáveis de ambiente do arquivo .env (geralmente para o token do bot)
load_dotenv()

# Variável para armazenar o token do bot Telegram (obtido do @BotFather)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Função para conectar ao banco de dados SQLite e criar a tabela de participantes, se ainda não existir
def conectar_banco():
    conn = sqlite3.connect('amigo_secreto.db')  # Conectar ao banco de dados SQLite
    cursor = conn.cursor()  # Criar um cursor para interagir com o banco
    cursor.execute('''  # Criar a tabela 'participantes', caso ela não exista
        CREATE TABLE IF NOT EXISTS participantes (
            id INTEGER PRIMARY KEY,  # ID único para cada participante
            chat_id INTEGER,  # ID do chat do Telegram onde o participante está
            nome TEXT,  # Nome do participante
            UNIQUE(chat_id, nome)  # Garantir que um participante não possa ser adicionado mais de uma vez
        )
    ''')
    conn.commit()  # Confirmar a criação da tabela
    return conn, cursor  # Retornar a conexão e o cursor

# Função para adicionar um participante ao sorteio
async def adicionar_participante(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Extração do ID do usuário e nome completo
    usuario_id = update.message.from_user.id
    nome = update.message.from_user.first_name
    sobrenome = update.message.from_user.last_name or ""  # Sobrenome é opcional
    nome_completo = f"{nome} {sobrenome}".strip()  # Combina nome e sobrenome
    chat_id = update.effective_chat.id  # ID do chat onde a mensagem foi enviada

    # Conectar ao banco de dados SQLite
    conn, cursor = conectar_banco()

    # Verificar se o participante já existe no banco de dados
    cursor.execute("SELECT * FROM participantes WHERE chat_id = ? AND nome = ?", (chat_id, nome))
    participante_existente = cursor.fetchone()

    if participante_existente:
        await update.message.reply_text(f"Você já está no sorteio, {nome}.")
        conn.close()  # Fechar a conexão com o banco de dados
        return

    # Caso o participante não exista, adicionamos ele ao banco de dados
    try:
        cursor.execute("INSERT INTO participantes (chat_id, nome) VALUES (?, ?)", (chat_id, nome_completo))
        conn.commit()  # Confirmar a inserção no banco
        await update.message.reply_text(f"Adicionado ao sorteio como {nome_completo}.")
    except sqlite3.IntegrityError:
        # Em caso de erro de integridade, como se o participante já tivesse sido adicionado
        await update.message.reply_text(f"Você já está no sorteio, {nome}.")

    conn.close()  # Fechar a conexão com o banco de dados

# Função para remover um participante do sorteio
async def remover_participante(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id  # ID do chat onde a mensagem foi enviada

    # Conectar ao banco de dados SQLite
    conn, cursor = conectar_banco()

    # Remover o participante do banco de dados
    cursor.execute("DELETE FROM participantes WHERE chat_id = ? AND nome = ?", (chat_id, update.message.from_user.first_name))
    conn.commit()

    if cursor.rowcount > 0:
        await update.message.reply_text(f"Você foi removido do sorteio.")
    else:
        await update.message.reply_text("Você não está no sorteio.")

    conn.close()  # Fechar a conexão com o banco de dados

# Função para listar todos os participantes do sorteio
async def listar_participantes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id  # ID do chat onde a mensagem foi enviada

    # Conectar ao banco de dados SQLite
    conn, cursor = conectar_banco()

    # Consultar todos os participantes do banco de dados
    cursor.execute("SELECT nome FROM participantes WHERE chat_id = ?", (chat_id,))
    participantes = cursor.fetchall()  # Retornar todos os resultados da consulta

    if participantes:
        nomes = [p[0] for p in participantes]  # Extrair apenas os nomes dos participantes
        await update.message.reply_text("Participantes atuais: " + ", ".join(nomes))  # Exibir os nomes
    else:
        await update.message.reply_text("Não há participantes no sorteio ainda.")

    conn.close()  # Fechar a conexão com o banco de dados

# Função para realizar o sorteio e atribuir amigos secretos
async def sorteio_amigo_secreto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id  # ID do chat onde a mensagem foi enviada

    # Conectar ao banco de dados SQLite
    conn, cursor = conectar_banco()

    # Consultar todos os participantes
    cursor.execute("SELECT id, nome FROM participantes WHERE chat_id = ?", (chat_id,))
    participantes = cursor.fetchall()  # Retornar todos os participantes do sorteio

    if len(participantes) < 2:  # Verificar se há pelo menos 2 participantes
        await update.message.reply_text("É necessário pelo menos 2 participantes para realizar o sorteio.")
        conn.close()
        return

    # Embaralhar a lista de participantes
    sorteio = participantes[:]
    random.shuffle(sorteio)

    amigos_secretos = {}  # Dicionário para armazenar os amigos secretos
    for i in range(len(participantes)):
        # Garantir que o participante não tire a si mesmo
        while sorteio[i][0] == participantes[i][0]:
            random.shuffle(sorteio)

        amigos_secretos[participantes[i][0]] = sorteio[i][1]  # Atribuir o amigo secreto

    # Enviar a mensagem para cada participante com seu amigo secreto
    for participante in participantes:
        amigo = amigos_secretos[participante[0]]
        await context.bot.send_message(chat_id=participante[0], text=f"Seu amigo secreto é: {amigo}")

    await update.message.reply_text("O sorteio foi realizado com sucesso!")

    conn.close()  # Fechar a conexão com o banco de dados

# Função principal que configura o bot
def main():
    if TELEGRAM_TOKEN is None:  # Verificar se o token do bot foi configurado corretamente
        print("Erro: TELEGRAM_TOKEN não configurado no arquivo .env")
        return

    # Inicializar o bot com o token
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Adicionar manipuladores de comandos
    application.add_handler(CommandHandler("iniciar", sorteio_amigo_secreto))
    application.add_handler(CommandHandler("adicionar", adicionar_participante))
    application.add_handler(CommandHandler("remover", remover_participante))
    application.add_handler(CommandHandler("listar", listar_participantes))

    print("Bot iniciado em modo polling. Pressione Ctrl+C para interromper.")
    application.run_polling()  # Iniciar o bot

# Ponto de entrada do script
if __name__ == '__main__':
    main()
