import streamlit as st
import math
import matplotlib.pyplot as plt

st.title("Simulador de Fragmentación IP ")

mtu = st.number_input("MTU (bytes)", value=1500, step=10)
header = st.number_input("Tamaño cabecera IP (bytes)", value=20, step=1)
total = st.number_input("Tamaño total del datagrama IP (bytes)", value=4000, step=10)

if st.button("Fragmentar"):
    payload_total = total - header
    payload_por_fragmento = ((mtu - header) // 8) * 8
    if payload_total <= 0:
        st.error("El tamaño total debe ser mayor que la cabecera IP.")
        st.stop()
    if payload_por_fragmento <= 0:
        st.error("La MTU es demasiado pequeña para transportar datos con esa cabecera.")
        st.stop()

    # Construcción inicial de payloads por fragmento.
    payloads = []
    restante = payload_total
    while restante > 0:
        payload = min(payload_por_fragmento, restante)
        payloads.append(payload)
        restante -= payload

    # Caso especial: si el ultimo fragmento es menor que 8 bytes, intentar fusionarlo
    # con el penultimo si no se supera la MTU (cabecera + payload <= MTU).
    if len(payloads) >= 2 and payloads[-1] < 8:
        payload_penultimo = payloads[-2]
        payload_ultimo = payloads[-1]
        if header + payload_penultimo + payload_ultimo <= mtu:
            payloads[-2] = payload_penultimo + payload_ultimo
            payloads.pop()

    fragmentos = []
    offset = 0
    total_payload = 0
    total_transmitido = 0
    num_frag = len(payloads)

    for i, payload in enumerate(payloads):
        size = payload + header
        mf = 1 if i < num_frag - 1 else 0
        fragmentos.append((i + 1, size, payload, mf, offset))
        offset += payload // 8
        total_payload += payload
        total_transmitido += size

    st.write(f"Se generan **{num_frag} fragmentos**.")

    #st.table(fragmentos)

    # === Visualización ===
    fig, ax = plt.subplots(figsize=(14, 2 + num_frag * 0.6))

    pastel_colors = [
        "#b4d8e7", "#d0e3c4", "#f7d9c4", "#e8c7e6",
        "#f2e2ae", "#c6d9f0", "#e6ccb3"
    ]

    MIN_WIDTH_FOR_TEXT = 90

    for i, (num, size, payload, mf, off) in enumerate(fragmentos):

        # Cabecera
        ax.barh(i, header, left=0, color="#cccccc", edgecolor="black")

        # Payload
        ax.barh(i, payload, left=header,
                color=pastel_colors[i % len(pastel_colors)], edgecolor="black")

        texto = f"Frag {num} | Payload={payload} B | Offset={off} | MF={mf}"

        if payload >= MIN_WIDTH_FOR_TEXT:
            ax.text(header + payload / 2, i, texto,
                    ha="center", va="center", fontsize=12)
        else:
            ax.text(header + payload + 15, i, texto,
                    ha="left", va="center", fontsize=12)

    ax.set_xlabel("Tamaño en bytes del fragmento")
    ax.set_yticks(range(num_frag))
    ax.set_yticklabels([f"Fragmento {i+1}" for i in range(num_frag)])
    ax.set_title("Paquetes IP fragmentados: Cabecera + Payload")

    st.pyplot(fig)

    # === Cálculo y visualización de eficiencia ===
    eficiencia = (total_payload / total_transmitido) * 100

    st.markdown("---")
    st.subheader("Eficiencia de transmisión:")

    st.write(f"**Payload útil total:** {total_payload} bytes")
    st.write(f"**Bytes realmente transmitidos (incluyendo cabeceras):** {total_transmitido} bytes")

    st.write(f"**Eficiencia = {eficiencia:.2f}%**")


