import time
import traceback
import undetected_chromedriver as uc
import re  # Import necessário para usar expressões regulares
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Solicitar o CNPJ do usuário
cnpj_raw = input("Por favor, digite o CNPJ (pode incluir pontos, traços e barra): ")

# Remover caracteres especiais do CNPJ (mantendo apenas dígitos)
cnpj = re.sub(r'\D', '', cnpj_raw)
print(f"CNPJ lido e sanitizado: {cnpj}")

# Atenção para cnpjs que só possam ser acessados pelo certificado da Alldax 

# Inicializar o driver com o undetected_chromedriver
options = uc.ChromeOptions()
options.add_argument('--start-maximized')
driver = uc.Chrome(options=options,version_main=132 )

# Configuração do Chrome
    # options = uc.ChromeOptions()
    # prefs = {"download.default_directory": download_path, "download.prompt_for_download": False}
    # options.add_experimental_option("prefs", prefs)
    # driver = uc.Chrome(options=options, version_main=132)

# Função para login no site
def login_ecac(driver):
    try:
        driver.get("https://cav.receita.fazenda.gov.br")
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="login-dados-certificado"]/p[2]/input'))
        ).click()
        time.sleep(5)
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="login-certificate"]'))
        ).click()
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="btnPerfil"]/span'))
        )
        print("Login realizado com sucesso!")
    except Exception as e:
        print(f"Erro ao realizar login: {e}")

# Função para navegar e selecionar o CNPJ
def selecionar_cnpj(driver, cnpj):
    try:
        WebDriverWait(driver, 10).until(
             EC.element_to_be_clickable((By.XPATH,'//*[@id="btnPerfil"]/span'))
         ).click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="txtNIPapel2"]'))
        ).send_keys(cnpj)
        time.sleep(5)
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="formPJ"]/input[4]'))
        ).click()
        print(f"CNPJ {cnpj} selecionado com sucesso!")
    except Exception as e:
        print(f"Erro ao selecionar o CNPJ {cnpj}: {e}")

# Função para navegar até a página de consulta à PER/DCOMP
def navegar_consulta(driver):
    try:
        # Navegar para a página de consulta
        driver.get("https://www3.cav.receita.fazenda.gov.br/perdcomp-web/#/documento/identificacao-novo")

        # Esperar e clicar no link 'Visualizar Documentos'
        visualizar_xpath = "//i[contains(@class, 'icon-VisualizarDocumento')]/ancestor::a"
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, visualizar_xpath))
        ).click()

        # Agora, clicar na aba 'Documentos Entregues'
        documentos_entregues_xpath = "//li[@id='Documentos Entregues']/a"
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, documentos_entregues_xpath))
        ).click()

        print("Navegação para 'Documentos Entregues' realizada com sucesso!")
    except Exception as e:
        print(f"Erro ao navegar para a página de consulta: {e}")

# Função para verificar qual XPath está presente para o botão de avançar
def verificar_xpath_botao_avancar(driver):
    xpaths = [
        '(//a[@aria-label="Next"])[2]',  # Primeira possibilidade
        '(//a[@aria-label="Next"])[1]'   # Segunda possibilidade
    ]
    
    for xpath in xpaths:
        try:
            # Verificar se o botão de avançar existe para o XPath atual
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            print(f"Botão de avançar encontrado com XPath: {xpath}")
            return xpath  # Retorna o XPath válido
        except Exception:
            continue  # Tenta o próximo XPath
    
    print("Nenhum botão de avançar encontrado.")
    return None  # Retorna None se nenhum dos dois funcionar

