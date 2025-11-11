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
    num_frag = math.ceil(payload_total / payload_por_fragmento)

    st.write(f"Se generan **{num_frag} fragmentos**.")

    offset = 0
    fragmentos = []
    total_payload = 0
    total_transmitido = 0

    for i in range(num_frag):
        payload = min(payload_por_fragmento, payload_total - i * payload_por_fragmento)
        size = payload + header
        mf = 1 if i < num_frag - 1 else 0

        fragmentos.append((i+1, size, payload, mf, offset))

        offset += payload // 8
        total_payload += payload
        total_transmitido += size

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



