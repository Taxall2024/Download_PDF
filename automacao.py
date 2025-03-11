import os
import time
import traceback
import random  # Para atrasos aleatórios
import undetected_chromedriver as uc
import re

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# === Função para fazer movimentos de mouse aleatórios ===
def random_mouse_moves(driver, moves=3):
    """
    Movimenta o mouse um número 'moves' de vezes com offsets aleatórios.
    Isso ajuda a simular uma interação mais humana, sem sair da janela.
    """
    for _ in range(moves):
        x_offset = random.randint(-30, 30)
        y_offset = random.randint(-30, 30)
        try:
            ActionChains(driver).move_by_offset(x_offset, y_offset).perform()
            # "Reseta" o mouse para não acumular offset
            ActionChains(driver).move_by_offset(0, 0).perform()
        except:
            # Se der "move target out of bounds", ignora e segue
            pass
        time.sleep(random.uniform(0.3, 1.2))

# === Solicitar entradas do usuário ===
cnpj_raw = input("Por favor, digite o CNPJ (pode incluir pontos, traços e barra): ")
cnpj = re.sub(r'\D', '', cnpj_raw)
print(f"CNPJ lido e sanitizado: {cnpj}")

data_inicial_raw = input("Por favor, digite a data inicial (dd/mm/aaaa): ")
data_final_raw = input("Por favor, digite a data final (dd/mm/aaaa): ")

data_inicial_digits = re.sub(r'\D', '', data_inicial_raw)
data_final_digits = re.sub(r'\D', '', data_final_raw)

def formatar_data(digits):
    if len(digits) == 8:  # Supondo ddmmYYYY
        return digits[:2] + "/" + digits[2:4] + "/" + digits[4:]
    else:
        return data_inicial_raw  # Fallback

data_inicial_formatada = formatar_data(data_inicial_digits)
data_final_formatada = formatar_data(data_final_digits)

print(f"Data inicial lida e formatada: {data_inicial_formatada}")
print(f"Data final lida e formatada: {data_final_formatada}")

# === Configurar pasta de downloads ===
download_base_path = r"C:\Users\pedro.melo\Desktop\0_TAX\DownloadPerDcomp\Download_PDF\data_output"
cnpj_subfolder = os.path.join(download_base_path, cnpj)
os.makedirs(cnpj_subfolder, exist_ok=True)
print(f"Pasta de download criada (ou já existente): {cnpj_subfolder}")

# === Inicializar o driver com preferências de download ===
options = uc.ChromeOptions()

# Ainda tentamos usar prefs, embora em incognito geralmente não funcione
prefs = {
    "download.default_directory": cnpj_subfolder,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True
}
options.add_experimental_option("prefs", prefs)

# Modo Incógnito e maximizado
options.add_argument('--incognito')
options.add_argument('--start-maximized')

# Definir User-Agent customizado (exemplo do Chrome estável no Windows 64 bits)
custom_user_agent = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/111.0.0.0 Safari/537.36"
)
options.add_argument(f"--user-agent={custom_user_agent}")

driver = uc.Chrome(options=options, version_main=132)

