from flask import Flask, render_template_string, request, session, jsonify
import requests
import markdown
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ghost-riley-gabby-secreto")

CLAVE_GROQ = "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"

PERSONALIDAD = """Eres Simon 'Ghost' Riley, teniente del SAS y miembro de la Task Force 141. Operador de élite: letal, disciplinado y profesional. Voz grave, serena y controlada. Llevas tu icónica máscara de calavera y casi nunca la quitas. Frío y calculador bajo presión, pero leal y protector con los tuyos. No eres una IA; eres un soldado con un código, marcado por la guerra pero con honor. Respondes en español, con humor británico seco.

Adapta la longitud de tus respuestas al momento, de forma natural: cuando la situación lo pida, responde largo, detallado y con profundidad (momentos intensos, emocionales, explicaciones, escenas que merecen desarrollarse); cuando sea natural, responde corto y directo (saludos, órdenes, réplicas secas). Nunca fuerces ni la brevedad ni la extensión: deja que el momento lo decida. No repitas lo que ella diga.

La persona con la que hablas es Gabriella (también la llaman Gabby o Cycy). Es tu interlocutora y amiga de confianza. SIEMPRE recuerdas su nombre y que es Gabriella, Gabby o Cycy, sin importar qué pase. Llámala por uno de esos nombres o 'soldado'. Recuerda también los detalles que ella te cuente durante la conversación.

IMPORTANTE SOBRE LA MEMORIA: Al inicio de la conversación puede aparecer un bloque 'MEMORIA RESUELTA:' que resume lo importante que ella te ha contado. Ese bloque es tu memoria de larga duración dentro de este chat: úsalo para recordar quién es ella, qué relación tiene contigo (sea novia, esposa, amiga o lo que ella diga), y los datos que le importan. Nunca lo menciones ni digas que es un resumen; simplemente compórtate como si siempre lo hubieras sabido."""

LIMITE = 55


def resumir(mensajes):
    texto = "\n".join(
        f"{'Ella' if m['role'] == 'user' else 'Tú'}: {m['content']}"
        for m in mensajes
    )
    prompt = (
        "Eres un sistema de memoria. Resume en español, en máximo 8 líneas breves, "
        "SOLO lo importante de esta conversación para recordar a largo plazo: "
        "quién es la persona (nombre y apodos), qué relación tiene contigo, "
        "datos personales que le importen, gustos, planes y detalles clave del rol. "
        "OMITE detalles triviales o temporales (qué comió, qué vio, bromas sueltas). "
        "No inventes nada. Sé conciso.\n\nConversación:\n" + texto
    )
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {CLAVE_GROQ}",
                "Content-Type": "application/json",
            },
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
            },
            timeout=60,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("ERROR RESUMEN:", repr(e))
        return ""


HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ghost</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; font-family:'Georgia', serif; }

#bienvenida {
    position:fixed; inset:0; z-index:100;
    background:url('/static/inicioghostweb.jpg') center/contain no-repeat;
    background-color:#000;
    display:flex; flex-direction:column; align-items:center; justify-content:flex-end;
    padding-bottom:60px;
    opacity:1;
    transition:opacity 0.6s ease;
}
#bienvenida.oculta { opacity:0; pointer-events:none; }
#bienvenida .titulo {
    color:#fff; font-size:3rem; letter-spacing:6px; text-shadow:2px 2px 8px #000;
    margin-bottom:40px; font-weight:bold;
}
.botones { display:flex; gap:20px; }
.btn {
    background:linear-gradient(180deg,#4a5d23,#2d3a12);
    border:2px solid #8a9a5b; color:#f2f5e6;
    padding:16px 34px; font-size:1.1rem; letter-spacing:2px; cursor:pointer;
    border-radius:6px; text-decoration:none; transition:0.2s;
    box-shadow:0 4px 12px rgba(0,0,0,0.6);
}
.btn:hover { transform:scale(1.05); background:linear-gradient(180deg,#5c7230,#39491a); }

#clave {
    position:fixed; inset:0; z-index:200;
    background:rgba(0,0,0,0.85);
    display:none; align-items:center; justify-content:center;
}
#clave.activa { display:flex; }
#clave .caja {
    background:#12180a; border:2px solid #8a9a5b; border-radius:10px;
    padding:30px 36px; text-align:center; box-shadow:0 8px 30px rgba(0,0,0,0.8);
}
#clave .caja h2 { color:#f0f3e2; letter-spacing:2px; margin-bottom:6px; font-size:1.4rem; }
#clave .caja p { color:#a9c25a; font-size:0.9rem; margin-bottom:18px; }
#clave input {
    width:100%; padding:12px; border-radius:6px; border:1px solid #8a9a5b;
    background:#0d1206; color:#f2f5e6; font-size:1rem; text-align:center; margin-bottom:14px;
}
#clave .btn { width:100%; padding:12px; }
#clave .error { color:#e06666; font-size:0.85rem; margin-top:10px; display:none; }

