def recomendar(perfil):
    schema_fixo = perfil["schema_fixo"]
    precisa_acid = perfil["precisa_acid"]
    escala_horizontal = perfil["escala_horizontal"]
    tolera_atraso = perfil["tolera_atraso_de_consistencia"]
    dado_sensivel = perfil["dado_sensivel"]

    if precisa_acid and schema_fixo and not tolera_atraso:
        banco = "MySQL"
        cap = "CP"
        if dado_sensivel:
            justificativa = (
                "aceitar uma escrita parcial aqui pode autenticar ou "
                "autorizar alguem com base num dado que nunca foi "
                "confirmado; e' mais seguro recusar a operacao do que "
                "deixar o sistema acessivel com uma decisao errada"
            )
            risco_owasp = "A07"
        else:
            justificativa = (
                "sem ACID, duas operacoes concorrentes podem gerar um "
                "estado duplicado ou corrompido (ex: a mesma licenca "
                "vendida duas vezes); e' aceitavel recusar a escrita em "
                "vez de arriscar essa inconsistencia"
            )
            risco_owasp = "A08"
        return {
            "banco": banco,
            "cap": cap,
            "justificativa": justificativa,
            "risco_owasp": risco_owasp,
        }

    if escala_horizontal and tolera_atraso and not precisa_acid:
        banco = "MongoDB"
        cap = "AP"
        if dado_sensivel:
            justificativa = (
                "recusar a escrita para manter consistencia imediata "
                "derrubaria todo mundo que depende desse dado agora; "
                "aceita-se a janela curta de inconsistencia e trata-se "
                "qualquer efeito colateral (ex: revogar sessao) depois"
            )
            risco_owasp = "A02"
        else:
            justificativa = (
                "perder 1s de log e' aceitavel; parar de aceitar log "
                "durante uma particao de rede nao e', porque cria um "
                "buraco cego justamente na hora de um incidente"
            )
            risco_owasp = "A09"
        return {
            "banco": banco,
            "cap": cap,
            "justificativa": justificativa,
            "risco_owasp": risco_owasp,
        }

    if escala_horizontal and not tolera_atraso and dado_sensivel:
        banco = "MongoDB"
        cap = "CP"
        justificativa = (
            "um registro de auditoria que ficou desatualizado ou "
            "divergente entre replicas nao serve como prova depois de "
            "um incidente; melhor recusar a leitura/escrita do que "
            "confiar em um registro que pode nao refletir o que houve"
        )
        risco_owasp = "A08"
        return {
            "banco": banco,
            "cap": cap,
            "justificativa": justificativa,
            "risco_owasp": risco_owasp,
        }

    raise ValueError(f"perfil sem regra de decisao definida: {perfil}")


perfis = {
    "credenciais_do_SOC": {"schema_fixo": True, "precisa_acid": True, "escala_horizontal": False, "tolera_atraso_de_consistencia": False, "dado_sensivel": True},
    "telemetria_de_sensores": {"schema_fixo": False, "precisa_acid": False, "escala_horizontal": True, "tolera_atraso_de_consistencia": True, "dado_sensivel": False},
    "trilha_de_auditoria": {"schema_fixo": False, "precisa_acid": False, "escala_horizontal": True, "tolera_atraso_de_consistencia": False, "dado_sensivel": True},
    "carrinho_de_licencas": {"schema_fixo": True, "precisa_acid": True, "escala_horizontal": False, "tolera_atraso_de_consistencia": False, "dado_sensivel": False},
    "cache_de_sessoes": {"schema_fixo": True, "precisa_acid": False, "escala_horizontal": True, "tolera_atraso_de_consistencia": True, "dado_sensivel": True},
}


if __name__ == "__main__":
    for nome, perfil in perfis.items():
        r = recomendar(perfil)
        print(f"{nome:24s} -> {r['banco']:7s} | {r['cap']} | \"{r['justificativa']}\" | {r['risco_owasp']}")
