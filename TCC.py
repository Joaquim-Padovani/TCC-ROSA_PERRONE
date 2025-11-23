import cv2
import pytesseract
import time

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

placas_autorizadas = ["ABC1234", "XYZ9876", "JKS4567", "DMW6B16"]

def detectar_placa(frame):
    imagem_cinza = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    imagem_cinza = cv2.bilateralFilter(imagem_cinza, 11, 17, 17)

    bordas = cv2.Canny(imagem_cinza, 30, 200)

    contornos, _ = cv2.findContours(bordas, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contornos = sorted(contornos, key=cv2.contourArea, reverse=True)[:10]

    for contorno in contornos:
        perimetro = cv2.arcLength(contorno, True)
        aproximado = cv2.approxPolyDP(contorno, 0.018 * perimetro, True)

        if len(aproximado) == 4:
            x, y, w, h = cv2.boundingRect(aproximado)
            proporcao = w / h
            if 2 < proporcao < 6:
                return x, y, w, h

    return None


def capturar_e_ler_ao_vivo():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Não consegui abrir a webcam")
        return

    print("Pressione 'Q' para sair")

    porta_aberta = False
    portao_fechando = False

    tempo_abertura = 0
    tempo_fechamento = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Falha ao capturar frame")
            break

        tempo_atual = time.time()

        # =======================
        # PORTÃO ABERTO
        # =======================
        if porta_aberta:
            if tempo_atual - tempo_abertura >= 10:
                porta_aberta = False
                portao_fechando = True
                tempo_fechamento = time.time()
                print("🔴 Portão FECHANDO...")

            else:
                cv2.putText(frame, "PORTAO ABERTO - AGUARDE",
                            (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (0, 255, 255), 2)

                restante = int(10 - (tempo_atual - tempo_abertura))
                cv2.putText(frame, f"Fechando em: {restante}s",
                            (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (0, 0, 0), 2)

                cv2.imshow("Detector de Placa", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                continue

        # =======================
        # PORTÃO FECHANDO
        # =======================
        if portao_fechando:
            if tempo_atual - tempo_fechamento >= 3:
                portao_fechando = False
                print("✅ Portão FECHADO")

            else:
                cv2.putText(frame, "PORTAO FECHANDO...",
                            (50, 70), cv2.FONT_HERSHEY_SIMPLEX,
                            1.3, (0, 0, 255), 3)

                cv2.imshow("Detector de Placa", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                continue

        # MENSGEM PADRÃO (SEM ATRAPALHAR)
        cv2.putText(frame, "AGUARDANDO PLACA...",
                    (20, frame.shape[0] - 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (0, 0, 0), 2)

        # =======================
        # DETECÇÃO DA PLACA
        # =======================
        resultado = detectar_placa(frame)

        if resultado:
            x, y, w, h = resultado
            placa_img = frame[y:y + h, x:x + w]

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            texto = pytesseract.image_to_string(
                placa_img,
                config="--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            )

            placa = texto.strip().replace(" ", "").replace("\n", "")

            cv2.putText(frame, placa, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            if len(placa) >= 7:
                if placa in placas_autorizadas:
                    print("✅ PLACA AUTORIZADA:", placa)
                    print("⏳ Aguardando 3 segundos para abrir o portão...")

                    cv2.putText(frame, "PLACA AUTORIZADA",
                                (50, 100),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                1.2, (0, 255, 0), 3)

                    cv2.imshow("Detector de Placa", frame)
                    cv2.waitKey(1)

                    time.sleep(3)

                    print("🟢 PORTAO ABERTO")
                    porta_aberta = True
                    tempo_abertura = time.time()

                else:
                    print("❌ PLACA NAO AUTORIZADA:", placa)

                    cv2.putText(frame, "ACESSO NEGADO",
                                (50, 100),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                1.2, (0, 0, 255), 3)

        cv2.imshow("Detector de Placa", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    capturar_e_ler_ao_vivo()
