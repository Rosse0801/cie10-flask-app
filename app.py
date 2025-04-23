from flask import Flask, render_template, request, send_file, flash, redirect, url_for
import pandas as pd
from procesador import procesar_archivo_excel
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'clave-super-secreta'

# Variable global temporal
archivo_procesado = None
nombre_archivo_resultado = "resultado_codificado.xlsx"
resumen_final = None

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    global archivo_procesado, resumen_final

    if request.method == 'POST':
        file = request.files.get('archivo')
        if not file or file.filename == '':
            flash('No seleccionaste ningún archivo')
            return redirect(url_for('upload_file'))

        df = pd.read_excel(file)

        df_resultado, resumen = procesar_archivo_excel(df)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_resultado.to_excel(writer, index=False, sheet_name='Resultado')
        output.seek(0)

        # Guardamos en memoria temporal
        archivo_procesado = output
        resumen_final = resumen

        return render_template('upload.html', resumen=resumen)

    return render_template('upload.html', resumen=None)

@app.route('/descargar')
def descargar_archivo():
    global archivo_procesado
    if archivo_procesado is None:
        return redirect(url_for('upload_file'))

    return send_file(
        archivo_procesado,
        as_attachment=True,
        download_name=nombre_archivo_resultado,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if __name__ == '__main__':
    app.run(debug=True)
    