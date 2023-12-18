import requests
import parsel
import psycopg2
from datetime import datetime
from telegram import Bot
from time import sleep
from links import links_urls
import asyncio

banco_de_dados = ""
usuario_bd = ""
senha_bd = ""
bot_token = ""
chat_id = "@"

async def enviar_mensagem(nome_produto, valor_anterior, preco_float, link):
    bot = Bot(token=bot_token)
    await bot.send_message(chat_id=chat_id,text=f"Entrou em Promoção \n\nO {nome_produto} \n💵 De R$ {valor_anterior} para R$ {preco_float}\n\n🔗{link}.")

async def rastreamento_precos(urls, banco_de_dados, usuario_bd, senha_bd, bot_token, chat_id):
    valores_atuais = {}
    valores_antigos = {}

    while True:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 OPR/102.0.0.0',
        }

        for url in urls:
            req = requests.get(url, headers=headers)
            if req.status_code == 200:
                sel = parsel.Selector(text=req.text)
                nome_produto = sel.xpath('//h1[@class]/text()').get().strip()[:40]
                preco_produto = sel.xpath('//h4[@class]//text()').get()

                if preco_produto and any(char.isdigit() for char in preco_produto):
                    preco_float = float(preco_produto.replace('.', '').replace(',', '.').replace('R$', '').strip())
                    link = url
                    data_hora = lambda: datetime.now().strftime("%d/%m/%y %H:%M")

                    if url in valores_atuais:
                        valor_anterior = valores_atuais[url]
                        valores_antigos[url] = valor_anterior

                        if preco_float < valor_anterior:
                            conn = psycopg2.connect(database=banco_de_dados, user=usuario_bd, password=senha_bd,host="localhost", port="5433")
                            cur = conn.cursor()
                            cur.execute(
                                "UPDATE produtos SET preco_desconto = %s, data_hora = %s WHERE nome_produto = %s",
                                (preco_float, data_hora, nome_produto))
                            conn.commit()
                            conn.close()
                            preco_atual_formatado = '{:.2f}'.format(preco_float).replace('.', ',')
                            preco_anterior_formatado = '{:.2f}'.format(valor_anterior).replace('.', ',')
                            await enviar_mensagem(nome_produto, preco_anterior_formatado, preco_atual_formatado, link)
                            print("mensagem enviada")
                        elif preco_float == valor_anterior:
                            print(f"O produto {nome_produto} continua com o mesmo preço {preco_produto}.")

                    if url not in valores_atuais:
                        if not produto_existe_no_banco(nome_produto, link):
                            print(f"O produto {nome_produto} {preco_produto} está sendo adicionado pela primeira vez.")
                            conn = psycopg2.connect(database=banco_de_dados, user=usuario_bd, password=senha_bd,
                                                    host="localhost", port="5433")
                            cur = conn.cursor()
                            cur.execute(
                                "INSERT INTO produtos (nome_produto,preco_atual,link_produto,data_hora) VALUES (%s,%s,%s,%s)",
                                (nome_produto, preco_float, link, data_hora()))
                            conn.commit()
                            print("Os valores foram adicionados ao banco de dados")
                            conn.close()
                        else:
                            print(
                                f"O produto {nome_produto} já existe no banco de dados. Não será adicionado novamente.")

                    valores_atuais[url] = preco_float
                    valores_atuais[url] = preco_float

                else:
                    print(f'O produto {nome_produto} não possui um preço válido: {preco_produto}')
            else:
                print('Não foi possível encontrar os dados para a URL: ' + url)

        sleep(60)

def produto_existe_no_banco(nome_produto, link):
    conn = psycopg2.connect(database=banco_de_dados, user=usuario_bd, password=senha_bd, host="localhost", port="5433")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM produtos WHERE nome_produto = %s OR link_produto = %s", (nome_produto, link))
    count = cur.fetchone()[0]
    conn.close()
    return count > 0

if __name__ == "__main__":
    urls_nvme = links_urls('nvme')
    urls_fonte = links_urls('fonte')
    urls_placa_de_video = links_urls('placa_de_video')
    urls_monitor = links_urls('monitor')
    urls_headset = links_urls('headset')
    for url in urls_nvme:
        pass
    for url in urls_fonte:
        pass
    for url in urls_placa_de_video:
        pass
    for url in urls_monitor:
        pass
    for url in urls_headset:
        pass
    loop = asyncio.get_event_loop()
    loop.run_until_complete(rastreamento_precos(urls_nvme + urls_fonte + urls_placa_de_video + urls_monitor + urls_headset , banco_de_dados, usuario_bd, senha_bd, bot_token, chat_id))
