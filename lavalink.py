'''
Feito por liveira!
'''
# -------- Area de importações -------- #
import os # Importação da blibioteca do sistema operacional
import datetime # Importação da blibioteca de data
import discloud # Importação da blibioteca do discloud para verificar a RAM!
import json # Importação da blibioteca de manipulação de JSON
from subprocess import Popen
import subprocess # Importação da blibioteca de processos
import time # Importação de blibioteca de tempo
import sys 
import re
import asyncio
# -------- Area de inicialização de variaveis! -------- #

# Variavel de configuração do lavalink! Pode ser editado
nw = datetime.datetime.now()
lava_config = """
server: # REST and WS server
  port: 2333
  address: 0.0.0.0
lavalink:
  server:
    password: "discloud"
    sources:
      youtube: true
      bandcamp: true
      soundcloud: true
      twitch: true
      vimeo: true
      mixer: true
      http: true
      local: false
    bufferDurationMs: 400
    youtubePlaylistLoadLimit: 6 # Number of pages at 100 each
    youtubeSearchEnabled: true
    soundcloudSearchEnabled: true
    gc-warnings: true
    #ratelimit:
      #ipBlocks: ["1.0.0.0/8", "..."] # list of ip blocks
      #excludedIps: ["...", "..."] # ips which should be explicit excluded from usage by lavalink
      #strategy: "RotateOnBan" # RotateOnBan | LoadBalance | NanoSwitch | RotatingNanoSwitch
      #searchTriggersFail: true # Whether a search 429 should trigger marking the ip as failing
      #retryLimit: -1 # -1 = use default lavaplayer value | 0 = infinity | >0 = retry will happen this numbers times
metrics:
  prometheus:
    enabled: false
    endpoint: /metrics
sentry:
  dsn: ""
#  tags:
#    some_key: some_value
#    another_key: another_value
"""
with open('config.json','r') as f: # Abrindo o arquivo JSON
    config = json.load(f) # Transformando arquivo em um JSON

# Verificar se os logs estão ativados
if config['logMODE']:
    lava_config += '''
logging:
  file:
    max-history: 10
    max-size: 50MB
  path: ../../logs/lavalink/
  level:
    root: INFO
    lavalink: INFO
''' # Ativando os LOGS

# Tentativas
bot_process = None
lavalink_process = None
lavalink_tries = 0

### CHECAR DIRETÓRIO ###
def is_dir_valid(dir, name):
    for item in os.listdir(dir):
        if os.path.isdir(dir+"/"+item) and item == name:
            print("Achei")
            return True # Se ele encontrar o arquivo no diretorio retorna verdadeiro
    # Caso não achar, retorna falso
    return False
def is_file_valid(dir,name):
    for item in os.listdir(dir):
        if not os.path.isdir(item) and item == name:
            return True # Se ele encontrar o arquivo no diretorio retorna verdadeiro
    # Caso não achar, retorna falso
    return False
### FIM DE CHECAR DIRETÓRIO ###    




### RODAR LAVALINK ###
async def run_lavalink():
    print("Iniciando Lavalink...")
    java_path = f'../jdk-{config["openJDK"]["version"]}/bin/java'
    global lavalink_process
    lavalink_process = Popen([java_path,'-jar','Lavalink.jar'],cwd='./java/lavalink')
    global lavalink_tries
    if lavalink_tries < 3:
        if lavalink_process.poll == None:
            print('Tentando reineicar o lava link')
            lavalink_tries += 1
            run_lavalink()
    else:
        print('O lavalink caiu mais de 3 vezes, proecsso desligado')
        bot_process.kill()
        lavalink_process.kill()
        sys.kill(1)
### FIM DE RODAR LAVALINK ###





