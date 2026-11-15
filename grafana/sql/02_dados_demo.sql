USE {{banco_sistema}};

INSERT INTO evento (nome, tipo, data_inicio, data_fim, descricao)
WITH RECURSIVE sabados AS (
    SELECT DATE('2026-02-07') AS dia
    UNION ALL
    SELECT dia + INTERVAL 7 DAY FROM sabados WHERE dia + INTERVAL 7 DAY <= CURDATE()
)
SELECT 'Reunião', 'Reunião', s.dia, s.dia, '[demo-grafana]'
FROM sabados s
WHERE NOT EXISTS (SELECT 1 FROM evento e WHERE e.tipo = 'Reunião' AND e.data_inicio = s.dia);

INSERT INTO chamada (data_chamada, titulo, Evento_idEvento)
SELECT e.data_inicio, CONCAT('[demo] Chamada - ', DATE_FORMAT(e.data_inicio, '%d/%m/%Y')), MIN(e.idEvento)
FROM evento e
WHERE e.tipo = 'Reunião'
  AND e.data_inicio BETWEEN '2026-02-07' AND CURDATE()
  AND NOT EXISTS (SELECT 1 FROM chamada c WHERE c.data_chamada = e.data_inicio)
GROUP BY e.data_inicio;

INSERT INTO presenca (presenca, Chamada_idChamada, Pessoa_idPessoa)
SELECT
    RAND(c.idChamada * 1000 + p.idPessoa) < GREATEST(0.2,
        0.95
        - (p.idPessoa % 7) * 0.04
        - CASE WHEN f.chuva_mm >= 10 THEN 0.25 WHEN f.chuva_mm >= 2 THEN 0.10 ELSE 0 END
        - CASE WHEN f.feriado_prolongado THEN 0.30 ELSE 0 END),
    c.idChamada,
    p.idPessoa
FROM chamada c
JOIN Pessoa p ON p.ativo = 1
JOIN Cargo cg ON cg.idCargo = p.fkCargo AND cg.Nome = 'Desbravador'
LEFT JOIN arandu_analise.fatores_dia f ON f.dia = c.data_chamada
WHERE c.titulo LIKE '[demo]%'
  AND NOT EXISTS (SELECT 1 FROM presenca x WHERE x.Chamada_idChamada = c.idChamada);
