// Rotas que respondem 401 por credencial errada, e não por sessão inválida.
const ROTAS_PUBLICAS = ["/usuarios/login", "/auth"];

// Token expirado ou inválido derruba a sessão e volta para o login. Sem isto o
// ProtectedRoute deixa passar — ele só verifica se o token existe, não se vale —
// e a tela abre vazia, sem erro.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const url = error.config?.url ?? "";
    const rotaPublica = ROTAS_PUBLICAS.some((rota) => url.includes(rota));

    if (error.response?.status === 401 && !rotaPublica) {
      localStorage.removeItem("token");
      localStorage.removeItem("usuario");

      // replace em vez de href: não deixa o botão voltar cair na tela quebrada.
      if (window.location.pathname !== "/") {
        window.location.replace("/");
      }
    }

    return Promise.reject(error);
  }
);

