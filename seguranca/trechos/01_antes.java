public class JwtUtil {

    private static final String SECRET = "segredo-super-seguro-seguro-123456";

    private static final Key KEY = Keys.hmacShaKeyFor(SECRET.getBytes());