# == Redefinindo navigator.webdriver via DevTools ==
driver.execute_cdp_cmd(
    "Page.addScriptToEvaluateOnNewDocument",
    {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            });
        """
    }
)

# === O COMANDO CHAVE PARA FORÇAR DOWNLOADS EM INCÓGNITO ===
driver.execute_cdp_cmd("Page.setDownloadBehavior", {
    "behavior": "allow",
    "downloadPath": cnpj_subfolder
})
# ======================

def login_ecac(driver):
    try:
        driver.get("https://cav.receita.fazenda.gov.br")

        # Logo após carregar a página, movimentos de mouse
        time.sleep(random.uniform(2, 4))
        random_mouse_moves(driver, moves=3)

        # Rolagem "parcial"
        driver.execute_script("window.scrollBy(0, 300);")
        time.sleep(random.uniform(1, 3))

        # Espera o botão 'usar Certificado Digital' ficar clicável
        botao_cert_1 = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="login-dados-certificado"]/p[2]/input'))
        )

        # Atraso aleatório antes de clicar
        time.sleep(random.uniform(2, 5))
        botao_cert_1.click()

        # Após clicar, mais movimentos de mouse
        time.sleep(random.uniform(1, 3))
        random_mouse_moves(driver, moves=2)

        # Outra pequena rolagem
        driver.execute_script("window.scrollBy(0, 250);")
        time.sleep(random.uniform(1, 2))

        # Espera o link 'login-certificate'
        botao_cert_2 = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="login-certificate"]'))
        )
        # Novo atraso aleatório
        time.sleep(random.uniform(2, 5))
        botao_cert_2.click()

        # Aguarda ícone de perfil
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="btnPerfil"]/span'))
        )
        print("Login realizado com sucesso!")
    except Exception as e:
        print(f"Erro ao realizar login: {e}")

def selecionar_cnpj(driver, cnpj):
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="btnPerfil"]/span'))
        ).click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="txtNIPapel2"]'))
        ).send_keys(cnpj)
        time.sleep(3)
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="formPJ"]/input[4]'))
        ).click()
        print(f"CNPJ {cnpj} selecionado com sucesso!")
    except Exception as e:
        print(f"Erro ao selecionar o CNPJ {cnpj}: {e}")

def navegar_consulta(driver, data_inicial, data_final):
    try:
        driver.get("https://www3.cav.receita.fazenda.gov.br/perdcomp-web/#/documento/identificacao-novo")

        visualizar_xpath = "//i[contains(@class, 'icon-VisualizarDocumento')]/ancestor::a"
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, visualizar_xpath))
        ).click()

        documentos_entregues_xpath = "//li[@id='Documentos Entregues']/a"
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, documentos_entregues_xpath))
        ).click()

        print("Navegação para 'Documentos Entregues' realizada com sucesso!")

        campo_data_inicial = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "(//input[@id='date'])[1]"))
        )
        campo_data_inicial.clear()
        campo_data_inicial.send_keys(data_inicial)
        time.sleep(1)

        campo_data_final = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "(//input[@id='date'])[2]"))
        )
        campo_data_final.clear()
        campo_data_final.send_keys(data_final)
        time.sleep(1)

        print(f"Datas de consulta inseridas: {data_inicial} até {data_final}")
    except Exception as e:
        print(f"Erro ao navegar para a página de consulta: {e}")

def verificar_xpath_botao_avancar(driver):
    xpaths = [
        '(//a[@aria-label="Next"])[2]',
        '(//a[@aria-label="Next"])[1]'
    ]
    for xpath in xpaths:
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            print(f"Botão de avançar encontrado com XPath: {xpath}")
            return xpath
        except:
            continue
    print("Nenhum botão de avançar encontrado.")
    return None

def verificar_e_clicar_todos_botoes_download(driver, botao_avancar_xpath):
    try:
        pagina_atual = 2
        while True:
            for i in range(1, 6):
                botao_download_xpath = f'(//i[contains(@class, "icon-button") and contains(@class, "icon-print") and contains(@class, "iconeAcao")])[{i}]'
                try:
                    botao_download = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, botao_download_xpath))
                    )
                    print(f"Botão de download {i} encontrado. Forçando clique via JS...")

                    driver.execute_script("arguments[0].scrollIntoView(true);", botao_download)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", botao_download)
                    print(f"Botão de download {i} clicado com sucesso (JS).")

                    time.sleep(5)
                except Exception as e:
                    print(f"Erro ao verificar ou clicar no botão de download {i}: {e}")
                    break

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            print("Rolando até o final da página para garantir visibilidade da paginação.")
            time.sleep(2)

            botao_desabilitado_xpath = '(//li[@class="page-item ng-star-inserted disabled"])[1]'
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, botao_desabilitado_xpath))
                )
                print("Botão de avançar está desabilitado. Não há mais páginas para avançar.")
                encerrar_sessao(driver)
                return
            except:
                print("Botão de avançar não está desabilitado. Continuando...")

            try:
                botao_avancar = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, botao_avancar_xpath))
                )
                print("Botão de avançar para próxima página encontrado. Clicando no botão...")

                driver.execute_script("arguments[0].scrollIntoView(true);", botao_avancar)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", botao_avancar)

                print(f"Avançando para a página {pagina_atual}")
                pagina_atual += 1
                time.sleep(2)
            except Exception as e:
                print("Erro ao clicar no botão de avançar.")
                break
    except Exception as e:
        print(f"Erro ao verificar ou clicar nos botões de download: {e}")

def encerrar_sessao(driver):
    try:
        ecac_home_url = "https://cav.receita.fazenda.gov.br/ecac/Default.aspx"
        driver.get(ecac_home_url)
        print("Voltando para a página inicial do eCAC...")

        sair_xpath = "//span[contains(text(), 'Sair com Segurança')]"
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, sair_xpath))
        ).click()
        print("Sessão encerrada com segurança!")
        time.sleep(2)
    except Exception as e:
        print(f"Erro ao encerrar a sessão: {e}")

# === Fluxo principal ===
try:
    # 1. Login (com atrasos aleatórios, movimentos de mouse e rolagem)
    login_ecac(driver)
    time.sleep(2)

    # 2. Selecionar CNPJ
    selecionar_cnpj(driver, cnpj)
    time.sleep(5)

    # 3. Navegar e inserir datas
    navegar_consulta(driver, data_inicial_formatada, data_final_formatada)
    time.sleep(2)

    # 4. Verificar qual XPath do botão de avançar e fazer downloads
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
        encerrar_sessao(driver)
    except:
        print("Não foi possível encerrar a sessão de forma segura.")
    finally:
        driver.quit()