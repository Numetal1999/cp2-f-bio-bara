# Auditoria - app_vulneravel.py

| # | Falha | OWASP 2025 | Impacto | Correcao |
|---|-------|------------|---------|----------|
| 1 | SQL Injection em `/api/usuarios/buscar` (nome concatenado na query) | A03 | Qualquer usuario pode ler a tabela inteira, inclusive senha | Query parametrizada com `%s` e `LIKE %s` |
| 2 | XSS refletido em `/perfil` (parametro `u` volta cru no HTML) | A03 | Execucao de script no navegador de quem clicar no link | Escapar a saida com `markupsafe.escape` antes de montar o HTML |
| 3 | `DELETE /api/usuarios/<id>` sem autenticacao nem autorizacao | A01 | Qualquer requisicao apaga qualquer usuario | Exigir `X-API-Key` valido e nivel de acesso >= 5 |
| 4 | `/api/relatorio` devolve traceback e nome de tabela no erro | A05 | Vaza estrutura interna do banco para reconhecimento de ataque | Capturar excecao e devolver `{"erro":"erro interno"}` com 500 |
| 5 | Senha do banco (`"senha"`) e `SENHA_MESTRA` escritas no codigo | A02 | Vazamento de credencial em qualquer copia do repositorio | Credenciais via variavel de ambiente, nunca no codigo |
| 6 | `SELECT *` em `/api/usuarios/buscar` expõe a coluna senha | A02 | Hashes/senhas de todos os usuarios encontrados vazam na resposta | Selecionar explicitamente `id, nome, email` |
| 7 | `debug=True` em producao | A05 | Ativa o debugger do Werkzeug, que pode executar codigo remotamente | `debug=False` antes de expor a porta |
| 8 (ausencia) | Nenhum header de seguranca em nenhuma resposta | A05 | Sem CSP/X-Frame-Options/X-Content-Type-Options, a aplicacao fica mais exposta a XSS, clickjacking e MIME sniffing | Adicionar os headers em um `after_request` |
| 9 (ausencia) | Nenhuma requisicao e' registrada em lugar nenhum | A09 | Sem log, um ataque bem-sucedido nao deixa rastro para investigacao | Registrar `ip`, `metodo` e `path` de cada requisicao em um `before_request` |
