## ADDED Requirements

### Requirement: Importar productos desde Excel QUENDRA
El sistema SHALL permitir la importación masiva de productos desde archivos Excel con formato QUENDRA.

#### Scenario: Importación con preview exitosa
- **WHEN** un usuario autenticado envía POST /productos/import con un archivo .xlsx válido
- **THEN** el sistema parsea el archivo, genera una vista previa con filas válidas e inválidas, detecta duplicados de PLU contra la base existente, y devuelve el preview sin persistir aún

#### Scenario: Confirmar importación desde preview
- **WHEN** un usuario confirma la importación enviando POST /productos/import/confirm con el ID de sesión de preview
- **THEN** el sistema persiste solo las filas válidas, ignora las inválidas, y devuelve un resumen con cantidad creados, omitidos y errores

#### Scenario: Formato de archivo inválido
- **WHEN** un usuario envía un archivo que no es .xlsx
- **THEN** el sistema rechaza con 415 Unsupported Media Type

### Requirement: Detectar duplicados en importación
El sistema SHALL detectar PLUs duplicados tanto dentro del archivo como contra la base de datos existente.

#### Scenario: PLU duplicado en el archivo
- **WHEN** el archivo Excel contiene dos filas con el mismo PLU
- **THEN** el sistema marca la segunda ocurrencia como inválida en el preview con error "PLU duplicado en archivo"

#### Scenario: PLU ya existente en la empresa
- **WHEN** el archivo contiene un PLU que ya existe para la empresa autenticada
- **THEN** el sistema marca esa fila como inválida en el preview con error "PLU ya existe en la empresa"

### Requirement: Validar formato de filas en importación
El sistema SHALL validar el formato de cada fila del Excel y reportar errores específicos.

#### Scenario: Fila con precio inválido
- **WHEN** una fila del Excel tiene precio_publico como texto no numérico
- **THEN** el sistema marca la fila como inválida con error "precio_publico debe ser numérico"

#### Scenario: Fila con nombre vacío
- **WHEN** una fila del Excel tiene nombre vacío o ausente
- **THEN** el sistema marca la fila como inválida con error "nombre es obligatorio"

#### Scenario: Categoría inexistente
- **WHEN** una fila del Excel referencia una categoría que no existe en la empresa
- **THEN** el sistema marca la fila como inválida con error "categoría no encontrada"

### Requirement: Mapeo de columnas QUENDRA
El sistema SHALL interpretar las columnas estándar de exportación QUENDRA.

#### Scenario: Mapeo correcto de columnas
- **WHEN** el archivo tiene columnas: PLU, Nombre, Categoria, Precio_Publico, Precio_Mayorista, Costo_Kilo, Stock_Actual, Stock_Minimo
- **THEN** el sistema mapea cada columna al campo correspondiente del producto

### Requirement: Límite de filas en importación
El sistema SHALL limitar la cantidad de filas procesables en una sola importación.

#### Scenario: Archivo con más de 5000 filas
- **WHEN** un usuario envía un archivo con más de 5000 filas de datos
- **THEN** el sistema rechaza la operación con 413 Payload Too Large y mensaje "Máximo 5000 filas por importación"
