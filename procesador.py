import pandas as pd
import numpy as np
import re
import unicodedata
from gensim.models import Word2Vec
from sklearn.metrics.pairwise import cosine_similarity

# Lectura de catálogos directamente aquí
df_cie9 = pd.read_excel('PROCEDIMIENTO_202402.xlsx').iloc[:, [2,3]].copy()
df_cie9.columns = ['CODIGO', 'DESCRIPCION']

df_cie10 = pd.read_excel('catalogo_cie10.xlsx').iloc[:, [1,2]].copy()
df_cie10.columns = ['CODIGO', 'DESCRIPCION']

def normalizar_texto(texto):
    if not isinstance(texto, str):
        return ""
    texto = texto.lower()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    texto = re.sub(r'[^a-z0-9\s]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def safe_cosine_similarity(vector, vectores_catalogo):
    if np.isnan(vector).any() or np.isnan(vectores_catalogo).any():
        return np.zeros(len(vectores_catalogo))
    if vectores_catalogo.shape[0] == 0:
        return np.zeros(1)
    return cosine_similarity([vector], vectores_catalogo)[0]

def entrenar_word2vec(corpus):
    modelo = Word2Vec(sentences=corpus, vector_size=50, window=5, min_count=1, workers=2, sg=1)
    return modelo

def generar_vectores(textos, modelo):
    vectores = []
    for texto in textos:
        palabras = texto.split()
        palabras_validas = [p for p in palabras if p in modelo.wv]
        if palabras_validas:
            vectores.append(np.mean([modelo.wv[p] for p in palabras_validas], axis=0))
        else:
            vectores.append(np.zeros(modelo.vector_size))
    return np.array(vectores)

def mapear_columna(df, catalogo, columna_datos, nombre_codigo, nombre_descripcion, nombre_similitud):
    df['texto_normalizado'] = df[columna_datos].apply(normalizar_texto)
    catalogo['texto_normalizado'] = catalogo['DESCRIPCION'].apply(normalizar_texto)

    corpus = [t.split() for t in df['texto_normalizado']] + [t.split() for t in catalogo['texto_normalizado']]
    modelo = entrenar_word2vec(corpus)

    vectores_datos = generar_vectores(df['texto_normalizado'], modelo)
    vectores_catalogo = generar_vectores(catalogo['texto_normalizado'], modelo)

    codigos = []
    descripciones = []
    similitudes = []

    for vector in vectores_datos:
        semejanzas = safe_cosine_similarity(vector, vectores_catalogo)
        idx = np.argmax(semejanzas)
        max_similitud = semejanzas[idx]

        if max_similitud >= 0.7:
            codigos.append(catalogo.iloc[idx]['CODIGO'])
            descripciones.append(catalogo.iloc[idx]['DESCRIPCION'])
        else:
            codigos.append('NO_ENCONTRADO')
            descripciones.append('Revisión manual')
        similitudes.append(round(float(max_similitud), 4))

    df[nombre_codigo] = codigos
    df[nombre_descripcion] = descripciones
    df[nombre_similitud] = similitudes

    return df

def procesar_archivo_excel(df):
    df = mapear_columna(df, df_cie9, 'CIRUGIA_REALIZADA', 'CODIGO_CIE9', 'DESCRIPCION_CIE9', 'SIMILITUD_CIE9')
    df = mapear_columna(df, df_cie10, 'DIAGNOSTICO', 'CODIGO_CIE10', 'DESCRIPCION_CIE10', 'SIMILITUD_CIE10')

    total = len(df)
    cie9_codificados = df['CODIGO_CIE9'].ne('NO_ENCONTRADO').sum()
    cie10_codificados = df['CODIGO_CIE10'].ne('NO_ENCONTRADO').sum()

    resumen = {
        'total': total,
        'cie9_codificados': cie9_codificados,
        'cie9_pendientes': total - cie9_codificados,
        'cie10_codificados': cie10_codificados,
        'cie10_pendientes': total - cie10_codificados,
        'cie9_porcentaje': round((cie9_codificados/total)*100, 2),
        'cie10_porcentaje': round((cie10_codificados/total)*100, 2)
    }

    return df, resumen