# Função para verificar e clicar em todos os botões de download
def verificar_e_clicar_todos_botoes_download(driver, botao_avancar_xpath):
    try:
        while True:  # Loop para continuar enquanto houver páginas
            # Iterar até no máximo 5 botões na página atual
            for i in range(1, 6):
                botao_download_xpath = f'(//i[contains(@class, "icon-button") and contains(@class, "icon-print") and contains(@class, "iconeAcao")])[{i}]'
                try:
                    botao_download = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, botao_download_xpath))
                    )
                    print(f"Botão de download {i} encontrado. Forçando clique via JS...")

                    # Rolamos até o botão, para garantir que ele esteja no DOM
                    driver.execute_script("arguments[0].scrollIntoView(true);", botao_download)
                    time.sleep(1)

                    # Agora, em vez de usar botao_download.click(), forçamos via JavaScript
                    driver.execute_script("arguments[0].click();", botao_download)
                    print(f"Botão de download {i} clicado com sucesso (JS).")

                    # Esperar alguns segundos para garantir que o arquivo seja baixado
                    time.sleep(5)

                except Exception as e:
                    print(f"Erro ao verificar ou clicar no botão de download {i}: {e}")
                    break  # Interrompe o loop caso não encontre o próximo botão

            # Rolar até o final da página para garantir que a paginação está visível
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            print("Rolando até o final da página para garantir visibilidade da paginação.")
            time.sleep(2)

            # Verifica se chegou ao final (botão de avançar desabilitado)
            botao_desabilitado_xpath = '(//li[@class="page-item ng-star-inserted disabled"])[1]'
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, botao_desabilitado_xpath))
                )
                print("Botão de avançar está desabilitado. Não há mais páginas para avançar.")
                encerrar_sessao(driver)
                return  # Sai do loop
            except Exception:
                print("Botão de avançar não está desabilitado. Continuando...")

            # Verificar e clicar no botão para avançar
            try:
                botao_avancar = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, botao_avancar_xpath))
                )
                print("Botão de avançar para próxima página encontrado. Clicando no botão...")

                driver.execute_script("arguments[0].scrollIntoView(true);", botao_avancar)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", botao_avancar)

                print("Avançando para a próxima página...")
                time.sleep(2)
            except Exception as e:
                print("Erro ao clicar no botão de avançar.")
                break

    except Exception as e:
        print(f"Erro ao verificar ou clicar nos botões de download: {e}")

# Função para encerrar a sessão com segurança
def encerrar_sessao(driver):
    try:
        # Voltar para a página inicial do eCAC
        ecac_home_url = "https://cav.receita.fazenda.gov.br/ecac/Default.aspx"
        driver.get(ecac_home_url)
        print("Voltando para a página inicial do eCAC...")

        # Esperar até que o botão "Sair com Segurança" esteja visível e clicável
        sair_xpath = "//span[contains(text(), 'Sair com Segurança')]"
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, sair_xpath))
        ).click()
        print("Sessão encerrada com segurança!")
        time.sleep(2)  # Aguarde um tempo para garantir que a ação foi concluída
    except Exception as e:
        print(f"Erro ao encerrar a sessão: {e}")

# Fluxo principal
try:
    login_ecac(driver)
    time.sleep(2)  # Aguarde 2 segundos para observar o navegador
    selecionar_cnpj(driver, cnpj)
    time.sleep(5)  # Aguarde 5 segundos para observar o navegador
    navegar_consulta(driver)
    time.sleep(2)  # Aguarde 2 segundos para observar o navegador

    # Verificar qual XPath deve ser usado para o botão de avançar
    botao_avancar_xpath = verificar_xpath_botao_avancar(driver)
    if botao_avancar_xpath:
        verificar_e_clicar_todos_botoes_download(driver, botao_avancar_xpath)
    else:
        print("Não foi possível determinar o XPath do botão de avançar. Encerrando a rotina.")
except Exception as e:
    print("Ocorreu um erro durante a execução do script:")
    traceback.print_exc()
finally:
    try:
        encerrar_sessao(driver)  # Chamar a função para encerrar a sessão
    except Exception:
        print("Não foi possível encerrar a sessão de forma segura.")
    finally:
        driver.quit()  # Garantir que o navegador será fechado