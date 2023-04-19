from tkinter import filedialog, messagebox
from tkcalendar import DateEntry

from app.settings import RUTA_INSUMOS, RUTA_RAIZ, RUTA_RESULTADOS
from app.classes.lectura_pandas import LecturaMercadoPago, LecturaMercadoLibre, LecturaEnterprise
from app.classes.procesamiento_archivos import ejecutar_procesamiento

import pandas as pd
import tkinter as tk
import shutil
import os

#ejecutar_procesamiento()


root = tk.Tk()
root.resizable(False, False)
root.configure(background = "white")
root.minsize(800, 600)

root.grid_columnconfigure(0, pad=20)
root.grid_rowconfigure(0, pad=20)

df_ML = pd.DataFrame()
df_MP = pd.DataFrame()
df_ET = pd.DataFrame()

ruta_ML = ""
ruta_MP = ""
ruta_ET = ""
ruta_resultados = ""



def copiar_archivo_a_insumos(ruta_archivo: str):

    shutil.copy(ruta_archivo, RUTA_INSUMOS)


def eliminar_archivo_de_insumos(ruta_archivo: str):
    nombre_archivo = ruta_archivo.split('/')[-1]
    print(ruta_archivo)
    print(f'{RUTA_INSUMOS}\\{nombre_archivo}')
    os.remove(f'{RUTA_INSUMOS}\\{nombre_archivo}')


def seleccionar_archivo_mercado_libre(label_ml):

    archivo = filedialog.askopenfilename(title="Seleccionar mercado libre", filetypes=[("Excel", "*.xlsx")])
    try:
        copiar_archivo_a_insumos(archivo)
        global df_ML, ruta_ML
        df_ML = LecturaMercadoLibre(errores=[]).leer_archivo()
        ruta_ML = archivo
        label_ml.config(text=archivo)
        check_files()
    except ValueError as e:
        eliminar_archivo_de_insumos(archivo)
        messagebox.showerror('Error', e)
    except Exception as e:
        eliminar_archivo_de_insumos(archivo)
        messagebox.showerror('Error', e)




# Definir una función para seleccionar el archivo 2
def seleccionar_archivo_mercado_pago(label):
    global cal_fecha_inicio, cal_fecha_final

    fecha_ini = cal_fecha_inicio.get_date().strftime('%Y-%m-%d')
    fecha_fin = cal_fecha_final.get_date().strftime('%Y-%m-%d')

    archivo = filedialog.askopenfilename(title="Seleccionar mercado pago", filetypes=[("Excel", "*.xlsx")])

    try:
        copiar_archivo_a_insumos(archivo)
        global df_MP, ruta_MP
        df_MP, _ = LecturaMercadoPago(errores=[], fecha_inicio=fecha_ini, fecha_fin=fecha_fin).leer_archivo()
        ruta_MP = archivo
        label.config(text=archivo)
        check_files()
    except ValueError as e:
        eliminar_archivo_de_insumos(archivo)
        print(e)
        messagebox.showerror('Error', e)
    except Exception as e:
        eliminar_archivo_de_insumos(archivo)
        print(e)
        messagebox.showerror('Error', e)


def seleccionar_archivo_enterprise(label):
    archivo = filedialog.askopenfilename(title="Seleccionar enterprise", filetypes=[("Excel", "*.xlsx"), ("Excel", "*.xls")])
    try:
        copiar_archivo_a_insumos(archivo)
        global df_ET, ruta_ET
        df_ET = LecturaEnterprise(errores=[]).leer_archivo()
        ruta_ET = archivo
        label.config(text=archivo)
        check_files()
    except ValueError as e:
        eliminar_archivo_de_insumos(archivo)
        messagebox.showerror('Error', e)
    except Exception as e:
        eliminar_archivo_de_insumos(archivo)
        messagebox.showerror('Error', e)

def check_files():
    global df_ML, df_MP, df_ET

    if df_ML.empty or df_MP.empty or df_ET.empty:
        boton_cruce.config(state='disabled')
    else:
        boton_cruce.config(state='normal')


def cruzar_archivos():
    global fecha_ini, fecha_fin

    fecha_ini = cal_fecha_inicio.get_date().strftime('%Y-%m-%d')
    fecha_fin = cal_fecha_final.get_date().strftime('%Y-%m-%d')
    try:
        ejecutar_procesamiento(fecha_ini, fecha_fin)
        global ruta_ML, ruta_MP, ruta_ET
        eliminar_archivo_de_insumos(ruta_ML)
        eliminar_archivo_de_insumos(ruta_MP)
        eliminar_archivo_de_insumos(ruta_ET)
        messagebox.showinfo('Info', "Proceso finalizado con éxito")
    except Exception as e:
        messagebox.showerror('Error', e)


def validar_fecha(event, fecha_inicio, fecha_fin, btn_MP):
    global fecha_rango_inicio, fecha_rango_fin

    fecha_ini = fecha_inicio.get_date()
    fecha_fin = fecha_fin.get_date()

    if fecha_ini and fecha_fin:
        if fecha_ini > fecha_fin:
            btn_MP.config(state='disabled')
            fecha_inicio.config(background ="red")
        else:
            btn_MP.config(state='normal')
            fecha_inicio.config(background ="darkgray")

        fecha_inicio.config(background=fecha_inicio.cget("background"))


def modificar_configuracion(nuevos_valores: dict):
    import json
    import app.settings

    with open(os.path.join(RUTA_RAIZ, 'secrets.json'), 'r') as f:
        variables_ambiente = json.load(f)

    variables_ambiente.update(nuevos_valores)

    with open(os.path.join(RUTA_RAIZ, 'secrets.json'), "w") as f:
        json.dump(variables_ambiente, f, indent=4)

    app.settings.RUTA_RESULTADOS = variables_ambiente['RUTA_RESULTADOS']
    messagebox.showinfo('Info', "Se reiniciara la aplicación para guardar los cambios")
    reiniciar()
    root.mainloop()

