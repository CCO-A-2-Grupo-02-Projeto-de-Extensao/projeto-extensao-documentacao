# Arquitetura RabbitMQ para notificações e e-mail

## Decisão de arquitetura

O Spring Boot continua responsável por:

- receber a ação do usuário
- persistir o documento
- publicar o evento no RabbitMQ

O Java Spring não envia e-mail. Ele apenas publica um evento de negócio para o broker.

O e-mail passa a ser responsabilidade de um worker externo dedicado, conectado à fila do RabbitMQ, por exemplo:

- Python + smtplib + email.message
- Node.js + Nodemailer
- outro consumidor específico, em container separado

Assim, o RabbitMQ vira a infraestrutura de transporte e orquestração, e o envio efetivo do e-mail fica fora do backend Java.

## Topologia sugerida

- exchange: `exchange_documento_atualizado`
- filas:
  - `queue_responsaveis_documentos`
  - `queue_diretoria_documentos`
- bindings:
  - `routing_key_responsaveis_documentos`
  - `routing_key_diretoria_documentos`

## Fluxo

1. O usuário faz upload ou substituição de documento.
2. O controller chama o service e salva o documento.
3. O `AvisoProducer` monta o evento `DocumentoAtualizadoMessage`.
4. O produtor publica o evento para duas filas:
   - responsáveis, com e-mail pedindo validação do documento
   - diretoria, com e-mail avisando que a informação foi atualizada
5. Cada consumer recebe a mensagem e envia o e-mail correspondente por um worker específico.
6. O backend Java continua sem enviar e-mail diretamente.

## Vantagens

- menor complexidade do que três filas
- separação clara entre público responsável e diretoria
- cada fila tem sua própria intenção e texto específico
- mantém o backend desacoplado do envio real de e-mail

## Observações

- a fila de responsáveis tem foco em revisão/validação
- a fila da diretoria tem foco em acompanhamento e notificação
- o envio final de e-mail fica para um worker externo de entrega, e não para o Spring