### INICIAR BOT ###
async def run_bot(dir):
    print("Preparando o Bot...")
    req = ""
    # INSTALAR BIBLIOTECAS
    with open("./bot/requirements.txt",'r') as f:
        req = f.read()
    for i in req.splitlines():
        process = Popen(["pip3", "install",i],stdout=subprocess.PIPE, stderr=subprocess.PIPE,)
        process.wait()
        if config['logMODE']:
            with open(f'./logs/{nw}.log','a') as f:
                f.write(f"logs:\n{process.stdout.read()}\n\n\n\nerros:\n{process.stderr.read()}")
        if process.returncode != 0:
            print(f"Erro ao instalar os módulos: {process.stderr.read()}")
            if lavalink_process:
                lavalink_process.kill()
            sys.exit(1)
    # LIGAR O BOT
    print("Iniciando o bot...")
    global bot_process
    bot_process = Popen(['python3',config['fileRunBot']],cwd='./bot',encoding='utf-8',stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(30)
    # ENQUANTO O BOT NÃO MORRER(ter status code)
    while not bot_process.poll:
        # se os logs estiverem desativados
        if not config['logMODE']:
            continue
        # se os logs estiverem ativados
        # capturar logs
        log = bot_process.stdout.read().encode("utf-8")
        # capturar logs de erros
        try:
            logErr = bot_process.stderr.read().encode("utf-8")
        except AttributeError:
            logErr = None
        # se algum erro for gerado, salvar ele
        if logErr != bot_process.stderr.read().encode("utf-8"):
            logErr2 = bot_process.stderr.read().encode("utf-8").replace(logErr,"")
            with open(f'./logs/{nw}.log','w+') as f:
                f.writelines(logErr2)
            logErr += logErr2
        # se o ultimo log for diferente dos logs atuais(foi escrito algum log), salvar ele
        if log != bot_process.stdout.read().encode("utf-8"):
            log2 = bot_process.stdout.read().encode("utf-8").replace(log,"")
            with open(f'./logs/{nw}.log','w+') as f:
                f.writelines(log2)
            log += log2
        time.sleep(5)
    else:
        # se o bot morrer
        print(f"O bot caiu: {bot_process.stderr.read()}")
        # matar o lavalink
        if lavalink_process:
            lavalink_process.kill()
        bot_process.kill()
        sys.exit(1)
### FIM DE INICIAR BOT ###



### INICIAR TUDO ###
async def run():
    # checar o SO
    if os.name != "posix":
        print("Este código só funciona em distribuições linux")
        sys.exit(1)
    # informações de memória ram
    ram = discloud.total_ram()
    if ram == 'Dados não encontrados':
        return print('Verificação de RAM indisponivel')
    nRam = int(re.match("^(\d*)(?:[a-zA-Z]*)$",ram).group(1))
    lRam = re.match("^(\d*)([a-zA-Z]*)$",ram).group(2)
    if nRam < 512 and lRam.upper() == 'MB':
        print(f'Você só tem {ram} disponivel, o minimo para você não ter problemas é 512MB!')
    else: 
        print(f"Você tem disponivel {ram}")
    # criar pastas
    print("Preparando o sistema")
    # criar a pasta de logs
    if config['logMODE'] and not is_dir_valid("./","logs"):
        try:
            os.mkdir("logs")
        except Exception as ex:
            print(f"Erro ao criar a pasta logs: {ex.args}") 
            sys.exit(1)
    # criar a pasta java
    if not is_dir_valid('./','java'):
        try:
            os.mkdir("java")
        except Exception as ex:
            print(f"Erro ao criar a pasta java: {ex.args}")
            sys.exit(1)
    # checar o arquivo principal
    if not is_file_valid("./bot",config['fileRunBot']):
        print(f"O arquivo {config['fileRunBot']} não foi encontrado")
        sys.exit(1)
    # se não existir a pasta java = não tem o java, então vai baixar o java
    if not is_dir_valid('./java',f'jdk-{config["openJDK"]["version"]}'):
        print("Baixando o openJDK")
        down_jdk = None
        down_jdk_cmd  = ["wget","-c",'-O',"java.tar.gz",config['openJDK']['linkDown']]
        if config['logMODE']: # se os logs estiverem ativados, salvar os logs do download
            down_jdk_cmd.insert(2, f"../logs/downjava-{nw}.log")
            down_jdk_cmd.insert(2, f"-o")
        down_jdk = Popen(down_jdk_cmd,encoding='utf-8',cwd='./java',stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        down_jdk.wait()
        if down_jdk.returncode != 0:
            print(f"Erro ao baixar o openJDK: - {down_jdk.stderr.read().encode('utf-8')}")
            sys.exit(1)    
        print("OpenJDK baixado com sucesso")
        print("Extraindo o OpenJDK")
        extract = Popen(["tar","-zxvf","java.tar.gz"],encoding='utf-8',cwd="./java",stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        extract.wait()
        if extract.returncode != 0:
            print(f"Erro ao extrair o OpenJDK: - {extract.stderr.read().encode('utf-8')}")
            sys.exit(1)
        # salvar logs da extração do java
        if config['logMODE']:
            with open(f"./logs/extractJava-{nw}.log",'w+') as f:
                f.write(extract.stdout.read())
        print("Extração completa")
        # remover o java para liberar espaço
        try:
            os.remove("./java/java.tar.gz")
        except Exception as ex:
            print("Falha ao remover o java.tar.gz")
            print(ex.args)
    if not is_dir_valid('./java','lavalink'): # criar a pasta lavalink dentro da pasta java
        try:
            os.mkdir("./java/lavalink")
        except Exception as ex:
            print(f"Erro ao criar a pasta lavalink: {ex.args}")
            sys.exit(1)
    if not is_file_valid("./java/lavalink","Lavalink.jar"): # se não tiver o arquivo do lavalink, baixar
        print('Baixando o lavalink')
        down_lava_cmd = ["wget","-c", "-O", "Lavalink.jar", config['lavalink']]
        downlava = None
        if config['logMODE']: # se os logs estiverem ativados, salvar os logs do download
            down_lava_cmd.insert(2, f"../../logs/lavalinkdown-{nw}.log")
            down_lava_cmd.insert(2, f"-o")
        downlava = Popen(down_lava_cmd, encoding="utf-8", cwd="./java/lavalink",stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        downlava.wait()
        if downlava.returncode != 0:
            print(f"Erro ao baixar o lavalink: - {downlava.stderr.read().encode('utf-8')}")
            sys.exit(1)
        print("Lavalink baixado com sucesso")
    if is_file_valid("./java/lavalink","application.yml"):
        os.remove("./java/lavalink/application.yml")
    with open('./java/lavalink/application.yml','w+') as f:
        f.write(lava_config)
    await run_lavalink()
    time.sleep(30)
    await run_bot('./bot')
asyncio.run(run())