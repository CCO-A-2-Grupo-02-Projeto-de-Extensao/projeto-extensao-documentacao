public class JwtUtil {

    // Em produção o segredo vem da variável de ambiente JWT_SECRET, injetada pelo
    // script de infraestrutura. O valor abaixo serve só para rodar localmente sem
    // precisar configurar nada.
    private static final String SECRET_PADRAO_DEV =
            "dev-local-somente-nao-usar-em-producao-1234567890";

    private static final String SECRET = resolverSecret();

    private static final Key KEY = Keys.hmacShaKeyFor(SECRET.getBytes());

    private static String resolverSecret() {
        String env = System.getenv("JWT_SECRET");
        if (env != null && !env.isBlank()) {
            return env;
        }
        System.err.println("AVISO: JWT_SECRET não definido, usando o segredo de desenvolvimento");
        return SECRET_PADRAO_DEV;
