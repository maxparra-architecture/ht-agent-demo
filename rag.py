import streamlit as st
import oci
import genai_agent_service_bmc_python_client
import time

# Configuración OCI
config = oci.config.from_file(profile_name="DEFAULT")
endpoint = st.secrets["endpoint"]
agent_endpoint_id = st.secrets["agent_endpoint_id"]

# Inicializar estado de sesión
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None

# Crear cliente y sesión una sola vez
if st.session_state.session_id is None:
    client = genai_agent_service_bmc_python_client.GenerativeAiAgentRuntimeClient(
        config=config,
        service_endpoint=endpoint,
        retry_strategy=oci.retry.NoneRetryStrategy(),
        timeout=(10, 240)
    )

    session_details = genai_agent_service_bmc_python_client.models.CreateSessionDetails(
        display_name="streamlit-session",
        idle_timeout_in_seconds=600,
        description="Chat con agente RAG"
    )

    response = client.create_session(session_details, agent_endpoint_id)
    st.session_state.session_id = response.data.id

    if hasattr(response.data, "welcome_message") and response.data.welcome_message:
        st.session_state.messages.append({"role": "assistant", "content": response.data.welcome_message})

# UI
st.title("🧠 Agente RAG - HT LAD")

# Mostrar historial
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input del usuario
if prompt := st.chat_input("Escribe tu pregunta..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    client = genai_agent_service_bmc_python_client.GenerativeAiAgentRuntimeClient(
        config=config,
        service_endpoint=endpoint,
        retry_strategy=oci.retry.NoneRetryStrategy(),
        timeout=(10, 240)
    )

    with st.spinner("Consultando al agente..."):
        execute_details = genai_agent_service_bmc_python_client.models.ExecuteSessionDetails(
            user_message=prompt,
            should_stream=False
        )
        response = client.execute_session(agent_endpoint_id, st.session_state.session_id, execute_details)

    if response.status == 200:
        reply = response.data.message.content.text
        with st.chat_message("assistant"):
            st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})
    else:
        st.error(f"Error {response.status}: {response.data}")
