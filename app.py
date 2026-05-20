"""
app.py — Backend PetShop GT Website
Flask + Google Sheets CRM + Twilio WhatsApp + Google Calendar
"""
import os, json
from pathlib import Path
from datetime import datetime, date
from flask import Flask, jsonify, request, render_template, send_from_directory
from dotenv import load_dotenv

load_dotenv()
BASE = Path(__file__).parent
app  = Flask(__name__, template_folder="templates", static_folder="static")

ADMIN_PHONE = os.getenv("ADMIN_WHATSAPP", "whatsapp:+50254626994")
ADMIN_PASS  = os.getenv("ADMIN_PASSWORD", "petshop2025")


# ══════════════════════════════════════════════════════════════
# PÁGINAS
# ══════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/admin")
def admin():
    return render_template("admin.html")


# ══════════════════════════════════════════════════════════════
# API — MASCOTAS
# ══════════════════════════════════════════════════════════════

@app.route("/api/mascotas")
def api_mascotas():
    try:
        from sheets_crm import get_mascotas
        return jsonify({"ok": True, "mascotas": get_mascotas()})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/mascotas", methods=["POST"])
def api_mascotas_create():
    try:
        from sheets_crm import add_mascota
        d   = request.json or {}
        mid = add_mascota(d)
        return jsonify({"ok": True, "id": mid})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/mascotas/<mid>", methods=["PUT"])
def api_mascotas_update(mid):
    try:
        from sheets_crm import update_mascota
        ok = update_mascota(mid, request.json or {})
        return jsonify({"ok": ok})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/mascotas/<mid>/foto", methods=["POST"])
def api_mascota_foto(mid):
    """Sube foto de mascota al servidor."""
    if "foto" not in request.files:
        return jsonify({"ok": False, "error": "Sin archivo"}), 400
    f    = request.files["foto"]
    ext  = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else "jpg"
    name = f"{mid}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
    path = BASE / "static" / "mascotas" / name
    f.save(str(path))
    return jsonify({"ok": True, "url": f"/static/mascotas/{name}"})


# ══════════════════════════════════════════════════════════════
# API — CITAS
# ══════════════════════════════════════════════════════════════

@app.route("/api/disponibilidad")
def api_disponibilidad():
    fecha    = request.args.get("fecha", str(date.today()))
    servicio = request.args.get("servicio")
    try:
        from sheets_crm import get_disponibilidad
        slots = get_disponibilidad(fecha, servicio)
        return jsonify({"ok": True, "slots": slots})
    except Exception as e:
        # Fallback con slots por defecto
        slots = [{"hora": h, "disponible": True}
                 for h in ["08:00","09:00","10:00","11:00","14:00","15:00","16:00"]]
        return jsonify({"ok": True, "slots": slots, "fallback": True})


@app.route("/api/citas", methods=["POST"])
def api_citas_create():
    try:
        from sheets_crm import save_cita
        d   = request.json or {}
        cid = save_cita(d)

        # Notifica al admin por WhatsApp
        _notificar_admin_cita(cid, d)

        # Agrega a Google Calendar
        _crear_evento_calendar(cid, d)

        return jsonify({"ok": True, "id": cid})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/citas")