def abrir_carpeta_resultados(label):
    global ruta_resultados

    archivo = filedialog.askdirectory(title="Seleccionar nueva carpeta")
    label.config(text=archivo)

def reiniciar():
    import sys
    # cierra la ventana principal
    root.destroy()
    # vuelve a ejecutar el script
    os.execl(sys.executable, sys.executable, *sys.argv)

def abrir_ventana():
    print(RUTA_RESULTADOS)
    ventana = tk.Toplevel(root)
    ventana.grab_set()
    ventana.title('Ventana de configuración')

    frame = tk.Frame(ventana)
    ruta_resultados_label = tk.Label(frame, text="RUTA DE ARCHIVOS RESULTADOS: ", bd=1, anchor="w", justify="left")
    ruta_resultados_label.grid(row=0, column=0)
    label_resultados_label = tk.Label(frame, text=RUTA_RESULTADOS, bg="white", bd=1)
    label_resultados_label.grid(row=0, column=1)

    boton_cruce = tk.Button(frame, text='Seleccionar nueva carpeta', command=lambda: abrir_carpeta_resultados(label_resultados_label))
    boton_cruce.config(bd=1, relief="solid", height=2)
    boton_cruce.grid(row=0, column=2)

    boton_aceptar = tk.Button(frame, text='Aceptar', command=lambda: modificar_configuracion({'RUTA_RESULTADOS':label_resultados_label.cget('text')}))
    boton_aceptar.config(bd=1, relief="solid", height=2)
    boton_aceptar.grid(row=1, column=0, columnspan=2)

    frame.grid(row=0, column=0, padx=(0, 10), pady=10)

    # Aquí puedes agregar los widgets que desees en la ventana

boton = tk.Button(root, text='Configuracion', command=abrir_ventana)
boton.grid(row=0, column=1, padx=(0, 10), pady=10)

def añadir_labels(frame, fila: int, columna: int):
    ruta_label = tk.Label(frame, text="", bd=1, bg="white", anchor="w", justify="left")
    ruta_label.config(width=70, bd=1, relief="solid", height=2)
    ruta_label.grid(row=fila, column=columna, padx=(0, 10), pady=10)
    return ruta_label

def añadir_boton(frame, texto: str, fila: int, columna: int, label, funcion):
    boton_archivo = tk.Button(frame, text=texto.upper(), command=lambda: funcion(label), anchor="w", justify="left")
    boton_archivo.config(width=30, height=2)
    boton_archivo.grid(row=fila, column=columna, padx=(10, 0), pady=10)
    return boton_archivo

# Crear botones para seleccionar los archivos 1 y 2
frame_fechas_ml = tk.Frame()
ruta_label_ML = añadir_labels(frame_fechas_ml, 5, 2)
btn_ML = añadir_boton(frame_fechas_ml, 'Seleccionar mercado libre', 5, 1, ruta_label_ML, seleccionar_archivo_mercado_libre)
frame_fechas_ml.grid(row=2, column=1, columnspan=2, padx=10)
frame_fechas_ml.configure(background = "white")

frame_fechas_mp = tk.Frame()
ruta_label_MP = añadir_labels(frame_fechas_mp, 6, 2)
btn_MP = añadir_boton(frame_fechas_mp, 'Seleccionar mercado pago', 6, 1, ruta_label_MP, seleccionar_archivo_mercado_pago)
btn_MP.config(state='disabled')
frame_fechas_mp.grid(row=3, column=1, columnspan=2, padx=10)
frame_fechas_mp.configure(background = "white")


frame_fechas_et = tk.Frame()
ruta_label_ET = añadir_labels(frame_fechas_et, 7, 2)
btn_ET = añadir_boton(frame_fechas_et, 'Seleccionar enterprise', 7, 1, ruta_label_ET, seleccionar_archivo_enterprise)
frame_fechas_et.grid(row=4, column=1, columnspan=2, padx=10)
frame_fechas_et.configure(background = "white")

frame_fechas = tk.Frame()
frame_fechas.configure(background = "white")

label_fecha_inicial = tk.Label(frame_fechas, text = "Fecha inicio")
label_fecha_inicial.grid(row=1, column=1)
label_fecha_inicial.config(width=30, height=2)

cal_fecha_inicio = DateEntry(frame_fechas, selectmode = 'day',
               year = 2023, month = 4,
               day = 18)
cal_fecha_inicio.grid(row=1, column=2)
cal_fecha_inicio.config(width=20)


label_fecha_final= tk.Label(frame_fechas, text = "Fecha final")
label_fecha_final.grid(row=1, column=3)
label_fecha_final.config(width=30, height=2)

cal_fecha_final = DateEntry(frame_fechas, selectmode = 'day',
               year = 2023, month = 4,
               day = 18, height=2)
cal_fecha_final.grid(row=1, column=4)
cal_fecha_final.config(width=20)

frame_fechas.grid(row=1, column=1, columnspan=2)


cal_fecha_inicio.bind("<<DateEntrySelected>>", lambda event: validar_fecha(event, cal_fecha_inicio, cal_fecha_final, btn_MP))
cal_fecha_final.bind("<<DateEntrySelected>>", lambda event: validar_fecha(event, cal_fecha_inicio, cal_fecha_final, btn_MP))




boton_cruce = tk.Button(root, text='Cruzar archivos', command=cruzar_archivos, state='disabled')
boton_cruce.config(bd=1, relief="solid", height=2)
boton_cruce.grid(row=8, column=1, sticky="nswe", columnspan=2, padx=160, pady=20)


root.mainloop()