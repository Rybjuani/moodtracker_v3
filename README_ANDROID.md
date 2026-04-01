# MoodTracker Android

La aplicación incluye una interfaz móvil en `Kivy` para Android y mantiene la UI original de escritorio en `tkinter`.

## Archivos clave

- `moodtracker.py`: entrada principal con detección de plataforma.
- `main.py`: punto de entrada usado por `buildozer`.
- `buildozer.spec`: configuración del empaquetado Android.
- `.github/workflows/build-android.yml`: workflow para generar el APK en GitHub Actions.

## Generar un único APK en GitHub

1. Sube este proyecto a un repositorio de GitHub.
2. Asegúrate de que la rama principal sea `main`.
3. En GitHub, abre `Actions` y ejecuta `Build Android APK`, o haz push a `main`.
4. Al terminar, descarga el artefacto `moodtracker-apk`.

Ese artefacto contiene un único archivo `.apk` listo para compartir e instalar.

## Compilación local

```bash
buildozer android debug
```

El APK quedará en `bin/`.

## Notas

- En Android se conserva el registro de estados, promedio del día, últimos registros e historial por registros, día, semana y mes.
- El botón `Inicio auto` informa la limitación, porque Android no ofrece un equivalente directo al autostart de escritorio para esta app empaquetada.
- La configuración actual genera APK para `arm64-v8a`, que cubre la mayoría de los teléfonos Android modernos.