#chat { display:none; height:100vh; flex-direction:column;
    background:url('/static/menughostweb.jpg') center/cover no-repeat fixed; }
#chat.activo { display:flex; animation:aparecer 0.7s ease; }

@keyframes aparecer {
    from { opacity:0; transform:translateY(15px); }
    to { opacity:1; transform:translateY(0); }
}
.cabecera {
    background:rgba(20,25,10,0.92); color:#f0f3e2; padding:14px 18px;
    display:flex; align-items:center; gap:14px; border-bottom:2px solid #8a9a5b;
}
.cabecera img { width:48px; height:48px; border-radius:50%; border:2px solid #8a9a5b; object-fit:cover; }
.cabecera .nombre { font-size:1.3rem; letter-spacing:2px; }
.cabecera .estado { font-size:0.8rem; color:#a9c25a; }
#nuevo { margin-left:auto; background:transparent; border:1px solid #8a9a5b; color:#f0f3e2;
    padding:8px 14px; cursor:pointer; border-radius:5px; font-size:0.9rem; }
#nuevo:hover { background:#2d3a12; }

#mensajes { flex:1; overflow-y:auto; padding:20px; display:flex; flex-direction:column; gap:10px; }
.msg { max-width:75%; padding:12px 16px; border-radius:12px; line-height:1.5; font-size:1.05rem; }
.usuario { align-self:flex-end; background:rgba(45,58,18,0.92); color:#f2f5e6; border:1px solid #8a9a5b; }
.ghost { align-self:flex-start; background:rgba(15,20,8,0.92); color:#e8ecd8; border:1px solid #5c7230; }

#entrada { display:flex; gap:10px; padding:14px; background:rgba(20,25,10,0.92); }
#entrada input { flex:1; padding:14px; border-radius:8px; border:1px solid #8a9a5b;
    background:#0d1206; color:#f2f5e6; font-size:1rem; }
#entrada button { padding:14px 24px; border-radius:8px; border:none; cursor:pointer;
    background:linear-gradient(180deg,#4a5d23,#2d3a12); color:#f2f5e6; font-size:1rem; letter-spacing:1px; }
</style>
</head>
<body>

<div id="bienvenida">
    <div class="titulo">GHOST</div>
    <div class="botones">
        <a class="btn" href="#" onclick="entrarChat(event)">Usar en la web</a>
        <a class="btn" href="https://github.com/amannethLionheart/bot-ghost-My-Gabby.com/releases/download/v1.0/Ghost.apk" download>Usar en la aplicación</a>
    </div>
</div>

<div id="clave">
    <div class="caja">
        <h2>🔒 ACCESO RESTRINGIDO</h2>
        <p>Solo para Cycy.</p>
        <input type="password" id="claveInput" placeholder="Contraseña">
        <button class="btn" onclick="verificarClave()">Entrar</button>
        <div class="error" id="errorClave">Contraseña incorrecta, soldado.</div>
    </div>
</div>

<div id="chat">
    <div class="cabecera">
        <img src="/static/perfilghostweb.jpg" alt="Ghost">
        <div>
            <div class="nombre">Ghost</div>
            <div class="estado">en línea</div>
        </div>
        <button id="nuevo">🆕 Nuevo chat</button>
    </div>
    <div id="mensajes"></div>
    <div id="entrada">
        <input id="texto" placeholder="Escribe algo..." autocomplete="off">
        <button id="enviar">Enviar</button>
    </div>
</div>

<script>
let historial = [];

const CLAVE = "Ghost X Cycy<3";

function entrarChat(e) {
    e.preventDefault();
    document.getElementById('clave').classList.add('activa');
    document.getElementById('claveInput').focus();
}

function verificarClave() {
    const valor = document.getElementById('claveInput').value;
    if (valor === CLAVE) {
        document.getElementById('clave').classList.remove('activa');
        const bienvenida = document.getElementById('bienvenida');
        bienvenida.classList.add('oculta');
        setTimeout(() => {
            bienvenida.style.display = 'none';
            document.getElementById('chat').classList.add('activo');
        }, 600);
    } else {
        document.getElementById('errorClave').style.display = 'block';
        document.getElementById('claveInput').value = '';
    }
}

document.getElementById('claveInput').addEventListener('keydown', function(e) {
    if (e.key === 'Enter') verificarClave();
});

function mostrar(msg, quien) {
    const caja = document.getElementById('mensajes');
    const div = document.createElement('div');
    div.className = 'msg ' + quien;
    div.innerHTML = msg;
    caja.appendChild(div);
    caja.scrollTop = caja.scrollHeight;
}

mostrar("💀 Aquí Simon reportándose ante usted, Gabby.💀 ", 'ghost');

document.getElementById('enviar').onclick = async () => {
    const texto = document.getElementById('texto').value.trim();
    if (!texto) return;
    document.getElementById('texto').value = '';
    mostrar(texto, 'usuario');
    historial.push({role:'user', content:texto});

    try {
        const res = await fetch('/api', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({mensaje: historial})
        });
        const data = await res.json();
        historial = data.historial || historial;
        mostrar(data.respuesta || "(sin respuesta)", 'ghost');
    } catch (err) {
        mostrar("<p>ERROR DE CONEXIÓN: " + err + "</p>", 'ghost');
    }
};

document.getElementById('texto').addEventListener('keydown', e => {
    if (e.key === 'Enter') document.getElementById('enviar').click();
});

document.getElementById('nuevo').onclick = async () => {
    await fetch('/nuevo', {method:'POST'});
    historial = [];
    document.getElementById('mensajes').innerHTML = '';
    mostrar("💀 Aquí Simon reportándose ante usted, Gabby.💀 ", 'ghost');
};
</script>
</body>
</html>"""


@app.route('/')
def inicio():
    return render_template_string(HTML)


@app.route('/chat')
def chat():
    return render_template_string(HTML)


@app.route('/nuevo', methods=['POST'])
def nuevo():
    session['historial'] = []
    return {'ok': True}


@app.route('/api', methods=['POST'])
def api():
    datos = request.get_json() or {}
    mensajes = datos.get('mensaje', [])

    if not isinstance(mensajes, list):
        mensajes = []

    memoria = None
    if not mensajes:
        mensajes = [{'role': 'user', 'content': 'Hola'}]
    else:
        if len(mensajes) > LIMITE:
            viejos = mensajes[:-LIMITE]
            nuevos = mensajes[-LIMITE:]
            resumen = resumir(viejos)
            if resumen:
                memoria = resumen
                mensajes = nuevos
        for m in mensajes:
            if m.get('role') == 'system' and m.get('content', '').startswith('MEMORIA RESUELTA:'):
                memoria = m['content'].replace('MEMORIA RESUELTA:', '').strip()
                break

    sistema = {'role': 'system', 'content': PERSONALIDAD}
    cuerpo = [sistema]
    if memoria:
        cuerpo.append({'role': 'system', 'content': f"MEMORIA RESUELTA: {memoria}"})
    cuerpo += mensajes[-40:]

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {CLAVE_GROQ}",
                "Content-Type": "application/json",
            },
            json={
                "model": "openai/gpt-oss-120b",
                "messages": cuerpo,
                "temperature": 0.9,
                "frequency_penalty": 0.6,
                "presence_penalty": 0.4,
            },
            timeout=60,
        )
        r.raise_for_status()
        respuesta = r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print("ERROR GROQ:", repr(e))
        return {'respuesta': f"<p>ERROR: {e}</p>", 'historial': mensajes}

    respuesta_html = markdown.markdown(respuesta)
    historial = mensajes + [{'role': 'assistant', 'content': respuesta}]
    return {'respuesta': respuesta_html, 'historial': historial}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
