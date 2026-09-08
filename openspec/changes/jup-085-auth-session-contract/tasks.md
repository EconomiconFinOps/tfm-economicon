## 1. Contrato y configuracion

- [x] 1.1 JUP-085 inventariar el login, `/me`, JWT y almacenamiento frontend heredados.
- [x] 1.2 JUP-085 definir request, response, claims, TTL, errores y limites de la auth demo.
- [ ] 1.3 JUP-085 alinear seed, ejemplos y configuracion con una unica politica de credenciales demo.

## 2. Backend y frontend

- [ ] 2.1 JUP-085 validar password no vacio y clasificar token ausente, invalido y expirado sin filtraciones.
- [ ] 2.2 JUP-085 limpiar sesion, tenant y cache cuando el usuario hace logout o recibe un `401` de sesion.
- [ ] 2.3 JUP-085 impedir secretos versionados o variables de firma accesibles al frontend.

## 3. Verificacion

- [ ] 3.1 JUP-085 cubrir login, perfil, expiracion, usuario ausente y logout con pruebas backend/frontend.
- [ ] 3.2 JUP-085 ejecutar lint, tests, build, OpenSpec y trazabilidad JUP.
- [ ] 3.3 JUP-085 publicar PR, evidencia funcional y revision del equipo.
