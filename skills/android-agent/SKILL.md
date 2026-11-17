---
name: android-agent
description: Pareie e controle um Android autorizado por ADB Wi-Fi usando seletores UIAutomator e a biblioteca Device.
---

# Android Agent Kit — instruções para agentes

## Preparar e parear
1. Oriente o usuário a ativar Opções do desenvolvedor > Depuração sem fio.
2. Peça que consulte no aparelho o IP e a porta de pareamento. Execute `adb pair IP:PORTA_DE_PAREAMENTO` e solicite o código exibido.
3. Na tela principal, use o IP e a porta de conexão: `adb connect IP:PORTA`.
4. Confirme com `adb devices` e configure `ANDROID_SERIAL`. Nunca invente ou reutilize endereço de outro aparelho.
5. A conexão pode mudar após reinício ou troca de rede.

## Inspecionar e agir
Execute `python -m android_agent.inspect dump`. Examine `text`, `desc`, `id`, `clickable` e `bounds`. Para tocar: `python -m android_agent.inspect tap "texto visível"`. Para voltar: `python -m android_agent.inspect key KEYCODE_BACK`.

## Criar fluxo
Use `from android_agent import Device` e `device = Device()`. Chame `wake_unlock()`, inspecione com `dump()`, localize por `find(text=...)`, `find(desc=...)` ou `find(rid=...)` e toque no nó com `tap(node)`. Use `type_text()`, `swipe_up()`, `swipe_down()`, `back()`, `home()`, `open_url()`, `screenshot()` e `human_pause()`. Revise os elementos antes de ações sensíveis.

## Armadilhas
- **Tela bloqueada:** wake_unlock acorda e tenta apenas arrastar. Se houver PIN, padrão ou biometria, pare e peça desbloqueio manual; não tente contornar.
- **Dump vazio:** animações, vídeo e transições podem impedir o UIAutomator de obter estado ocioso. Aguarde, pause a animação ou tente novamente.
- **Acentos:** ADBKeyBoard melhora a digitação UTF-8. Sem ele, `input text` pode variar conforme aparelho e teclado.
- **IDs variáveis:** versões diferentes podem alterar resource-id, texto e hierarquia. Prefira texto/content-desc e confira o dump atual.
- **Sem bounds:** não toque no elemento. Nunca substitua seletores por coordenadas fixas.
- **Concorrência:** evite fluxos simultâneos no mesmo serial.

## Segurança
Use apenas dispositivos e contas autorizados. Respeite termos de serviço, evite spam e ações automáticas de publicar, enviar, curtir ou seguir. Não registre PINs, senhas ou tokens.
