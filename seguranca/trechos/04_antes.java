        }

        String header = request.getHeader("Authorization");

        // debug
        System.out.println("HEADER: " + header);

        if (header == null || !header.startsWith("Bearer ")) {
            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            return;
        }
