import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from datetime import datetime
import time
import os
import tempfile
import shutil
import subprocess


def executar_robo_incor():
    st.subheader("⬇️ Download de PDFs de pacientes - INCOR")
    entrada_pacientes = st.text_area("Cole aqui os RGHCs dos pacientes (um por linha):")

    if st.button("Executar robô"):
        base_folder = r"D:\usuarios\enf51\Desktop\karol\pdfs"
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_folder = os.path.join(base_folder, timestamp)
        os.makedirs(output_folder, exist_ok=True)

        def iniciar_driver():
            options = webdriver.ChromeOptions()
            prefs = {
                "download.default_directory": output_folder,
                "download.prompt_for_download": False,
                "plugins.always_open_pdf_externally": True
            }
            options.add_experimental_option("prefs", prefs)
            options.add_argument("--start-maximized")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            profile_path = tempfile.mkdtemp()
            options.add_argument(f"--user-data-dir={profile_path}")
            service = Service(r"D:\usuarios\enf51\Desktop\karol\chromedriver.exe")
            driver = webdriver.Chrome(service=service, options=options)
            return driver, profile_path

        driver, profile_path = iniciar_driver()

        try:
            driver.get("http://intranet.phcnet.usp.br/default.aspx")
            st.success("🌐 Navegador iniciado")

            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, "userLogin")))
            driver.find_element(By.NAME, "userLogin").send_keys("k.wayla")
            driver.find_element(By.NAME, "userPassword").send_keys("Nefrologia@06")
            driver.find_element(By.ID, "btnEntrar").click()

            # Acessar HCMED
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.LINK_TEXT, "HCMED"))).click()

            # Trocar para nova aba
            WebDriverWait(driver, 20).until(lambda d: len(d.window_handles) > 1)
            driver.switch_to.window(driver.window_handles[1])

            # Login no HCMED
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "Email"))).send_keys("k.wayla")
            driver.find_element(By.ID, "Password").send_keys("Nefrologia@06")
            driver.find_element(By.XPATH, "//span[contains(text(), 'Acessar')]").click()

            # Aceitar termos de acesso
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "aceitar"))).click()

            pacientes = [p.strip() for p in entrada_pacientes.strip().splitlines() if p.strip()]
            progresso = st.progress(0)
            total = len(pacientes)

            for idx, rghc in enumerate(pacientes):
                try:
                    st.write(f"🔍 Buscando RGHC: {rghc}")
                    aba_principal = driver.current_window_handle

                    # Buscar paciente pelo RGHC
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "p_nclimycli")))
                    campo = driver.find_element(By.ID, "p_nclimycli")
                    campo.clear()
                    campo.send_keys(rghc)
                    driver.find_element(By.XPATH, "//input[@value=' Ok ']").click()
                    time.sleep(2)

                    # Clicar em "Resultados de Exames Laboratoriais"
                    WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                        (By.XPATH, "//font[contains(text(),'Resultados de Exames Laboratoriais')]"))).click()

                    # Aguardar tabela carregar
                    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located(
                        (By.XPATH, "//tr[@data-input='40346389_INCOR']")))

                    linhas = driver.find_elements(By.XPATH, "//tr[@data-input='40346389_INCOR']")
                    linhas.reverse()  # Começa dos mais recentes

                    hrefs_unicos = []
                    for linha in linhas:
                        try:
                            mostrar = linha.find_element(By.XPATH, ".//a[contains(text(), 'MOSTRAR')]")
                            href = mostrar.get_attribute("href")
                            if href and href not in hrefs_unicos:
                                hrefs_unicos.append(href)
                            if len(hrefs_unicos) >= 4:
                                break
                        except:
                            continue

                    if not hrefs_unicos:
                        st.warning(f"⚠️ Nenhum laudo disponível para RGHC: {rghc}")
                        continue

                    for href in hrefs_unicos:
                        try:
                            original_tabs = driver.window_handles
                            driver.execute_script("window.open(arguments[0], '_blank');", href)
                            WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > len(original_tabs))
                            nova_aba = [t for t in driver.window_handles if t not in original_tabs][0]
                            driver.switch_to.window(nova_aba)
                            time.sleep(3)

                            timeout = time.time() + 15
                            while True:
                                crdownloads = [f for f in os.listdir(output_folder) if f.endswith(".crdownload")]
                                if not crdownloads or time.time() > timeout:
                                    break
                                time.sleep(1)

                            driver.close()
                            driver.switch_to.window(aba_principal)

                        except:
                            if len(driver.window_handles) > 0:
                                try:
                                    driver.switch_to.window(aba_principal)
                                except:
                                    pass
                            continue

                except WebDriverException:
                    continue
                finally:
                    progresso.progress((idx + 1) / total)

            st.success(f"✅ PDFs foram baixados para: {output_folder}")

        except Exception as e:
            st.error(f"❌ Erro inesperado: {e}")

        finally:
            driver.quit()
            shutil.rmtree(profile_path, ignore_errors=True)
            st.write("✅ Robô finalizado")