def api_citas_list():
    try:
        from sheets_crm import get_citas
        fecha = request.args.get("fecha")
        return jsonify({"ok": True, "citas": get_citas(fecha)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/citas/<cid>/estado", methods=["PUT"])
def api_cita_estado(cid):
    try:
        from sheets_crm import get_spreadsheet
        ws   = get_spreadsheet().worksheet("Citas")
        rows = ws.get_all_records()
        for i, r in enumerate(rows):
            if r.get("ID") == cid:
                headers = ws.row_values(1)
                ws.update_cell(i + 2, headers.index("Estado") + 1,
                               (request.json or {}).get("estado", "Confirmada"))
                return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Cita no encontrada"}), 404
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ══════════════════════════════════════════════════════════════
# API — CRM CONTACTOS
# ══════════════════════════════════════════════════════════════

@app.route("/api/contacto", methods=["POST"])
def api_contacto():
    try:
        from sheets_crm import save_contacto
        d   = request.json or {}
        cid = save_contacto(d)
        _notificar_admin_contacto(d)
        return jsonify({"ok": True, "id": cid})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/contactos")
def api_contactos_list():
    try:
        from sheets_crm import get_contactos
        return jsonify({"ok": True, "contactos": get_contactos()})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ══════════════════════════════════════════════════════════════
# NOTIFICACIONES WHATSAPP AL ADMIN
# ══════════════════════════════════════════════════════════════

def _notificar_admin_cita(cid: str, d: dict):
    try:
        from twilio.rest import Client
        sid    = os.getenv("TWILIO_ACCOUNT_SID")
        token  = os.getenv("TWILIO_AUTH_TOKEN")
        from_n = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
        if not sid or not token:
            return
        client = Client(sid, token)
        to     = ADMIN_PHONE if ADMIN_PHONE.startswith("whatsapp:") else f"whatsapp:{ADMIN_PHONE}"
        body   = (
            f"🐾 *Nueva Cita Agendada — PetShop GT*\n\n"
            f"📋 ID: {cid}\n"
            f"👤 Cliente: {d.get('nombre', '—')}\n"
            f"📞 Teléfono: {d.get('telefono', '—')}\n"
            f"🐶 Interés: {d.get('mascota_interes', '—')}\n"
            f"🔧 Servicio: {d.get('servicio', '—')}\n"
            f"📅 Fecha: {d.get('fecha_cita', '—')}\n"
            f"⏰ Hora: {d.get('hora_cita', '—')}\n"
            f"{('📝 ' + d['notas']) if d.get('notas') else ''}"
        )
        client.messages.create(from_=from_n, to=to, body=body.strip())
    except Exception as e:
        print(f"[WhatsApp admin cita] {e}")


def _notificar_admin_contacto(d: dict):
    try:
        from twilio.rest import Client
        sid    = os.getenv("TWILIO_ACCOUNT_SID")
        token  = os.getenv("TWILIO_AUTH_TOKEN")
        from_n = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
        if not sid or not token:
            return
        client = Client(sid, token)
        to     = ADMIN_PHONE if ADMIN_PHONE.startswith("whatsapp:") else f"whatsapp:{ADMIN_PHONE}"
        body   = (
            f"📬 *Nuevo Contacto Web — PetShop GT*\n\n"
            f"👤 {d.get('nombre','')} {d.get('apellido','')}\n"
            f"📞 {d.get('telefono', '—')}\n"
            f"🐶 Interés: {d.get('raza_interes', '—')}\n"
            f"✉️ {d.get('email', '—')}\n"
            f"💬 {d.get('mensaje', '—')}"
        )
        client.messages.create(from_=from_n, to=to, body=body.strip())
    except Exception as e:
        print(f"[WhatsApp admin contacto] {e}")


# ══════════════════════════════════════════════════════════════
# GOOGLE CALENDAR
# ══════════════════════════════════════════════════════════════

CALENDAR_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyQY5bKvVj5IHeIc9FuFY1cx74H8CArga0X-j2QRpl726sVHmJihF4hdbAQ7a_oAJZd/exec"

def _crear_evento_calendar(cid: str, d: dict):
    try:
        import requests as _req
        payload = {
            "nombre_dueno":   d.get("nombre", "Cliente"),
            "telefono":       d.get("telefono", ""),
            "nombre_mascota": d.get("mascota_interes", "Mascota"),
            "especie":        "Mascota",
            "servicio":       d.get("servicio", "Cita"),
            "fecha":          d.get("fecha_cita", str(date.today())),
            "hora":           d.get("hora_cita", "09:00"),
            "notas":          f"ID:{cid} | Email:{d.get('email','')} | {d.get('notas','')}".strip(" |"),
        }
        _req.post(CALENDAR_SCRIPT_URL, json=payload, timeout=15)
    except Exception as e:
        print(f"[Google Calendar] {e}")


# ══════════════════════════════════════════════════════════════
# ADMIN AUTH
# ══════════════════════════════════════════════════════════════

@app.route("/api/admin/login", methods=["POST"])
def api_admin_login():
    d = request.json or {}
    if d.get("password") == ADMIN_PASS:
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Contraseña incorrecta"}), 401


# ══════════════════════════════════════════════════════════════
# INICIAR
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print()
    print("=" * 52)
    print("  PetShop GT — Website")
    print("  http://localhost:5001")
    print("=" * 52)
    print()
    app.run(debug=False, port=5001, use_reloader=False)
