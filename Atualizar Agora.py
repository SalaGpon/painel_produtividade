# Adicione no HEADER, antes dos filtros:
col_header1, col_header2, col_header3 = st.columns([2, 1, 1])

with col_header3:
    if st.button("🔄 Atualizar Agora", use_container_width=True):
        st.cache_data.clear()
        st.rerun()