from tkinter import filedialog, messagebox, ttk
from tkcalendar import DateEntry

from app.settings import RUTA_INSUMOS, RUTA_RAIZ, RUTA_RESULTADOS
from app.classes.lectura_pandas import LecturaMercadoPago, LecturaMercadoLibre, LecturaEnterprise
from app.classes.procesamiento_archivos import ejecutar_procesamiento

from datetime import datetime

import customtkinter
import pandas as pd
import tkinter as tk
import shutil
import os

#ejecutar_procesamiento()

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("dark-blue")

root = customtkinter.CTk()
root.resizable(False, False)
root.minsize(1200, 400)
root.title('Semi automatización de conciliaciones de mercado libre')

root.grid_columnconfigure(0, pad=20)
root.grid_rowconfigure(0, pad=20)

mercado_libre:LecturaMercadoLibre = None
mercado_pago:LecturaMercadoPago = None
enterprise:LecturaEnterprise = None

ruta_ML = ""
ruta_MP = ""
ruta_ET = ""
ruta_resultados = ""



def copiar_archivo_a_insumos(ruta_archivo: str):

    shutil.copy(ruta_archivo, RUTA_INSUMOS)


def eliminar_archivo_de_insumos(ruta_archivo: str):
    nombre_archivo = ruta_archivo.split('/')[-1]
    os.remove(f'{RUTA_INSUMOS}\\{nombre_archivo}')


def seleccionar_archivo_mercado_libre(label_ml):

    archivo = filedialog.askopenfilename(title="Seleccionar mercado libre", filetypes=[("Excel", "*.xlsx")])
    try:
        global mercado_libre, ruta_ML
        mercado_libre = LecturaMercadoLibre(errores=[], crear_archivo=False, ruta=archivo, df=None)
        ruta_ML = archivo
        label_ml.configure(text=archivo)
        check_files()
    except ValueError as e:
        messagebox.showerror('Error', e)
    except Exception as e:
        messagebox.showerror('Error', e)


# Definir una función para seleccionar el archivo 2
def seleccionar_archivo_mercado_pago(label):
    global cal_fecha_final

    fecha_fin = cal_fecha_final.get_date().strftime('%Y-%m-%d')

    archivo = filedialog.askopenfilename(title="Seleccionar mercado pago", filetypes=[("Excel", "*.xlsx")])

    try:
        global mercado_pago, ruta_MP
        mercado_pago = LecturaMercadoPago(errores=[], fecha_fin=fecha_fin, crear_archivo=False, ruta=archivo, df=None, valor_evaluar=0.0)
        ruta_MP = archivo
        label.configure(text=archivo)
        check_files()
    except ValueError as e:
        messagebox.showerror('Error', e)
    except Exception as e:
        messagebox.showerror('Error', e)


def seleccionar_archivo_enterprise(label):
    archivo = filedialog.askopenfilename(title="Seleccionar enterprise", filetypes=[("Excel", "*.xlsx"), ("Excel", "*.xls")])
    try:
        global enterprise, ruta_ET
        enterprise = LecturaEnterprise(errores=[], crear_archivo=False, ruta=archivo, df=None)
        ruta_ET = archivo
        label.configure(text=archivo)
        check_files()
    except ValueError as e:
        messagebox.showerror('Error', e)
    except Exception as e:
        messagebox.showerror('Error', e)

def check_files():
    global mercado_pago, mercado_libre, enterprise
    try:
        if mercado_libre and mercado_pago and enterprise:
            df_ML = mercado_libre.leer_archivo()
            df_MP, _ = mercado_pago.leer_archivo()
            df_ET = enterprise.leer_archivo()

            if (df_ML.empty or df_MP.empty or df_ET.empty):
                boton_cruce.configure(state='disabled')
            else:
                boton_cruce.configure(state='normal')

    except Exception as e:
        messagebox.showerror('Error', e)


def cruzar_archivos():
    global fecha_fin, mercado_libre, mercado_pago, enterprise

    fecha_fin = cal_fecha_final.get_date().strftime('%Y-%m-%d')
    try:
        ejecutar_procesamiento(fecha_fin, mercado_libre, mercado_pago, enterprise)

        messagebox.showinfo('Info', "Proceso finalizado con éxito. Se reiniciara la aplicación")
        reiniciar()
        root.mainloop()
    except Exception as e:
        messagebox.showerror('Error', e)


def validar_fecha(event, fecha_fin, btn_MP):
    global fecha_rango_fin

    fecha_fin = fecha_fin.get_date()

    if fecha_fin:
        btn_MP.configure(state='normal')
    else:
        btn_MP.configure(state='disabled')


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
    label.configure(text=archivo)

def reiniciar():
    import sys
    # cierra la ventana principal
    root.destroy()
    # vuelve a ejecutar el script
    os.execl(sys.executable, sys.executable, *sys.argv)

def abrir_ventana():
    ventana = tk.Toplevel(root, height=500, width=500)
    ventana.grab_set()
    ventana.title('Ventana de configuración')

    frame = customtkinter.CTkFrame(master=ventana, border_width=0, corner_radius=0)
    ruta_resultados_label = customtkinter.CTkLabel(frame, text="RUTA DE ARCHIVOS RESULTADOS: ", anchor="w", justify="left")
    ruta_resultados_label.grid(row=0, column=0, padx=(10,0), pady=10)
    label_resultados_label = customtkinter.CTkLabel(frame, text=RUTA_RESULTADOS, fg_color="#F2F2F2", text_color="black")
    label_resultados_label.grid(row=0, column=1, pady=10)

    boton_cruce = customtkinter.CTkButton(frame, text='Seleccionar nueva carpeta', command=lambda: abrir_carpeta_resultados(label_resultados_label), cursor="hand2")
    boton_cruce.configure(height=30)
    boton_cruce.grid(row=0, column=2, padx=(0, 10))

    boton_aceptar = customtkinter.CTkButton(frame, text='Aceptar', command=lambda: modificar_configuracion({'RUTA_RESULTADOS':label_resultados_label.cget('text')}), cursor="hand2")
    boton_aceptar.configure(height=30)
    boton_aceptar.grid(row=1, column=0, columnspan=3, pady=10)

    frame.grid(row=0, column=0)

    # Aquí puedes agregar los widgets que desees en la ventana




