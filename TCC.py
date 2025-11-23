import cv2
import pytesseract
import time

# Caminho para o executável do Tesseract (OCR) no Windows
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Lista de placas autorizadas no sistema
placas_autorizadas = ["ABC1234", "XYZ9876", "JKS4567", "DMW6B16"]

# =========================================================
# FUNÇÃO: detectar_placa(frame)
# Responsável por encontrar uma possível placa no frame da câmera
# =========================================================
def detectar_placa(frame):

    # Converte a imagem para escala de cinza (facilita a detecção)
    imagem_cinza = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Aplica um filtro para reduzir ruídos e manter as bordas mais nítidas
    imagem_cinza = cv2.bilateralFilter(imagem_cinza, 11, 17, 17)

    # Detecta as bordas da imagem
    bordas = cv2.Canny(imagem_cinza, 30, 200)

    # Encontra os contornos presentes nas bordas detectadas
    contornos, _ = cv2.findContours(bordas, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Ordena os contornos por área (do maior para o menor) e pega os 10 maiores
    contornos = sorted(contornos, key=cv2.contourArea, reverse=True)[:10]

    # Percorre os contornos encontrados
    for contorno in contornos:

        # Calcula o perímetro do contorno
        perimetro = cv2.arcLength(contorno, True)

        # Aproxima o formato do contorno
        aproximado = cv2.approxPolyDP(contorno, 0.018 * perimetro, True)

        # Se o contorno tiver 4 lados, pode ser uma placa (formato retangular)
        if len(aproximado) == 4:
            x, y, w, h = cv2.boundingRect(aproximado)

            # Calcula a proporção largura / altura
            proporcao = w / h

            # Verifica se a proporção parece com uma placa real
            if 2 < proporcao < 6:
                return x, y, w, h

    # Se nenhuma placa for detectada
    return None


# =========================================================
# FUNÇÃO PRINCIPAL: capturar_e_ler_ao_vivo()
# Responsável por capturar imagens da câmera e controlar o portão
# =========================================================
def capturar_e_ler_ao_vivo():

    # Inicia a captura da webcam
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Não consegui abrir a webcam")
        return

    print("Pressione 'Q' para sair")

    # Estados do portão
    porta_aberta = False
    portao_fechando = False

    # Controle de tempo
    tempo_abertura = 0
    tempo_fechamento = 0

    # Loop infinito para leitura contínua da câmera
    while True:
        ret, frame = cap.read()

        if not ret:
            print("Falha ao capturar frame")
            break

        # Pega o tempo atual
        tempo_atual = time.time()

        # =======================
        # PORTÃO ABERTO
        # =======================
        if porta_aberta:

            # Se já passou 10 segundos, o portão começa a fechar
            if tempo_atual - tempo_abertura >= 10:
                porta_aberta = False
                portao_fechando = True
                tempo_fechamento = time.time()
                print("🔴 Portão FECHANDO...")

            else:
                # Mostra mensagem de portão aberto
                cv2.putText(frame, "PORTAO ABERTO - AGUARDE",
                            (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            (0, 255, 255),
                            2)

                # Calcula o tempo restante para fechar
                restante = int(10 - (tempo_atual - tempo_abertura))

                # Mostra o tempo restante
                cv2.putText(frame, f"Fechando em: {restante}s",
                            (50, 100),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            (0, 0, 0),
                            2)

                cv2.imshow("Detector de Placa", frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

                continue

        # =======================
        # PORTÃO FECHANDO
        # =======================
        if portao_fechando:

            # Após 3 segundos, o portão é considerado fechado
            if tempo_atual - tempo_fechamento >= 3:
                portao_fechando = False
                print("✅ Portão FECHADO")

            else:
                # Mostra mensagem de portão fechando
                cv2.putText(frame, "PORTAO FECHANDO...",
                            (50, 70),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1.3,
                            (0, 0, 255),
                            3)

                cv2.imshow("Detector de Placa", frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

                continue

        # =======================
        # MENSAGEM PADRÃO
        # =======================
        cv2.putText(frame, "AGUARDANDO PLACA...",
                    (20, frame.shape[0] - 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 0),
                    2)

        # =======================
        # DETECÇÃO DA PLACA
        # =======================
        resultado = detectar_placa(frame)

        if resultado:

            # Pega as coordenadas da placa
            x, y, w, h = resultado

            # Recorta a imagem somente da área da placa
            placa_img = frame[y:y + h, x:x + w]

            # Desenha um retângulo em volta da placa
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Usa OCR para tentar ler o texto da placa
            texto = pytesseract.image_to_string(
                placa_img,
                config="--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            )

            # Limpa o texto extraído
            placa = texto.strip().replace(" ", "").replace("\n", "")

            # Mostra a placa reconhecida na tela
            cv2.putText(frame, placa, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.9,
                        (0, 255, 0),
                        2)

            # Verifica se o tamanho do texto é válido
            if len(placa) >= 7:

                # Se a placa estiver na lista de autorizadas
                if placa in placas_autorizadas:
                    print("✅ PLACA AUTORIZADA:", placa)
                    print("⏳ Aguardando 3 segundos para abrir o portão...")

                    cv2.putText(frame, "PLACA AUTORIZADA",
                                (50, 100),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                1.2,
                                (0, 255, 0),
                                3)

                    cv2.imshow("Detector de Placa", frame)
                    cv2.waitKey(1)

                    # Espera 3 segundos antes de abrir
                    time.sleep(3)

                    print("🟢 PORTAO ABERTO")

                    porta_aberta = True
                    tempo_abertura = time.time()

                else:
                    # Caso a placa não seja autorizada
                    print("❌ PLACA NAO AUTORIZADA:", placa)

                    cv2.putText(frame, "ACESSO NEGADO",
                                (50, 100),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                1.2,
                                (0, 0, 255),
                                3)

        cv2.imshow("Detector de Placa", frame)

        # Se apertar 'q', o programa encerra
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Finaliza a câmera e fecha as janelas
    cap.release()
    cv2.destroyAllWindows()


# Executa o programa principal
if __name__ == "__main__":
    capturar_e_ler_ao_vivo()
