## ADDED Requirements

### Requirement: Parsear código SYSTEL de 13 dígitos
El sistema SHALL extraer el PLU y el peso en kilogramos desde un string de exactamente 13 dígitos que siga el formato SYSTEL.

#### Scenario: Código válido con peso entero
- **WHEN** se recibe el código `"2000270048052"`
- **THEN** el parser SHALL retornar `{ plu: "00027", pesoKg: 4.805 }`

#### Scenario: Código válido con peso pequeño
- **WHEN** se recibe el código `"2000270001005"`
- **THEN** el parser SHALL retornar `{ plu: "00027", pesoKg: 0.1 }`

#### Scenario: Código válido con peso máximo
- **WHEN** se recibe el código `"2999999999995"`
- **THEN** el parser SHALL retornar `{ plu: "99999", pesoKg: 99999.999 }`

#### Scenario: Código con longitud distinta a 13 dígitos
- **WHEN** se recibe un string de longitud menor o mayor a 13 dígitos
- **THEN** el parser SHALL retornar un error indicando longitud inválida

#### Scenario: Código con caracteres no numéricos
- **WHEN** se recibe un string que contenga letras, símbolos o espacios
- **THEN** el parser SHALL retornar un error indicando formato numérico inválido

#### Scenario: Código con prefijo distinto a 2
- **WHEN** se recibe un string de 13 dígitos cuyo primer carácter no sea `"2"`
- **THEN** el parser SHALL retornar un error indicando prefijo de producto pesado inválido
