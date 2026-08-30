# Instruções do Projeto - Calculadora_ROI_Consorcio

## Fluxo de Git

- Sempre que terminar uma alteração de código que funcione (testes passando,
  sem erros), faça commit e push automaticamente para o GitHub.
- Use mensagens de commit curtas e descritivas em português, no padrão:
  "Corrige X", "Adiciona Y", "Atualiza Z".
- Antes de commitar, rode a suíte de testes (pytest) e só prossiga se
  todos os testes passarem.
- Nunca commite arquivos sensíveis (.env, chaves de API, credenciais).
  Verifique o .gitignore antes de subir algo novo.
- Se os testes falharem, NÃO faça commit/push. Avise o problema e
  aguarde instrução.