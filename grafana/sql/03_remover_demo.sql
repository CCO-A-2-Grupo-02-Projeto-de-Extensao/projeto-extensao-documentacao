USE clube_tamoios;

DELETE pr FROM presenca pr
JOIN chamada c ON c.idChamada = pr.Chamada_idChamada
WHERE c.titulo LIKE '[demo]%';

DELETE FROM chamada WHERE titulo LIKE '[demo]%';

DELETE FROM evento WHERE descricao = '[demo-grafana]';
