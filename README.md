# Analizador de Artículos V3

Aplicación de escritorio (Tkinter) para analizar artículos científicos en PDF con la API de OpenAI y generar un documento Word (.docx) con el resumen estructurado.

## Requisitos

```
pip install -r requirements.txt
```

Configura tu clave en la variable de entorno `OPENAI_API_KEY` o introdúcela directamente en la interfaz.

Puedes crear un archivo `.env` (opcional):

```
OPENAI_API_KEY=tu_api_key
```

## Uso (GUI)

```
python app.py
```

1. Selecciona un PDF o una carpeta con PDFs.
2. (Opcional) Elige carpeta de salida.
3. (Opcional) Ingresa tu `OPENAI_API_KEY` o pulsa "Usar ENV".
4. Pulsa "Analizar". Se generará un `.docx` por cada PDF.

## Estructura

```
.
├─ analyzer.py      # Lógica de extracción, análisis y exportación
├─ gui.py           # Interfaz de usuario Tkinter
├─ app.py           # Punto de entrada (GUI)
├─ cli.py           # Modo batch por línea de comandos (opcional)
└─ requirements.txt # Dependencias
```

## Notas

- Tkinter viene con la instalación estándar de Python (no requiere pip).
- Se utiliza PyMuPDF para extraer texto de PDFs y python-docx para generar el Word.
- El modelo por defecto es `gpt-4o-2024-08-06`. Puedes ajustarlo en la GUI o en `analyzer.py`.
- Llamada única a OpenAI por archivo con salida JSON (menos coste/latencia).
- Búsqueda de PDFs recursiva en subcarpetas.

### OCR opcional

Si el PDF es escaneado (sin texto extraíble), se intentará un OCR si están disponibles las dependencias:

- `pytesseract`, `Pillow`, `pdf2image`
- Requiere Tesseract y Poppler instalados en el sistema (no incluidos por pip).

Si no están instalados, el programa seguirá sin OCR.

### Modo CLI (batch)

```
python cli.py --in "carpeta_o_pdf" --out "salida" \
  --model gpt-4o-2024-08-06 --max-output-tokens 1200 --temperature 0.2
```

### Estimación de coste

La interfaz muestra una estimación aproximada de tokens de entrada/salida (entrada ≈ bytes/4). Es un valor orientativo.

