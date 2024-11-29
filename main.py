import random
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Obter o token do bot do arquivo .env
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# Lista dos participantes (substitua pelos nomes dos participantes do canal)
participantes = []

# Função para realizar o sorteio
async def sorteio_amigo_secreto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(participantes) < 2:
        await update.message.reply_text("É necessário pelo menos 2 participantes para realizar o sorteio.")
        return

    # Sorteio do amigo secreto (sem repetir ninguém)
    sorteio = participantes[:]
    random.shuffle(sorteio)
    
    # Mapeamento dos amigos secretos
    amigos_secretos = {}
    for i in range(len(participantes)):
        # Garantir que ninguém tire a si mesmo
        while sorteio[i] == participantes[i]:
            random.shuffle(sorteio)
        
        amigos_secretos[participantes[i]] = sorteio[i]
    
    # Enviar os resultados para cada participante de forma privada
    for participante in participantes:
        amigo = amigos_secretos[participante]
        await context.bot.send_message(chat_id=participante, text=f"Seu amigo secreto é: {amigo}")
    
    await update.message.reply_text("O sorteio foi realizado com sucesso! Cada participante receberá uma mensagem com o nome de seu amigo secreto.")

# Função para adicionar participantes ao sorteio
async def adicionar_participante(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario = update.message.from_user.id  # Identificador único do usuário
    if usuario not in participantes:
        participantes.append(usuario)
        await update.message.reply_text(f"Você foi adicionado ao sorteio, {update.message.from_user.first_name}.")
    else:
        await update.message.reply_text(f"Você já está no sorteio, {update.message.from_user.first_name}.")

# Função para remover participantes
async def remover_participante(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario = update.message.from_user.id
    if usuario in participantes:
        participantes.remove(usuario)
        await update.message.reply_text(f"Você foi removido do sorteio, {update.message.from_user.first_name}.")
    else:
        await update.message.reply_text(f"Você não está no sorteio, {update.message.from_user.first_name}.")

# Função para listar os participantes
async def listar_participantes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if participantes:
        nomes = [f"Usuário {id}" for id in participantes]
        await update.message.reply_text("Participantes atuais: " + ", ".join(nomes))
    else:
        await update.message.reply_text("Não há participantes no sorteio ainda.")

# Função principal para configurar o bot
def main():
    # Verifique se o token foi carregado corretamente
    if TELEGRAM_TOKEN is None:
        print("Erro: TOKEN não encontrado no arquivo .env")
        return
    
    # Criação da aplicação
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Adicionando handlers para os comandos
    application.add_handler(CommandHandler("iniciar", sorteio_amigo_secreto))
    application.add_handler(CommandHandler("adicionar", adicionar_participante))
    application.add_handler(CommandHandler("remover", remover_participante))
    application.add_handler(CommandHandler("listar", listar_participantes))
    
    # Iniciar o bot
    application.run_polling()

if __name__ == '__main__':
    main()
