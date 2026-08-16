  // Limpa a sessão antes de sair: sem isto o token continua no localStorage e
  // basta voltar para /dashboard para entrar de novo.
  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("usuario");
    navigate("/", { replace: true });
  };


  // ...no item da sidebar:
            onClick={handleLogout}
