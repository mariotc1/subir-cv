4. Sistema de Subida de CVs

Descripción

El usuario se registra, inicia sesión y puede subir un archivo PDF con su currículum que se almacena en el servidor. Cada usuario tiene su propio CV (uno por usuario o uno “actual” que se reemplaza).

Registro y login

Cumplir los requisitos comunes de registro y login.
Solo usuarios autenticados pueden subir, ver o descargar su CV.
Funcionalidad específica

Subir CV: formulario con input type="file"; guardar el archivo en el servidor (carpeta segura dentro de /backend) y guardar en BD la ruta o nombre de archivo asociado al user_id.
Descargar / ver mi CV: el usuario solo puede descargar o ver su propio archivo; comprobar siempre user_id antes de servir el fichero.
Modelo de datos (ejemplo)

usuarios: id, email (o username), password, created_at.
cvs: id, user_id (FK único o con lógica “solo uno activo”), nombre_archivo o ruta, subido_at.
Especificaciones técnicas

Validar en backend: solo archivos PDF, verificar que el archivo es un PDF y que el tamaño es razonable.
Al servir el archivo, comprobar autenticación y que el recurso pertenece al usuario.
Checklist de supervivencia (recordatorio)

Antes de entregar, comprobar en todos los proyectos:

 Validación: formularios vacíos o datos inválidos se rechazan en backend con mensajes claros.
 Autenticación: no se puede acceder a rutas protegidas solo escribiendo la URL sin estar logueado.
 Autorización: cada usuario solo accede a sus propios recursos (notas, mensajes propios, productos propios, su CV).
 Reducción de información: las respuestas no incluyen campos innecesarios ni sensibles (hashes, rutas internas).
 Control de errores: los fallos devuelven mensajes amigables y códigos HTTP adecuados, sin stack traces ni rutas del sistema.