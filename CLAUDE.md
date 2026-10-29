# CLAUDE.md — petshopgt502.com (PetShop GT)

Sitio de PetShop GT, tienda de mascotas familiar en Boulevard Vista Hermosa 2, 22-74, Zona 15, Ciudad de Guatemala.
Objetivo: **convertir visitas en conversaciones por WhatsApp y citas** (conocer mascota, grooming, consulta, vacunas).

## Stack y despliegue
- Una sola página estática: `index.html` (CSS y JS en línea). GitHub Pages desde `main`, dominio `www.petshopgt502.com` (`CNAME`, no tocar).
- **Todo push a `main` se publica en minutos.** Trabajar en rama (`fase-N-…`) y fusionar solo cuando el dueño diga «publica».
- `_config.yml` (Jekyll) excluye del sitio publicado el backend (`app.py`, `*.py`) y los originales pesados. No volver a crear `.nojekyll`: publicaría todo.
- `app.py` (Flask + Sheets + Twilio) **no corre en GitHub Pages**. Nada del sitio debe depender de `/api/...`.
- Imágenes: el sitio usa solo `static/web/*.webp` (800 px mascotas, 1200 px hero, 700 px galería) y `static/web/og-petshop-gt.jpg` (1200×630). Originales en `static/images/mascotas/`, `static/mascotas/`, `static/images/clientes satisfechos/` (no se publican).
- Contacto: WhatsApp `wa.me/50254626994`. El formulario abre WhatsApp con los datos escritos (no hay servidor). Agenda: Google Calendar.

## Reglas
1. No inventar datos (años, certificaciones, precios, testimonios, razas disponibles). Si falta: preguntar.
2. Fotos de mascotas: reales de la tienda (confirmado por el dueño).
3. Pendiente de confirmar: la certificación «Pedigree A+ de la Asociación Canina de Guatemala».
4. Cada `<img>` con `alt`; `loading="lazy"` salvo el hero. Página: 1 `<h1>`, title ≤ 65, description 140–160, canonical, Open Graph, JSON-LD `PetStore`.
5. Probar en móvil (390 px) y escritorio (1440 px): sin desborde horizontal, sin errores de JS.