def añadir_labels(frame, fila: int, columna: int):
    ruta_label = customtkinter.CTkLabel(frame, text=" ", anchor="w")
    ruta_label.configure(width=950,
                        height=30,
                        font=customtkinter.CTkFont(size=12, family='Arial'),
                        text_color="black",
                        corner_radius=12,
                        fg_color="#F2F2F2"
                        )
    ruta_label.grid(row=fila, column=columna, padx=(0, 15), pady=10, sticky='we')
    return ruta_label

def añadir_boton(frame, texto: str, fila: int, columna: int, label, funcion):
    boton_archivo = customtkinter.CTkButton(frame,
                                            text=texto.upper(),
                                            command=lambda: funcion(label),
                                            width=180,
                                            height=12,
                                            border_width=0,
                                            border_spacing=8,
                                            corner_radius=24,
                                            anchor="w",
                                            text_color=("gray10", "#DCE4EE"),
                                            font=customtkinter.CTkFont(size=10, weight="bold", family='Arial'),
                                            cursor="hand2")
    boton_archivo.grid(row=fila, column=columna, padx=(15, 0), pady=10, sticky='we')
    return boton_archivo

def callback(url):
    import webbrowser
    webbrowser.open_new(url)

boton = customtkinter.CTkButton(root, text='Configuración', command=abrir_ventana, cursor="hand2")
boton.grid(row=0, column=0, padx=10, pady=10, sticky='w')

# Crear botones para seleccionar los archivos 1 y 2
frame_archivos = customtkinter.CTkFrame(master=root, height=100, width=1000, fg_color="#424242")
frame_ml = customtkinter.CTkFrame(master=frame_archivos, fg_color="transparent")
ruta_label_ML = añadir_labels(frame_ml, 1, 2)
btn_ML = añadir_boton(frame_ml, 'Seleccionar mercado libre', 1, 1, ruta_label_ML, seleccionar_archivo_mercado_libre)
frame_ml.grid(row=0, column=1, sticky='we')
#frame_ml.configure(background = "white")

frame_mp = customtkinter.CTkFrame(master=frame_archivos, fg_color="transparent")
ruta_label_MP = añadir_labels(frame_mp, 2, 2)
btn_MP = añadir_boton(frame_mp, 'Seleccionar mercado pago', 2, 1, ruta_label_MP, seleccionar_archivo_mercado_pago)
btn_MP.configure(state='disabled')
frame_mp.grid(row=1, column=1, sticky='we')
#frame_mp.configure(background = "white")


frame_et = customtkinter.CTkFrame(master=frame_archivos, fg_color="transparent")
ruta_label_ET = añadir_labels(frame_et, 3, 2)
btn_ET = añadir_boton(frame_et, 'Seleccionar enterprise', 3, 1, ruta_label_ET, seleccionar_archivo_enterprise)
frame_et.grid(row=2, column=1, sticky='we')
#frame_et.configure(background = "white")

frame_archivos.grid(row=3, column=0, padx=10, pady=10, sticky='we')



frame_fechas = customtkinter.CTkFrame(master=root, fg_color="#424242")

label_fecha_final= customtkinter.CTkLabel(frame_fechas, text = "Fecha final", fg_color="transparent", font=customtkinter.CTkFont(size=12, weight="bold", family='Arial'))
label_fecha_final.grid(row=0, column=0, sticky='w', padx=10, pady=10,)
label_fecha_final.configure(width=60, height=15)

fecha_hoy = datetime.now()

cal_fecha_final = DateEntry(frame_fechas, selectmode = 'day',
               year = fecha_hoy.year, month = fecha_hoy.month,
               day = fecha_hoy.day, height=15)
cal_fecha_final.grid(row=0, column=2, sticky='w')
cal_fecha_final.config(width=20)

frame_fechas.grid(row=2, column=0, padx=10, pady=10, sticky='we')

cal_fecha_final.bind("<<DateEntrySelected>>", lambda event: validar_fecha(event, cal_fecha_final, btn_MP))

frame_cruce = customtkinter.CTkFrame(master=root, fg_color="#424242")
boton_cruce = customtkinter.CTkButton(frame_cruce, text='Cruzar archivos', command=cruzar_archivos, state='disabled', cursor="hand2")

boton_cruce.configure(height=30, font=customtkinter.CTkFont(size=12, weight="bold", family='Arial'))
boton_cruce.pack(padx=10, pady=10)
frame_cruce.grid(row=4, column=0, padx=10, pady=10, columnspan=2, sticky='we')

label_footer = customtkinter.CTkButton(root, text="Desarrollado por Danalytics SAS", command=lambda: callback('https://www.danalyticspro.co/'), hover=False, cursor="hand2")
label_footer.configure(fg_color="transparent", font=("Arial", 14), text_color="white")
label_footer.grid(row=5, column=0, padx=10, pady=10, sticky="we")

root.mainloop()




