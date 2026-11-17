# Instruções Codex — Android Agent Kit

## Objetivo e pareamento
Este repositório controla um Android autorizado por ADB Wi-Fi com Python. Oriente o usuário a ativar Opções do desenvolvedor > Depuração sem fio, consultar no aparelho IP e porta de pareamento, executar `adb pair IP:PORTA_DE_PAREAMENTO` e informar o código. Depois use `adb connect IP:PORTA_DE_CONEXAO`, confirme com `adb devices` e configure `ANDROID_SERIAL`. Nunca invente endereços.

## Inspeção
Antes de agir, execute `python -m android_agent.inspect dump`. Examine text, desc, id, clickable e bounds. CLI: `python -m android_agent.inspect tap "texto"`, `python -m android_agent.inspect key KEYCODE_BACK` e `python -m android_agent.inspect shot arquivo.png`.

## Criar fluxos
Use `from android_agent import Device` e `device = Device()`. Acorde com `wake_unlock()`; leia com `dump()`; localize por `find(text=...)`, `find(desc=...)` ou `find(rid=...)`; toque no nó obtido via `tap(node)`. Digite com `type_text()`, role com `swipe_up()`/`swipe_down()`, volte com `back()`, use `home()`, `open_url()`, `screenshot()` e `human_pause()`. Não use coordenadas fixas.

## Armadilhas
- Tela bloqueada: wake_unlock só arrasta; se exigir PIN/padrão/biometria, pare e solicite desbloqueio manual.
- Dump vazio: animações e vídeo podem impedir o UIAutomator. Aguarde, pause ou tente novamente.
- Acentos: ADBKeyBoard melhora UTF-8; sem ele, input text pode variar.
- IDs e textos mudam entre versões. Inspecione a tela atual e prefira texto/content-desc.
- Elementos sem bounds não são tocáveis. Evite concorrência no mesmo serial.

## Segurança
Use apenas aparelhos/contas autorizados. Respeite termos de serviço, não faça spam e não automatize curtidas, comentários, seguidores ou mensagens. Não armazene credenciais.
